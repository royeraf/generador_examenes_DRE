"""
Router para gestionar exámenes generados (Lectura y Matemática).
Los exámenes quedan vinculados al docente autenticado.

Desde la normalización, los textos y las preguntas viven en ``textos_examen``
y ``preguntas_examen``. Las respuestas de este router componen el formato JSON
anterior para no romper a los clientes existentes.
"""
import json
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)

from app.core.database import get_db
from app.models.db_models import (
    ExamenLectura,
    ExamenMatematica,
    PreguntaExamen,
    RespuestaIntento,
    TextoExamen,
    Grado,
)
from app.models.usuario import Usuario as DocenteModel
from app.api.dependencies import get_current_active_user
from app.services.examen_serializer import (
    serializar_examen_lectura,
    serializar_examen_matematica,
)

router = APIRouter()


# =============================================================================
# HELPERS — normalización de textos y preguntas
# =============================================================================

def _as_list(value: Any) -> list:
    """Acepta listas o JSON serializado (clientes antiguos)."""
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else []
        except (TypeError, ValueError):
            return []
    return []


def _tabla_map(tabla: list) -> dict:
    """Indexa la tabla por número de pregunta aceptando claves int o str."""
    out: dict = {}
    for fila in _as_list(tabla):
        if not isinstance(fila, dict):
            continue
        clave = fila.get("pregunta")
        if clave is None:
            continue
        out[clave] = fila
        out[str(clave)] = fila
        try:
            out[int(clave)] = fila
        except (TypeError, ValueError):
            pass
    return out


def _extraer_pregunta(p: dict, tabla_map: dict) -> dict:
    """Parsea una pregunta del JSON de IA a campos planos."""
    try:
        num = int(p.get("numero", 0) or 0)
    except (TypeError, ValueError):
        num = 0
    opciones_raw = _as_list(p.get("opciones"))
    opciones = {}
    for o in opciones_raw:
        if not isinstance(o, dict):
            continue
        letra = str(o.get("letra", "")).upper()
        texto = o.get("texto") or o.get("opcion") or o.get("alternativa") or ""
        if letra:
            opciones[letra] = str(texto)

    info = tabla_map.get(num, {})

    tipo = str(p.get("tipo") or info.get("tipo") or "").strip().lower()
    if tipo not in ("cerrada", "abierta"):
        tipo = "cerrada" if any(str(v).strip() for v in opciones.values()) else "abierta"

    rc = str(info.get("respuesta_correcta") or "")[:1].upper() or None
    if tipo == "abierta":
        rc = None

    nivel_raw = p.get("nivel") or p.get("capacidad") or info.get("nivel") or info.get("capacidad") or ""
    dc_raw = p.get("desempeno_codigo") or info.get("desempeno_codigo") or ""

    return {
        "numero": num,
        "tipo": tipo,
        "enunciado": str(p.get("enunciado") or ""),
        "contexto": str(p.get("contexto")) if p.get("contexto") else None,
        "opcion_a": opciones.get("A") or None,
        "opcion_b": opciones.get("B") or None,
        "opcion_c": opciones.get("C") or None,
        "opcion_d": opciones.get("D") or None,
        "opcion_e": opciones.get("E") or None,
        "respuesta_correcta": rc,
        "respuesta_esperada": info.get("respuesta_esperada") or p.get("respuesta_esperada") or None,
        "espacio_respuesta": p.get("espacio_respuesta") or None,
        "nivel": str(nivel_raw)[:20] if nivel_raw else None,
        "desempeno_codigo": str(dc_raw)[:50] if dc_raw else None,
        "desempeno_descripcion": info.get("desempeno"),
        "criterio_evaluacion": p.get("criterio_evaluacion") or None,
        "justificacion": info.get("justificacion"),
        "retroalimentacion_correcta": info.get("retroalimentacion_correcta"),
        "retroalimentacion_incorrecta": info.get("retroalimentacion_incorrecta"),
    }


def _insertar_preguntas_lectura(db, examen_id: int, preguntas: Any, tabla: Any) -> None:
    tabla_map = _tabla_map(tabla)
    for p in _as_list(preguntas):
        if not isinstance(p, dict):
            continue
        campos = _extraer_pregunta(p, tabla_map)
        db.add(PreguntaExamen(examen_lectura_id=examen_id, **campos))


