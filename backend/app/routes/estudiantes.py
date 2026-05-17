"""
Rutas del portal estudiantil: exámenes, intentos y progreso.
"""
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from pydantic import BaseModel

from app.core.database import get_db
from app.models.db_models import (
    AsignacionExamen, IntentoExamen, ProgresoEstudiante,
    ExamenLectura, ExamenMatematica,
    PreguntaExamen, Rol, CodigoClase,
)
from app.models.usuario import Usuario
from app.models.enums import RolCodigo
from app.api.dependencies import get_estudiante_user, get_current_active_user, require_role, require_modulo
from app.services.examen_service import examen_service

router = APIRouter()

EXAM_CREATOR_ROLES = (
    RolCodigo.DOCENTE, RolCodigo.AUXILIAR, RolCodigo.DIRECTOR,
    RolCodigo.ESPECIALISTA_DRE_COMUNICACION, RolCodigo.ESPECIALISTA_DRE_MATEMATICA,
)


# ─── Schemas ─────────────────────────────────────────────────────────────────

class RespuestaEnvio(BaseModel):
    pregunta_numero: int
    respuesta: str


class FinalizarIntentoRequest(BaseModel):
    respuestas: List[RespuestaEnvio]


class AsignarExamenRequest(BaseModel):
    tipo_examen: str  # "lectura" o "matematica"
    examen_id: int
    codigo_clase_id: Optional[int] = None  # FK a codigos_clase; si se provee, grado_id+seccion se auto-pueblan
    grado_id: Optional[int] = None
    seccion: Optional[str] = None
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    duracion_minutos: Optional[int] = None
    intentos_permitidos: int = 1
    mostrar_resultados: bool = True
    mezclar_preguntas: bool = False
    mezclar_alternativas: bool = False


class UpdateAsignacionRequest(BaseModel):
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    duracion_minutos: Optional[int] = None
    intentos_permitidos: int = 1
    mezclar_preguntas: bool = False
    mezclar_alternativas: bool = False
    is_active: bool = True


# ─── Portal estudiante: preview de lectura (sin crear intento) ───────────────

