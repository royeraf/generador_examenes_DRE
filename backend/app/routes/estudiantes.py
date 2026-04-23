"""
Rutas del portal estudiantil: exámenes, intentos y progreso.
"""
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from pydantic import BaseModel

from app.core.database import get_db
from app.models.db_models import (
    AsignacionExamen, IntentoExamen, ProgresoEstudiante,
    ExamenLectura, ExamenMatematica,
)
from app.models.usuario import Usuario
from app.models.enums import RolCodigo
from app.api.dependencies import get_estudiante_user, get_current_active_user, require_role, require_modulo

router = APIRouter()

EXAM_CREATOR_ROLES = (
    RolCodigo.DOCENTE, RolCodigo.AUXILIAR, RolCodigo.DIRECTOR,
    RolCodigo.ESPECIALISTA_DRE_COMUNICACION, RolCodigo.ESPECIALISTA_DRE_MATEMATICA,
)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _puntaje_a_nivel(puntaje: float) -> str:
    if puntaje < 20:
        return "pre_inicio"
    if puntaje < 40:
        return "inicio"
    if puntaje < 60:
        return "proceso"
    if puntaje < 80:
        return "satisfactorio"
    return "destacado"


def _calificar(respuestas_estudiante: List[dict], tabla_respuestas: List[dict]) -> dict:
    """
    Califica las respuestas del estudiante vs la tabla de respuestas del examen.
    tabla_respuestas: [{"pregunta": 1, "respuesta_correcta": "A", "desempeno": "...", ...}, ...]
    respuestas_estudiante: [{"pregunta_numero": 1, "respuesta": "A"}, ...]
    """
    # Build lookup
    clave_map = {int(r["pregunta"]): r.get("respuesta_correcta", "").upper() for r in tabla_respuestas}
    student_map = {int(r["pregunta_numero"]): r["respuesta"].upper() for r in respuestas_estudiante}

    correctas = 0
    total = len(tabla_respuestas)

    for num, clave in clave_map.items():
        if student_map.get(num) == clave:
            correctas += 1

    puntaje = (correctas / total * 100) if total > 0 else 0
    nivel = _puntaje_a_nivel(puntaje)

    return {
        "correctas": correctas,
        "total": total,
        "puntaje": round(puntaje, 2),
        "nivel_logro": nivel,
    }


# ─── Schemas ─────────────────────────────────────────────────────────────────

class RespuestaEnvio(BaseModel):
    pregunta_numero: int
    respuesta: str


class FinalizarIntentoRequest(BaseModel):
    respuestas: List[RespuestaEnvio]


class AsignarExamenRequest(BaseModel):
    tipo_examen: str  # "lectura" o "matematica"
    examen_id: int
    grado_id: Optional[int] = None
    seccion: Optional[str] = None
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    duracion_minutos: Optional[int] = None
    intentos_permitidos: int = 1
    mostrar_resultados: bool = True


# ─── Portal estudiante: listar exámenes ──────────────────────────────────────