def _insertar_preguntas_matematica(db, examen_id: int, preguntas: Any, tabla: Any) -> None:
    tabla_map = _tabla_map(tabla)
    for p in _as_list(preguntas):
        if not isinstance(p, dict):
            continue
        campos = _extraer_pregunta(p, tabla_map)
        db.add(PreguntaExamen(examen_matematica_id=examen_id, **campos))


def _insertar_textos_lectura(db, examen_id: int, lecturas: Any, lectura: Optional[str]) -> None:
    """Inserta los textos de lectura. Prefiere ``lecturas`` sobre ``lectura``."""
    items: list[dict] = []
    if isinstance(lecturas, (list, tuple, str)):
        items = [
            t for t in _as_list(lecturas)
            if isinstance(t, dict) and str(t.get("texto") or "").strip()
        ]
    if not items and isinstance(lectura, str) and lectura.strip():
        items = [{"titulo": "", "texto": lectura}]

    for orden, item in enumerate(items, start=1):
        db.add(TextoExamen(
            examen_lectura_id=examen_id,
            orden=orden,
            titulo=(str(item.get("titulo")).strip() or None) if item.get("titulo") else None,
            texto=str(item.get("texto")),
        ))


def _insertar_textos_matematica(db, examen_id: int, situacion: Optional[str], lecturas: Any = None) -> None:
    """Inserta la situación problemática (o la lista de textos si se provee)."""
    items: list[dict] = []
    if isinstance(lecturas, (list, tuple, str)):
        items = [
            t for t in _as_list(lecturas)
            if isinstance(t, dict) and str(t.get("texto") or "").strip()
        ]
    if not items and isinstance(situacion, str) and situacion.strip():
        items = [{"titulo": "Situación Problemática", "texto": situacion}]

    for orden, item in enumerate(items, start=1):
        db.add(TextoExamen(
            examen_matematica_id=examen_id,
            orden=orden,
            titulo=(str(item.get("titulo")).strip() or None) if item.get("titulo") else None,
            texto=str(item.get("texto")),
        ))


# =============================================================================
# SCHEMAS
# =============================================================================

class ExamenLecturaCreate(BaseModel):
    """Datos para guardar un examen de lectura."""
    grado_id: Optional[int] = None
    titulo: Optional[str] = None
    nivel_dificultad: Optional[str] = None
    modelo_ia: Optional[str] = None
    saludo: Optional[str] = None
    instrucciones: Optional[str] = None
    # Entrada legacy: se normaliza a textos_examen. ``lecturas`` tiene prioridad.
    lectura: Optional[str] = None
    lecturas: Optional[Any] = None  # [{"titulo": str, "texto": str}]
    preguntas: Optional[Any] = None
    tabla_respuestas: Optional[Any] = None
    desempenos_usados: Optional[str] = None


class ExamenMatematicaCreate(BaseModel):
    """Datos para guardar un examen de matemática."""
    grado_id: Optional[int] = None
    competencia_id: Optional[int] = None
    titulo: Optional[str] = None
    nivel_dificultad: Optional[str] = None
    modelo_ia: Optional[str] = None
    saludo: Optional[str] = None
    instrucciones: Optional[str] = None
    tipo_producto: Optional[int] = None
    contenido_json: Optional[Any] = None
    # Entrada legacy: se normaliza a textos_examen. ``lecturas`` tiene prioridad.
    situacion_problematica: Optional[str] = None
    lecturas: Optional[Any] = None  # [{"titulo": str, "texto": str}]
    preguntas: Optional[Any] = None
    tabla_respuestas: Optional[Any] = None
    desempenos_usados: Optional[str] = None