@router.get("/estudiante/examenes/{asignacion_id}/preview")
async def preview_examen(
    asignacion_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_estudiante_user),
):
    """Devuelve el texto de lectura/situación del examen sin crear intento."""
    result = await db.execute(select(AsignacionExamen).where(AsignacionExamen.id == asignacion_id))
    asig = result.scalars().first()
    if not asig or not asig.is_active:
        raise HTTPException(404, "Examen no encontrado")
    if asig.institucion_educativa_id and asig.institucion_educativa_id != current_user.institucion_educativa_id:
        raise HTTPException(403, "No tienes acceso a este examen")

    if asig.tipo_examen == "lectura":
        ex_r = await db.execute(select(ExamenLectura).where(ExamenLectura.id == asig.examen_id))
        examen = ex_r.scalars().first()
        if not examen:
            raise HTTPException(404, "Examen no encontrado")
        lecturas = examen.lecturas or [{"titulo": "", "texto": examen.lectura or ""}]
        return {
            "titulo": examen.titulo or "Examen de Comunicación",
            "tipo_examen": "lectura",
            "lecturas": lecturas,
            "instrucciones": examen.instrucciones or "",
        }
    elif asig.tipo_examen == "matematica":
        ex_r = await db.execute(select(ExamenMatematica).where(ExamenMatematica.id == asig.examen_id))
        examen = ex_r.scalars().first()
        if not examen:
            raise HTTPException(404, "Examen no encontrado")
        return {
            "titulo": examen.titulo or "Examen de Matemática",
            "tipo_examen": "matematica",
            "lecturas": [{"titulo": "", "texto": examen.situacion_problematica or ""}],
            "instrucciones": "",
        }
    raise HTTPException(400, "Tipo de examen no soportado")


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
        or_(
            AsignacionExamen.fecha_fin == None,
            AsignacionExamen.fecha_fin >= ahora,
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
        if a.tipo_examen == "lectura":
            ex_r = await db.execute(select(ExamenLectura.titulo).where(ExamenLectura.id == a.examen_id))
            t = ex_r.scalar()
            if t:
                titulo = t
        elif a.tipo_examen == "matematica":
            ex_r = await db.execute(select(ExamenMatematica.titulo).where(ExamenMatematica.id == a.examen_id))
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

    # Usar UTC naive para comparar con las fechas almacenadas
    # SQLite no almacena timezone, así que comparamos naive-vs-naive en UTC
    ahora = datetime.now(timezone.utc).replace(tzinfo=None)
    def _naive(dt):
        """Normalizar datetime a naive UTC para comparar."""
        if dt is None:
            return None
        if dt.tzinfo:
            return dt.replace(tzinfo=None)
        return dt

    if asig.fecha_inicio and _naive(asig.fecha_inicio) > ahora:
        raise HTTPException(400, "El examen aún no está habilitado")
    if asig.fecha_fin and _naive(asig.fecha_fin) < ahora:
        raise HTTPException(400, "El horario del examen ya finalizó")

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

    # Obtener preguntas desde la tabla normalizada
    if asig.tipo_examen == "lectura":
        ex_r = await db.execute(select(ExamenLectura).where(ExamenLectura.id == asig.examen_id))
        examen = ex_r.scalars().first()
        if not examen:
            raise HTTPException(404, "Examen de lectura no encontrado")
        preguntas_r = await db.execute(
            select(PreguntaExamen)
            .where(PreguntaExamen.examen_lectura_id == asig.examen_id)
            .order_by(PreguntaExamen.numero)
        )
        preguntas = preguntas_r.scalars().all()
        lecturas = examen.lecturas or [{"titulo": "", "texto": examen.lectura or ""}]
        return {
            "titulo": examen.titulo or "Examen de Comunicación",
            "instrucciones": examen.instrucciones or "",
            "lectura": examen.lectura or "",
            "lecturas": lecturas,
            "preguntas": examen_service.mezclar_examen(
                examen_service.preparar_preguntas(preguntas),
                mezclar_preguntas=asig.mezclar_preguntas,
                mezclar_alternativas=asig.mezclar_alternativas,
                seed_base=f"{asig.id}:{intento.id}:lectura",
            ),
            "duracion_minutos": asig.duracion_minutos,
            "intento_id": intento.id,
        }
    elif asig.tipo_examen == "matematica":
        ex_r = await db.execute(select(ExamenMatematica).where(ExamenMatematica.id == asig.examen_id))
        examen = ex_r.scalars().first()
        if not examen:
            raise HTTPException(404, "Examen de matemática no encontrado")
        preguntas_r = await db.execute(
            select(PreguntaExamen)
            .where(PreguntaExamen.examen_matematica_id == asig.examen_id)
            .order_by(PreguntaExamen.numero)
        )
        preguntas = preguntas_r.scalars().all()
        return {
            "titulo": examen.titulo or "Examen de Matemática",
            "instrucciones": "",
            "lectura": examen.situacion_problematica or "",
            "lecturas": [{"titulo": "", "texto": examen.situacion_problematica or ""}],
            "preguntas": examen_service.mezclar_examen(
                examen_service.preparar_preguntas(preguntas),
                mezclar_preguntas=asig.mezclar_preguntas,
                mezclar_alternativas=asig.mezclar_alternativas,
                seed_base=f"{asig.id}:{intento.id}:matematica",
            ),
            "duracion_minutos": asig.duracion_minutos,
            "intento_id": intento.id,
        }
    else:
        raise HTTPException(400, "Tipo de examen no soportado")


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

    asig_r = await db.execute(select(AsignacionExamen).where(AsignacionExamen.id == intento.asignacion_id))
    asig = asig_r.scalars().first()

    return await examen_service.calificar_y_persistir(db, intento, asig, data.respuestas)


@router.get("/estudiante/examenes/{asignacion_id}/revision")
async def revision_por_asignacion(
    asignacion_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_estudiante_user),
):
    """Obtiene el último intento completado de la asignación y devuelve su revisión."""
    ult_r = await db.execute(
        select(IntentoExamen).where(
            IntentoExamen.asignacion_id == asignacion_id,
            IntentoExamen.estudiante_id == current_user.id,
            IntentoExamen.estado == "completado",
        ).order_by(IntentoExamen.numero_intento.desc())
    )
    ultimo = ult_r.scalars().first()
    if not ultimo:
        raise HTTPException(404, "No hay intentos completados para este examen")
    return await examen_service.construir_revision(db, ultimo.id, current_user)