@router.get("/estudiante/examenes")
async def listar_examenes_estudiante(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_estudiante_user),
):
    """Lista los exámenes asignados al estudiante."""
    ahora = datetime.now(timezone.utc)
    q = select(AsignacionExamen).where(
        AsignacionExamen.is_active == True,
        AsignacionExamen.institucion_educativa_id == current_user.institucion_educativa_id,
        or_(
            AsignacionExamen.grado_id == None,
            AsignacionExamen.grado_id == current_user.grado_id,
        ),
        or_(
            AsignacionExamen.seccion == None,
            AsignacionExamen.seccion == current_user.seccion,
        ),
        or_(
            AsignacionExamen.fecha_inicio == None,
            AsignacionExamen.fecha_inicio <= ahora,
        ),
    )
    result = await db.execute(q.order_by(AsignacionExamen.fecha_creacion.desc()))
    asignaciones = result.scalars().all()

    examenes_out = []
    for a in asignaciones:
        # Contar mis intentos
        cnt_result = await db.execute(
            select(func.count(IntentoExamen.id)).where(
                IntentoExamen.asignacion_id == a.id,
                IntentoExamen.estudiante_id == current_user.id,
            )
        )
        mis_intentos = cnt_result.scalar() or 0

        # Buscar último intento completado
        ult_result = await db.execute(
            select(IntentoExamen).where(
                IntentoExamen.asignacion_id == a.id,
                IntentoExamen.estudiante_id == current_user.id,
                IntentoExamen.estado == "completado",
            ).order_by(IntentoExamen.numero_intento.desc())
        )
        ultimo = ult_result.scalars().first()

        # Obtener título del examen
        titulo = f"Examen de {a.tipo_examen.capitalize()}"
        if a.tipo_examen == "lectura" and a.examen_lectura_id:
            ex_r = await db.execute(select(ExamenLectura.titulo).where(ExamenLectura.id == a.examen_lectura_id))
            t = ex_r.scalar()
            if t:
                titulo = t
        elif a.tipo_examen == "matematica" and a.examen_matematica_id:
            ex_r = await db.execute(select(ExamenMatematica.titulo).where(ExamenMatematica.id == a.examen_matematica_id))
            t = ex_r.scalar()
            if t:
                titulo = t

        examenes_out.append({
            "id": a.id,
            "tipo_examen": a.tipo_examen,
            "titulo": titulo,
            "fecha_inicio": a.fecha_inicio.isoformat() if a.fecha_inicio else None,
            "fecha_fin": a.fecha_fin.isoformat() if a.fecha_fin else None,
            "duracion_minutos": a.duracion_minutos,
            "intentos_permitidos": a.intentos_permitidos,
            "mis_intentos": mis_intentos,
            "completado": ultimo is not None,
            "puntaje": ultimo.puntaje_total if ultimo else None,
            "nivel_logro": ultimo.nivel_logro if ultimo else None,
        })

    return examenes_out


@router.post("/estudiante/examenes/{asignacion_id}/iniciar")
async def iniciar_examen(
    asignacion_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_estudiante_user),
):
    """Crea un nuevo intento y devuelve el contenido del examen."""
    result = await db.execute(select(AsignacionExamen).where(AsignacionExamen.id == asignacion_id))
    asig = result.scalars().first()
    if not asig or not asig.is_active:
        raise HTTPException(404, "Examen no encontrado")

    # Verificar que el estudiante pertenece a este examen
    if asig.institucion_educativa_id and asig.institucion_educativa_id != current_user.institucion_educativa_id:
        raise HTTPException(403, "No tienes acceso a este examen")

    # Contar intentos previos
    cnt_r = await db.execute(
        select(func.count(IntentoExamen.id)).where(
            IntentoExamen.asignacion_id == asignacion_id,
            IntentoExamen.estudiante_id == current_user.id,
        )
    )
    num_intentos = cnt_r.scalar() or 0
    if num_intentos >= asig.intentos_permitidos:
        raise HTTPException(400, "Has agotado los intentos permitidos")

    # Crear intento
    intento = IntentoExamen(
        asignacion_id=asignacion_id,
        estudiante_id=current_user.id,
        numero_intento=num_intentos + 1,
        estado="en_progreso",
        fecha_inicio=datetime.now(timezone.utc),
    )
    db.add(intento)
    await db.flush()
    await db.refresh(intento)

    # Obtener preguntas del examen
    if asig.tipo_examen == "lectura" and asig.examen_lectura_id:
        ex_r = await db.execute(select(ExamenLectura).where(ExamenLectura.id == asig.examen_lectura_id))
        examen = ex_r.scalars().first()
        if not examen:
            raise HTTPException(404, "Examen de lectura no encontrado")
        return {
            "titulo": examen.titulo or "Examen de Comunicación",
            "instrucciones": examen.instrucciones or "",
            "lectura": examen.lectura or "",
            "preguntas": _preparar_preguntas(examen.preguntas or []),
            "duracion_minutos": asig.duracion_minutos,
            "intento_id": intento.id,
        }
    elif asig.tipo_examen == "matematica" and asig.examen_matematica_id:
        ex_r = await db.execute(select(ExamenMatematica).where(ExamenMatematica.id == asig.examen_matematica_id))
        examen = ex_r.scalars().first()
        if not examen:
            raise HTTPException(404, "Examen de matemática no encontrado")
        return {
            "titulo": examen.titulo or "Examen de Matemática",
            "instrucciones": "",
            "lectura": examen.situacion_problematica or "",
            "preguntas": _preparar_preguntas(examen.preguntas or []),
            "duracion_minutos": asig.duracion_minutos,
            "intento_id": intento.id,
        }
    else:
        raise HTTPException(400, "Tipo de examen no soportado")