class ExamenLecturaResponse(BaseModel):
    id: int
    docente_id: int
    grado_id: Optional[int] = None
    fecha_creacion: datetime
    titulo: Optional[str] = None
    grado_nombre: Optional[str] = None
    nivel_dificultad: Optional[str] = None
    modelo_ia: Optional[str] = None
    saludo: Optional[str] = None
    instrucciones: Optional[str] = None
    # Campos derivados desde textos_examen/preguntas_examen, no columnas DB.
    lectura: Optional[str] = None
    lecturas: Optional[Any] = None
    preguntas: Optional[Any] = None
    tabla_respuestas: Optional[Any] = None
    desempenos_usados: Optional[str] = None
    total_preguntas: Optional[int] = None

    class Config:
        from_attributes = True


class ExamenLecturaListResponse(BaseModel):
    """Respuesta resumida para listado (sin contenido completo)."""
    id: int
    docente_id: int
    grado_id: Optional[int] = None
    fecha_creacion: datetime
    titulo: Optional[str] = None
    grado_nombre: Optional[str] = None
    nivel_dificultad: Optional[str] = None
    modelo_ia: Optional[str] = None
    total_preguntas: Optional[int] = None

    class Config:
        from_attributes = True


class ExamenMatematicaResponse(BaseModel):
    id: int
    docente_id: int
    grado_id: Optional[int] = None
    competencia_id: Optional[int] = None
    fecha_creacion: datetime
    titulo: Optional[str] = None
    grado_nombre: Optional[str] = None
    nivel_dificultad: Optional[str] = None
    modelo_ia: Optional[str] = None
    saludo: Optional[str] = None
    instrucciones: Optional[str] = None
    tipo_producto: Optional[int] = None
    contenido_json: Optional[Any] = None
    # Campos derivados desde textos_examen/preguntas_examen, no columnas DB.
    situacion_problematica: Optional[str] = None
    lecturas: Optional[Any] = None
    preguntas: Optional[Any] = None
    tabla_respuestas: Optional[Any] = None
    desempenos_usados: Optional[str] = None
    total_preguntas: Optional[int] = None

    class Config:
        from_attributes = True


class ExamenMatematicaListResponse(BaseModel):
    """Respuesta resumida para listado (sin contenido completo)."""
    id: int
    docente_id: int
    grado_id: Optional[int] = None
    competencia_id: Optional[int] = None
    fecha_creacion: datetime
    titulo: Optional[str] = None
    grado_nombre: Optional[str] = None
    nivel_dificultad: Optional[str] = None
    modelo_ia: Optional[str] = None
    total_preguntas: Optional[int] = None

    class Config:
        from_attributes = True


# =============================================================================
# ENDPOINTS - EXÁMENES DE LECTURA
# =============================================================================

@router.post("/lectura", response_model=ExamenLecturaResponse, status_code=status.HTTP_201_CREATED)
async def guardar_examen_lectura(
    examen_in: ExamenLecturaCreate,
    db: AsyncSession = Depends(get_db),
    current_user: DocenteModel = Depends(get_current_active_user),
):
    """
    Guarda un examen de comprensión lectora generado.
    El examen queda vinculado al docente autenticado.
    """
    datos = examen_in.model_dump(
        exclude={"lectura", "lecturas", "preguntas", "tabla_respuestas"}
    )
    db_examen = ExamenLectura(docente_id=current_user.id, **datos)
    if examen_in.grado_id:
        grado_r = await db.execute(select(Grado).where(Grado.id == examen_in.grado_id))
        grado = grado_r.scalars().first()
        if grado:
            db_examen.grado_nombre = grado.nombre
    db.add(db_examen)
    await db.flush()

    try:
        _insertar_textos_lectura(db, db_examen.id, examen_in.lecturas, examen_in.lectura)
        _insertar_preguntas_lectura(
            db, db_examen.id, examen_in.preguntas or [], examen_in.tabla_respuestas or []
        )
    except Exception as exc:
        logger.error("Error insertando textos/preguntas lectura: %s", exc, exc_info=True)
        raise

    examen_id = db_examen.id
    await db.commit()

    result = await db.execute(
        select(ExamenLectura)
        .options(
            selectinload(ExamenLectura.textos),
            selectinload(ExamenLectura.preguntas_rel),
        )
        .where(ExamenLectura.id == examen_id)
    )
    examen = result.scalars().first()
    return serializar_examen_lectura(examen, examen.textos, examen.preguntas_rel)