@router.get("/estudiante/intentos/{intento_id}/revision")
async def revision_intento(
    intento_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_estudiante_user),
):
    """Revisión detallada de un intento específico con retroalimentación IA."""
    return await examen_service.construir_revision(db, intento_id, current_user)


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
    examen_service.validar_rango_horario(data.fecha_inicio, data.fecha_fin)

    # Si se provee un codigo_clase_id, derivar grado_id y seccion de él
    grado_id = data.grado_id
    seccion = data.seccion
    codigo_clase_id = data.codigo_clase_id
    if codigo_clase_id:
        cc_r = await db.execute(select(CodigoClase).where(CodigoClase.id == codigo_clase_id))
        cc = cc_r.scalars().first()
        if not cc:
            raise HTTPException(404, "Código de clase no encontrado")
        grado_id = cc.grado_id
        seccion = cc.seccion

    kwargs = dict(
        tipo_examen=data.tipo_examen,
        asignado_por_id=current_user.id,
        institucion_educativa_id=current_user.institucion_educativa_id,
        codigo_clase_id=codigo_clase_id,
        grado_id=grado_id,
        seccion=seccion,
        fecha_inicio=data.fecha_inicio,
        fecha_fin=data.fecha_fin,
        duracion_minutos=data.duracion_minutos,
        intentos_permitidos=data.intentos_permitidos,
        mostrar_resultados=data.mostrar_resultados,
        mezclar_preguntas=data.mezclar_preguntas,
        mezclar_alternativas=data.mezclar_alternativas,
    )
    kwargs["examen_id"] = data.examen_id

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
    """Lista asignaciones scoped por rol: director/auxiliar ve su IE, UGEL ve sus IEs, DRE ve todo."""
    from app.models.db_models import InstitucionEducativa
    rol = RolCodigo(current_user.rol_codigo)
    ie_id = current_user.institucion_educativa_id
    ugel_id = current_user.ugel_id
    DRE_ROLES = {RolCodigo.ESPECIALISTA_DRE_COMUNICACION, RolCodigo.ESPECIALISTA_DRE_MATEMATICA}
    GESTORES_IE = {RolCodigo.DIRECTOR, RolCodigo.AUXILIAR}

    if rol in DRE_ROLES:
        q = select(AsignacionExamen)
    elif rol == RolCodigo.RESPONSABLE_UGEL and ugel_id:
        ie_ids_r = await db.execute(
            select(InstitucionEducativa.id).where(InstitucionEducativa.ugel_id == ugel_id)
        )
        ie_ids = [r[0] for r in ie_ids_r.all()]
        q = select(AsignacionExamen).where(AsignacionExamen.institucion_educativa_id.in_(ie_ids))
    elif rol in GESTORES_IE and ie_id:
        q = select(AsignacionExamen).where(AsignacionExamen.institucion_educativa_id == ie_id)
    else:
        q = select(AsignacionExamen).where(AsignacionExamen.asignado_por_id == current_user.id)

    result = await db.execute(q.order_by(AsignacionExamen.fecha_creacion.desc()))
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

        titulo = None
        grado_nombre = None
        if a.tipo_examen == "lectura":
            r = await db.execute(
                select(ExamenLectura.titulo, ExamenLectura.grado_nombre)
                .where(ExamenLectura.id == a.examen_id)
            )
            row = r.first()
            if row:
                titulo, grado_nombre = row.titulo, row.grado_nombre
        elif a.tipo_examen == "matematica":
            r = await db.execute(
                select(ExamenMatematica.titulo, ExamenMatematica.grado_nombre)
                .where(ExamenMatematica.id == a.examen_id)
            )
            row = r.first()
            if row:
                titulo, grado_nombre = row.titulo, row.grado_nombre

        # Nombre del creador (solo si no es el propio usuario)
        asignado_por_nombre = None
        if a.asignado_por_id != current_user.id:
            cr_r = await db.execute(
                select(Usuario.nombres, Usuario.apellidos, Usuario.dni)
                .where(Usuario.id == a.asignado_por_id)
            )
            cr = cr_r.first()
            if cr:
                asignado_por_nombre = f"{cr.nombres or ''} {cr.apellidos or ''}".strip() or cr.dni

        puede_eliminar = (
            a.asignado_por_id == current_user.id
            or rol in GESTORES_IE
            or rol in DRE_ROLES
        )

        out.append({
            "id": a.id,
            "tipo_examen": a.tipo_examen,
            "titulo": titulo,
            "grado_id": a.grado_id,
            "grado_nombre": grado_nombre,
            "seccion": a.seccion,
            "codigo_clase_id": a.codigo_clase_id,
            "fecha_inicio": a.fecha_inicio.isoformat() if a.fecha_inicio else None,
            "fecha_fin": a.fecha_fin.isoformat() if a.fecha_fin else None,
            "duracion_minutos": a.duracion_minutos,
            "intentos_permitidos": a.intentos_permitidos,
            "mezclar_preguntas": a.mezclar_preguntas,
            "mezclar_alternativas": a.mezclar_alternativas,
            "is_active": a.is_active,
            "completados": completados,
            "fecha_creacion": a.fecha_creacion.isoformat() if a.fecha_creacion else None,
            "asignado_por_id": a.asignado_por_id,
            "asignado_por_nombre": asignado_por_nombre,
            "puede_eliminar": puede_eliminar,
        })
    return out