def _preparar_preguntas(preguntas_raw: list) -> list:
    """Normaliza la lista de preguntas para el cliente."""
    out = []
    for p in preguntas_raw:
        opciones = []
        for o in p.get("opciones", []):
            opciones.append({
                "letra": o.get("letra", ""),
                "texto": o.get("texto", ""),
            })
        out.append({
            "numero": p.get("numero", 0),
            "enunciado": p.get("enunciado", ""),
            "opciones": opciones,
            "nivel": p.get("nivel", ""),
            "desempeno_codigo": p.get("desempeno_codigo", ""),
        })
    return out


@router.get("/estudiante/examenes/{asignacion_id}/resultado")
async def obtener_resultado_examen(
    asignacion_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_estudiante_user),
):
    """Devuelve los resultados del último intento completado."""
    ult_result = await db.execute(
        select(IntentoExamen).where(
            IntentoExamen.asignacion_id == asignacion_id,
            IntentoExamen.estudiante_id == current_user.id,
            IntentoExamen.estado == "completado",
        ).order_by(IntentoExamen.numero_intento.desc())
    )
    ultimo = ult_result.scalars().first()
    if not ultimo:
        raise HTTPException(404, "No hay resultados para este examen")
        
    return {
        "puntaje_total": ultimo.puntaje_total,
        "preguntas_correctas": ultimo.preguntas_correctas,
        "preguntas_total": ultimo.preguntas_total,
        "nivel_logro": ultimo.nivel_logro,
    }