@router.get("/lectura", response_model=List[ExamenLecturaListResponse])
async def listar_examenes_lectura(
    db: AsyncSession = Depends(get_db),
    current_user: DocenteModel = Depends(get_current_active_user),
):
    """
    Lista todos los exámenes de lectura del docente autenticado,
    ordenados del más reciente al más antiguo.
    """
    total_subq = (
        select(func.count(PreguntaExamen.id))
        .where(PreguntaExamen.examen_lectura_id == ExamenLectura.id)
        .correlate(ExamenLectura)
        .scalar_subquery()
    )
    result = await db.execute(
        select(ExamenLectura, total_subq)
        .where(ExamenLectura.docente_id == current_user.id)
        .order_by(ExamenLectura.fecha_creacion.desc())
    )

    response = []
    for ex, total in result.all():
        response.append(ExamenLecturaListResponse(
            id=ex.id,
            docente_id=ex.docente_id,
            grado_id=ex.grado_id,
            fecha_creacion=ex.fecha_creacion,
            titulo=ex.titulo,
            grado_nombre=ex.grado_nombre,
            nivel_dificultad=ex.nivel_dificultad,
            modelo_ia=ex.modelo_ia,
            total_preguntas=total or 0,
        ))
    return response


@router.get("/lectura/{examen_id}", response_model=ExamenLecturaResponse)
async def obtener_examen_lectura(
    examen_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: DocenteModel = Depends(get_current_active_user),
):
    """
    Obtiene un examen de lectura específico del docente autenticado.
    """
    result = await db.execute(
        select(ExamenLectura)
        .options(
            selectinload(ExamenLectura.textos),
            selectinload(ExamenLectura.preguntas_rel),
        )
        .where(
            ExamenLectura.id == examen_id,
            ExamenLectura.docente_id == current_user.id,
        )
    )
    examen = result.scalars().first()
    if not examen:
        raise HTTPException(status_code=404, detail="Examen no encontrado")
    return serializar_examen_lectura(examen, examen.textos, examen.preguntas_rel)


@router.delete("/lectura/{examen_id}", status_code=status.HTTP_200_OK)
async def eliminar_examen_lectura(
    examen_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: DocenteModel = Depends(get_current_active_user),
):
    """
    Elimina un examen de lectura del docente autenticado.
    """
    result = await db.execute(
        select(ExamenLectura)
        .options(
            selectinload(ExamenLectura.textos),
            selectinload(ExamenLectura.preguntas_rel),
        )
        .where(
            ExamenLectura.id == examen_id,
            ExamenLectura.docente_id == current_user.id,
        )
    )
    examen = result.scalars().first()
    if not examen:
        raise HTTPException(status_code=404, detail="Examen no encontrado")
    preguntas_ids = [p.id for p in examen.preguntas_rel]
    if preguntas_ids:
        # Borrado explícito para motores sin FK/cascada (p. ej. MyISAM en producción).
        await db.execute(
            delete(RespuestaIntento).where(RespuestaIntento.pregunta_id.in_(preguntas_ids))
        )
    await db.delete(examen)
    await db.commit()
    return {"message": "Examen eliminado correctamente"}


# =============================================================================
# ENDPOINTS - EXÁMENES DE MATEMÁTICA
# =============================================================================