@router.get("/examenes/asignaciones/{asig_id}/resultados")
async def resultados_asignacion(
    asig_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_modulo("asignaciones")),
):
    """Ver resultados de una asignación. Directores ven toda su IE, DRE ve todo."""
    result = await db.execute(select(AsignacionExamen).where(AsignacionExamen.id == asig_id))
    asig = result.scalars().first()
    if not asig:
        raise HTTPException(404, "Asignación no encontrada")

    rol = RolCodigo(current_user.rol_codigo)
    DRE_ROLES = {RolCodigo.ESPECIALISTA_DRE_COMUNICACION, RolCodigo.ESPECIALISTA_DRE_MATEMATICA}
    GESTORES_IE = {RolCodigo.DIRECTOR, RolCodigo.AUXILIAR}

    is_creator = asig.asignado_por_id == current_user.id
    is_gestor_ie = rol in GESTORES_IE and asig.institucion_educativa_id == current_user.institucion_educativa_id
    is_dre = rol in DRE_ROLES

    if not (is_creator or is_gestor_ie or is_dre):
        raise HTTPException(403, "No tienes acceso a esta asignación")

    intentos_r = await db.execute(
        select(IntentoExamen).where(
            IntentoExamen.asignacion_id == asig_id,
        ).order_by(IntentoExamen.estudiante_id, IntentoExamen.numero_intento.desc())
    )
    intentos = intentos_r.scalars().all()
    ultimo_intento_por_estudiante: dict[int, IntentoExamen] = {}
    for intento in intentos:
        if intento.estudiante_id not in ultimo_intento_por_estudiante:
            ultimo_intento_por_estudiante[intento.estudiante_id] = intento

    rol_estudiante_r = await db.execute(
        select(Rol.id).where(Rol.codigo == RolCodigo.ESTUDIANTE.value)
    )
    rol_estudiante_id = rol_estudiante_r.scalar()

    estudiantes_q = select(Usuario).where(
        Usuario.institucion_educativa_id == asig.institucion_educativa_id,
    )
    if rol_estudiante_id:
        estudiantes_q = estudiantes_q.where(Usuario.rol_id == rol_estudiante_id)
    if asig.grado_id is not None:
        estudiantes_q = estudiantes_q.where(Usuario.grado_id == asig.grado_id)
    if asig.seccion is not None:
        estudiantes_q = estudiantes_q.where(Usuario.seccion == asig.seccion)

    estudiantes_r = await db.execute(
        estudiantes_q.order_by(Usuario.apellidos, Usuario.nombres)
    )
    estudiantes = estudiantes_r.scalars().all()

    resultado = []
    for estudiante in estudiantes:
        intento = ultimo_intento_por_estudiante.get(estudiante.id)
        resultado.append({
            "estudiante": f"{estudiante.nombres or ''} {estudiante.apellidos or ''}".strip() or estudiante.codigo_estudiante,
            "codigo": estudiante.codigo_estudiante or estudiante.dni,
            "estado": intento.estado if intento else "sin_intento",
            "puntaje": intento.puntaje_total if intento else None,
            "nivel_logro": intento.nivel_logro if intento else None,
            "correctas": intento.preguntas_correctas if intento else None,
            "total": intento.preguntas_total if intento else None,
            "fecha": intento.fecha_fin.isoformat() if intento and intento.fecha_fin else None,
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

    rol = RolCodigo(current_user.rol_codigo)
    DRE_ROLES = {RolCodigo.ESPECIALISTA_DRE_COMUNICACION, RolCodigo.ESPECIALISTA_DRE_MATEMATICA}
    GESTORES_IE = {RolCodigo.DIRECTOR, RolCodigo.AUXILIAR}

    is_creator = asig.asignado_por_id == current_user.id
    is_gestor_ie = rol in GESTORES_IE and asig.institucion_educativa_id == current_user.institucion_educativa_id
    is_dre = rol in DRE_ROLES

    if not (is_creator or is_gestor_ie or is_dre):
        raise HTTPException(403, "No tienes acceso")
    await db.delete(asig)
    await db.flush()
    return {"ok": True}


@router.put("/examenes/asignaciones/{asig_id}")
async def actualizar_asignacion(
    asig_id: int,
    data: UpdateAsignacionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_modulo("asignaciones")),
):
    result = await db.execute(select(AsignacionExamen).where(AsignacionExamen.id == asig_id))
    asig = result.scalars().first()
    if not asig:
        raise HTTPException(404, "Asignación no encontrada")

    rol = RolCodigo(current_user.rol_codigo)
    DRE_ROLES = {RolCodigo.ESPECIALISTA_DRE_COMUNICACION, RolCodigo.ESPECIALISTA_DRE_MATEMATICA}
    GESTORES_IE = {RolCodigo.DIRECTOR, RolCodigo.AUXILIAR}

    is_creator = asig.asignado_por_id == current_user.id
    is_gestor_ie = rol in GESTORES_IE and asig.institucion_educativa_id == current_user.institucion_educativa_id
    is_dre = rol in DRE_ROLES

    if not (is_creator or is_gestor_ie or is_dre):
        raise HTTPException(403, "No tienes acceso a esta asignación")

    examen_service.validar_rango_horario(data.fecha_inicio, data.fecha_fin)

    asig.fecha_inicio = data.fecha_inicio
    asig.fecha_fin = data.fecha_fin
    asig.duracion_minutos = data.duracion_minutos
    asig.intentos_permitidos = data.intentos_permitidos
    asig.mezclar_preguntas = data.mezclar_preguntas
    asig.mezclar_alternativas = data.mezclar_alternativas
    asig.is_active = data.is_active

    await db.flush()
    return {"ok": True}