@router.post("/estudiante/intentos/{intento_id}/finalizar")
async def finalizar_intento(
    intento_id: int,
    data: FinalizarIntentoRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_estudiante_user),
):
    """Finaliza el intento, califica y actualiza el progreso."""
    result = await db.execute(select(IntentoExamen).where(IntentoExamen.id == intento_id))
    intento = result.scalars().first()
    if not intento or intento.estudiante_id != current_user.id:
        raise HTTPException(404, "Intento no encontrado")
    if intento.estado == "completado":
        raise HTTPException(400, "Este intento ya fue completado")

    # Obtener tabla de respuestas
    asig_r = await db.execute(select(AsignacionExamen).where(AsignacionExamen.id == intento.asignacion_id))
    asig = asig_r.scalars().first()
    tabla_respuestas = []

    if asig.tipo_examen == "lectura" and asig.examen_lectura_id:
        ex_r = await db.execute(select(ExamenLectura.tabla_respuestas).where(ExamenLectura.id == asig.examen_lectura_id))
        tabla_respuestas = ex_r.scalar() or []
    elif asig.tipo_examen == "matematica" and asig.examen_matematica_id:
        ex_r = await db.execute(select(ExamenMatematica.tabla_respuestas).where(ExamenMatematica.id == asig.examen_matematica_id))
        tabla_respuestas = ex_r.scalar() or []

    # Calificar
    respuestas_list = [{"pregunta_numero": r.pregunta_numero, "respuesta": r.respuesta} for r in data.respuestas]
    resultado = _calificar(respuestas_list, tabla_respuestas)

    # Actualizar intento
    intento.estado = "completado"
    intento.fecha_fin = datetime.now(timezone.utc)
    intento.respuestas = {str(r.pregunta_numero): r.respuesta for r in data.respuestas}
    intento.puntaje_total = resultado["puntaje"]
    intento.preguntas_correctas = resultado["correctas"]
    intento.preguntas_total = resultado["total"]
    intento.nivel_logro = resultado["nivel_logro"]

    # Actualizar progreso
    area = "comunicacion" if asig.tipo_examen == "lectura" else "matematica"
    progreso_r = await db.execute(
        select(ProgresoEstudiante).where(
            ProgresoEstudiante.estudiante_id == current_user.id,
            ProgresoEstudiante.area == area,
        )
    )
    progreso = progreso_r.scalars().first()
    if progreso:
        n = progreso.total_examenes_completados
        prom = (progreso.puntaje_promedio or 0) * n if n > 0 else 0
        progreso.total_examenes_completados = n + 1
        progreso.puntaje_promedio = (prom + resultado["puntaje"]) / (n + 1)
        progreso.nivel_logro_actual = resultado["nivel_logro"]
        progreso.ultima_actividad = datetime.now(timezone.utc)
    else:
        progreso = ProgresoEstudiante(
            estudiante_id=current_user.id,
            area=area,
            total_examenes_completados=1,
            puntaje_promedio=resultado["puntaje"],
            nivel_logro_actual=resultado["nivel_logro"],
            ultima_actividad=datetime.now(timezone.utc),
        )
        db.add(progreso)

    await db.flush()

    return {
        "puntaje_total": resultado["puntaje"],
        "preguntas_correctas": resultado["correctas"],
        "preguntas_total": resultado["total"],
        "nivel_logro": resultado["nivel_logro"],
    }


# ─── Progreso del estudiante ─────────────────────────────────────────────────

@router.get("/estudiante/progreso")
async def progreso_estudiante(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_estudiante_user),
):
    result = await db.execute(
        select(ProgresoEstudiante).where(ProgresoEstudiante.estudiante_id == current_user.id)
    )
    progresos = result.scalars().all()
    return [
        {
            "area": p.area,
            "total_examenes_completados": p.total_examenes_completados,
            "puntaje_promedio": round(p.puntaje_promedio or 0, 2),
            "nivel_logro_actual": p.nivel_logro_actual,
            "ultima_actividad": p.ultima_actividad.isoformat() if p.ultima_actividad else None,
        }
        for p in progresos
    ]


# ─── Asignaciones (para docentes) ────────────────────────────────────────────

@router.post("/examenes/asignar")
async def asignar_examen(
    data: AsignarExamenRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_modulo("asignaciones")),
):
    """Asigna un examen generado a un grado/sección de estudiantes."""
    if data.tipo_examen not in ("lectura", "matematica"):
        raise HTTPException(400, "tipo_examen debe ser 'lectura' o 'matematica'")

    kwargs = dict(
        tipo_examen=data.tipo_examen,
        asignado_por_id=current_user.id,
        institucion_educativa_id=current_user.institucion_educativa_id,
        grado_id=data.grado_id,
        seccion=data.seccion,
        fecha_inicio=data.fecha_inicio,
        fecha_fin=data.fecha_fin,
        duracion_minutos=data.duracion_minutos,
        intentos_permitidos=data.intentos_permitidos,
        mostrar_resultados=data.mostrar_resultados,
    )
    if data.tipo_examen == "lectura":
        kwargs["examen_lectura_id"] = data.examen_id
    else:
        kwargs["examen_matematica_id"] = data.examen_id

    asig = AsignacionExamen(**kwargs)
    db.add(asig)
    await db.flush()
    await db.refresh(asig)
    return {"id": asig.id, "message": "Examen asignado correctamente"}