@router.post("/matematica", response_model=ExamenMatematicaResponse, status_code=status.HTTP_201_CREATED)
async def guardar_examen_matematica(
    examen_in: ExamenMatematicaCreate,
    db: AsyncSession = Depends(get_db),
    current_user: DocenteModel = Depends(get_current_active_user),
):
    """
    Guarda un examen de matemática generado.
    El examen queda vinculado al docente autenticado.
    """
    datos = examen_in.model_dump(
        exclude={"situacion_problematica", "lecturas", "preguntas", "tabla_respuestas"}
    )
    db_examen = ExamenMatematica(docente_id=current_user.id, **datos)
    if examen_in.grado_id:
        grado_r = await db.execute(select(Grado).where(Grado.id == examen_in.grado_id))
        grado = grado_r.scalars().first()
        if grado:
            db_examen.grado_nombre = grado.nombre
    db.add(db_examen)
    await db.flush()

    try:
        _insertar_textos_matematica(
            db, db_examen.id, examen_in.situacion_problematica, examen_in.lecturas
        )
        _insertar_preguntas_matematica(
            db, db_examen.id, examen_in.preguntas or [], examen_in.tabla_respuestas or []
        )
    except Exception as exc:
        logger.error("Error insertando textos/preguntas matematica: %s", exc, exc_info=True)
        raise

    examen_id = db_examen.id
    await db.commit()

    result = await db.execute(
        select(ExamenMatematica)
        .options(
            selectinload(ExamenMatematica.textos),
            selectinload(ExamenMatematica.preguntas_rel),
        )
        .where(ExamenMatematica.id == examen_id)
    )
    examen = result.scalars().first()
    return serializar_examen_matematica(examen, examen.textos, examen.preguntas_rel)


@router.get("/matematica", response_model=List[ExamenMatematicaListResponse])
async def listar_examenes_matematica(
    db: AsyncSession = Depends(get_db),
    current_user: DocenteModel = Depends(get_current_active_user),
):
    """
    Lista todos los exámenes de matemática del docente autenticado,
    ordenados del más reciente al más antiguo.
    """
    total_subq = (
        select(func.count(PreguntaExamen.id))
        .where(PreguntaExamen.examen_matematica_id == ExamenMatematica.id)
        .correlate(ExamenMatematica)
        .scalar_subquery()
    )
    result = await db.execute(
        select(ExamenMatematica, total_subq)
        .where(ExamenMatematica.docente_id == current_user.id)
        .order_by(ExamenMatematica.fecha_creacion.desc())
    )

    response = []
    for ex, total in result.all():
        response.append(ExamenMatematicaListResponse(
            id=ex.id,
            docente_id=ex.docente_id,
            grado_id=ex.grado_id,
            competencia_id=ex.competencia_id,
            fecha_creacion=ex.fecha_creacion,
            titulo=ex.titulo,
            grado_nombre=ex.grado_nombre,
            nivel_dificultad=ex.nivel_dificultad,
            modelo_ia=ex.modelo_ia,
            total_preguntas=total or 0,
        ))
    return response


@router.get("/matematica/{examen_id}", response_model=ExamenMatematicaResponse)
async def obtener_examen_matematica(
    examen_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: DocenteModel = Depends(get_current_active_user),
):
    """
    Obtiene un examen de matemática específico del docente autenticado.
    """
    result = await db.execute(
        select(ExamenMatematica)
        .options(
            selectinload(ExamenMatematica.textos),
            selectinload(ExamenMatematica.preguntas_rel),
        )
        .where(
            ExamenMatematica.id == examen_id,
            ExamenMatematica.docente_id == current_user.id,
        )
    )
    examen = result.scalars().first()
    if not examen:
        raise HTTPException(status_code=404, detail="Examen no encontrado")
    return serializar_examen_matematica(examen, examen.textos, examen.preguntas_rel)


@router.delete("/matematica/{examen_id}", status_code=status.HTTP_200_OK)
async def eliminar_examen_matematica(
    examen_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: DocenteModel = Depends(get_current_active_user),
):
    """
    Elimina un examen de matemática del docente autenticado.
    """
    result = await db.execute(
        select(ExamenMatematica)
        .options(
            selectinload(ExamenMatematica.textos),
            selectinload(ExamenMatematica.preguntas_rel),
        )
        .where(
            ExamenMatematica.id == examen_id,
            ExamenMatematica.docente_id == current_user.id,
        )
    )
    examen = result.scalars().first()
    if not examen:
        raise HTTPException(status_code=404, detail="Examen no encontrado")
    preguntas_ids = [p.id for p in examen.preguntas_rel]
    if preguntas_ids:
        # Borrado explícito para motores sin FK/cascada (p. ej. MyISAM en producción).
        await db.execute(
            delete(RespuestaIntento).where(RespuestaIntento.pregunta_id.in_(preguntas_ids))
        )
    await db.delete(examen)
    await db.commit()
    return {"message": "Examen eliminado correctamente"}
