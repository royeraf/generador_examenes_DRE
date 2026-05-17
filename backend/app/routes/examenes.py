"""
Router para gestionar exámenes generados (Lectura y Matemática).
Los exámenes quedan vinculados al docente autenticado.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime

from app.core.database import get_db
from app.models.db_models import ExamenLectura, ExamenMatematica, PreguntaExamen, Grado
from app.models.usuario import Usuario as DocenteModel
from app.api.dependencies import get_current_active_user

router = APIRouter()


# =============================================================================
# HELPERS — normalización de preguntas
# =============================================================================

def _extraer_pregunta(p: dict, tabla_map: dict) -> dict:
    """Parsea una pregunta del JSON de IA a campos planos."""
    num = p.get("numero", 0)
    opciones_raw = p.get("opciones") or []
    opciones = {o["letra"]: o["texto"] for o in opciones_raw if isinstance(o, dict) and "letra" in o}
    info = tabla_map.get(num, {})
    return {
        "numero": num,
        "enunciado": p.get("enunciado", ""),
        "opcion_a": opciones.get("A", ""),
        "opcion_b": opciones.get("B", ""),
        "opcion_c": opciones.get("C", ""),
        "opcion_d": opciones.get("D", ""),
        "respuesta_correcta": info.get("respuesta_correcta", ""),
        "nivel": p.get("nivel") or info.get("nivel"),
        "desempeno_codigo": p.get("desempeno_codigo") or info.get("desempeno"),
        "desempeno_descripcion": info.get("desempeno"),
        "justificacion": info.get("justificacion"),
    }


def _insertar_preguntas_lectura(db, examen_id: int, preguntas: list, tabla: list) -> None:
    tabla_map = {r.get("pregunta"): r for r in tabla}
    for p in preguntas:
        campos = _extraer_pregunta(p, tabla_map)
        db.add(PreguntaExamen(examen_lectura_id=examen_id, **campos))


def _insertar_preguntas_matematica(db, examen_id: int, preguntas: list, tabla: list) -> None:
    tabla_map = {r.get("pregunta"): r for r in tabla}
    for p in preguntas:
        campos = _extraer_pregunta(p, tabla_map)
        db.add(PreguntaExamen(examen_matematica_id=examen_id, **campos))


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
    situacion_problematica: Optional[str] = None
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
    lectura: Optional[str] = None
    lecturas: Optional[Any] = None
    preguntas: Optional[Any] = None
    tabla_respuestas: Optional[Any] = None
    desempenos_usados: Optional[str] = None

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
    situacion_problematica: Optional[str] = None
    preguntas: Optional[Any] = None
    tabla_respuestas: Optional[Any] = None
    desempenos_usados: Optional[str] = None

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
    db_examen = ExamenLectura(
        docente_id=current_user.id,
        **examen_in.model_dump(exclude_none=False)
    )
    if examen_in.grado_id:
        grado_r = await db.execute(select(Grado).where(Grado.id == examen_in.grado_id))
        grado = grado_r.scalars().first()
        if grado:
            db_examen.grado_nombre = grado.nombre
    db.add(db_examen)
    await db.flush()

    # Poblar preguntas_examen desde el JSON generado por IA
    _insertar_preguntas_lectura(db, db_examen.id, examen_in.preguntas or [], examen_in.tabla_respuestas or [])

    await db.commit()
    await db.refresh(db_examen)
    return db_examen


@router.get("/lectura", response_model=List[ExamenLecturaListResponse])
async def listar_examenes_lectura(
    db: AsyncSession = Depends(get_db),
    current_user: DocenteModel = Depends(get_current_active_user),
):
    """
    Lista todos los exámenes de lectura del docente autenticado,
    ordenados del más reciente al más antiguo.
    """
    result = await db.execute(
        select(ExamenLectura)
        .where(ExamenLectura.docente_id == current_user.id)
        .order_by(ExamenLectura.fecha_creacion.desc())
    )
    examenes = result.scalars().all()

    # Calcular total_preguntas para cada examen
    response = []
    for ex in examenes:
        total = len(ex.preguntas) if isinstance(ex.preguntas, list) else 0
        response.append(ExamenLecturaListResponse(
            id=ex.id,
            docente_id=ex.docente_id,
            grado_id=ex.grado_id,
            fecha_creacion=ex.fecha_creacion,
            titulo=ex.titulo,
            grado_nombre=ex.grado_nombre,
            nivel_dificultad=ex.nivel_dificultad,
            modelo_ia=ex.modelo_ia,
            total_preguntas=total,
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
        select(ExamenLectura).where(
            ExamenLectura.id == examen_id,
            ExamenLectura.docente_id == current_user.id,
        )
    )
    examen = result.scalars().first()
    if not examen:
        raise HTTPException(status_code=404, detail="Examen no encontrado")
    return examen


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
        select(ExamenLectura).where(
            ExamenLectura.id == examen_id,
            ExamenLectura.docente_id == current_user.id,
        )
    )
    examen = result.scalars().first()
    if not examen:
        raise HTTPException(status_code=404, detail="Examen no encontrado")
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
    db_examen = ExamenMatematica(
        docente_id=current_user.id,
        **examen_in.model_dump(exclude_none=False)
    )
    if examen_in.grado_id:
        grado_r = await db.execute(select(Grado).where(Grado.id == examen_in.grado_id))
        grado = grado_r.scalars().first()
        if grado:
            db_examen.grado_nombre = grado.nombre
    db.add(db_examen)
    await db.flush()

    # Poblar preguntas_examen desde el JSON generado por IA
    _insertar_preguntas_matematica(db, db_examen.id, examen_in.preguntas or [], examen_in.tabla_respuestas or [])

    await db.commit()
    await db.refresh(db_examen)
    return db_examen


@router.get("/matematica", response_model=List[ExamenMatematicaListResponse])
async def listar_examenes_matematica(
    db: AsyncSession = Depends(get_db),
    current_user: DocenteModel = Depends(get_current_active_user),
):
    """
    Lista todos los exámenes de matemática del docente autenticado,
    ordenados del más reciente al más antiguo.
    """
    result = await db.execute(
        select(ExamenMatematica)
        .where(ExamenMatematica.docente_id == current_user.id)
        .order_by(ExamenMatematica.fecha_creacion.desc())
    )
    examenes = result.scalars().all()

    response = []
    for ex in examenes:
        total = len(ex.preguntas) if isinstance(ex.preguntas, list) else 0
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
            total_preguntas=total,
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
        select(ExamenMatematica).where(
            ExamenMatematica.id == examen_id,
            ExamenMatematica.docente_id == current_user.id,
        )
    )
    examen = result.scalars().first()
    if not examen:
        raise HTTPException(status_code=404, detail="Examen no encontrado")
    return examen


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
        select(ExamenMatematica).where(
            ExamenMatematica.id == examen_id,
            ExamenMatematica.docente_id == current_user.id,
        )
    )
    examen = result.scalars().first()
    if not examen:
        raise HTTPException(status_code=404, detail="Examen no encontrado")
    await db.delete(examen)
    await db.commit()
    return {"message": "Examen eliminado correctamente"}