@router.get("/examenes/asignaciones")
async def listar_asignaciones(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_modulo("asignaciones")),
):
    """Lista las asignaciones creadas por el usuario."""
    result = await db.execute(
        select(AsignacionExamen)
        .where(AsignacionExamen.asignado_por_id == current_user.id)
        .order_by(AsignacionExamen.fecha_creacion.desc())
    )
    asignaciones = result.scalars().all()
    out = []
    for a in asignaciones:
        cnt_r = await db.execute(
            select(func.count(IntentoExamen.id)).where(
                IntentoExamen.asignacion_id == a.id,
                IntentoExamen.estado == "completado",
            )
        )
        completados = cnt_r.scalar() or 0

        # Fetch exam title
        titulo = None
        grado_nombre = None
        if a.tipo_examen == "lectura" and a.examen_lectura_id:
            r = await db.execute(
                select(ExamenLectura.titulo, ExamenLectura.grado_nombre)
                .where(ExamenLectura.id == a.examen_lectura_id)
            )
            row = r.first()
            if row:
                titulo, grado_nombre = row.titulo, row.grado_nombre
        elif a.tipo_examen == "matematica" and a.examen_matematica_id:
            r = await db.execute(
                select(ExamenMatematica.titulo, ExamenMatematica.grado_nombre)
                .where(ExamenMatematica.id == a.examen_matematica_id)
            )
            row = r.first()
            if row:
                titulo, grado_nombre = row.titulo, row.grado_nombre

        out.append({
            "id": a.id,
            "tipo_examen": a.tipo_examen,
            "titulo": titulo,
            "grado_id": a.grado_id,
            "grado_nombre": grado_nombre,
            "seccion": a.seccion,
            "fecha_inicio": a.fecha_inicio.isoformat() if a.fecha_inicio else None,
            "fecha_fin": a.fecha_fin.isoformat() if a.fecha_fin else None,
            "duracion_minutos": a.duracion_minutos,
            "intentos_permitidos": a.intentos_permitidos,
            "is_active": a.is_active,
            "completados": completados,
            "fecha_creacion": a.fecha_creacion.isoformat() if a.fecha_creacion else None,
        })
    return out


@router.get("/examenes/asignaciones/{asig_id}/resultados")
async def resultados_asignacion(
    asig_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_modulo("asignaciones")),
):
    """Ver resultados de estudiantes para una asignación específica."""
    result = await db.execute(select(AsignacionExamen).where(AsignacionExamen.id == asig_id))
    asig = result.scalars().first()
    if not asig:
        raise HTTPException(404, "Asignación no encontrada")
    if asig.asignado_por_id != current_user.id:
        raise HTTPException(403, "No tienes acceso a esta asignación")

    intentos_r = await db.execute(
        select(IntentoExamen).where(
            IntentoExamen.asignacion_id == asig_id,
            IntentoExamen.estado == "completado",
        ).order_by(IntentoExamen.puntaje_total.desc())
    )
    intentos = intentos_r.scalars().all()

    resultado = []
    for i in intentos:
        est_r = await db.execute(
            select(Usuario.nombres, Usuario.apellidos, Usuario.codigo_estudiante)
            .where(Usuario.id == i.estudiante_id)
        )
        row = est_r.first()
        resultado.append({
            "estudiante": f"{row.nombres or ''} {row.apellidos or ''}".strip() or row.codigo_estudiante,
            "codigo": row.codigo_estudiante,
            "puntaje": i.puntaje_total,
            "nivel_logro": i.nivel_logro,
            "correctas": i.preguntas_correctas,
            "total": i.preguntas_total,
            "fecha": i.fecha_fin.isoformat() if i.fecha_fin else None,
        })
    return resultado


@router.delete("/examenes/asignaciones/{asig_id}")
async def eliminar_asignacion(
    asig_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_modulo("asignaciones")),
):
    result = await db.execute(select(AsignacionExamen).where(AsignacionExamen.id == asig_id))
    asig = result.scalars().first()
    if not asig:
        raise HTTPException(404, "Asignación no encontrada")
    if asig.asignado_por_id != current_user.id:
        raise HTTPException(403, "No tienes acceso")
    await db.delete(asig)
    await db.flush()
    return {"ok": True}
