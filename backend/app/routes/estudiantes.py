"""
Rutas del portal estudiantil: exámenes, intentos y progreso.
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, or_
from pydantic import BaseModel, field_validator

from app.core.database import get_db
from app.core.db_retry import con_reintento
from app.core.tz import a_peru_naive, ahora_peru, iso_peru
from app.core.escala_cneb import clasificar, porcentaje_a_nota, nota_a_nivel
from app.models.db_models import (
    AsignacionExamen, IntentoExamen, ProgresoEstudiante,
    ExamenLectura, ExamenMatematica, TextoExamen,
    PreguntaExamen, Rol, CodigoClase, Matricula, Grado,
)
from app.models.usuario import Usuario
from app.models.estudiante import Estudiante
from app.models.enums import RolCodigo
from app.api.dependencies import get_estudiante_user, get_current_active_user, require_role, require_modulo
from app.services.examen_service import examen_service
from app.services.examen_serializer import lecturas_dict, texto_concatenado, texto_plano
from app.services.matricula_service import get_matricula_activa

router = APIRouter()


async def _cargar_textos(
    db: AsyncSession,
    *,
    examen_lectura_id: Optional[int] = None,
    examen_matematica_id: Optional[int] = None,
) -> list[TextoExamen]:
    """Carga los textos normalizados de un examen, ordenados."""
    if examen_lectura_id is not None:
        q = (
            select(TextoExamen)
            .where(TextoExamen.examen_lectura_id == examen_lectura_id)
            .order_by(TextoExamen.orden)
        )
    else:
        q = (
            select(TextoExamen)
            .where(TextoExamen.examen_matematica_id == examen_matematica_id)
            .order_by(TextoExamen.orden)
        )
    result = await db.execute(q)
    return result.scalars().all()


EXAM_CREATOR_ROLES = (
    RolCodigo.DOCENTE, RolCodigo.AUXILIAR, RolCodigo.DIRECTOR,
    RolCodigo.ESPECIALISTA_DRE_COMUNICACION, RolCodigo.ESPECIALISTA_DRE_MATEMATICA,
)


def _iso_peru(dt: Optional[datetime]) -> Optional[str]:
    """Serializa un datetime guardado en hora Perú (naive) con offset -05:00.

    Sin el offset el frontend interpretaría el string como hora local del
    navegador y lo mostraría corrido si la zona del equipo no es Perú.
    """
    return iso_peru(dt)


def _peru_naive(dt: Optional[datetime]) -> Optional[datetime]:
    """Normaliza a hora Perú naive para comparar contra las fechas almacenadas.

    SQLite/MySQL no conservan timezone, así que comparamos naive-vs-naive en
    hora Perú.
    """
    return a_peru_naive(dt)


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
    año_escolar: Optional[int] = None  # default: año actual
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    duracion_minutos: Optional[int] = None
    intentos_permitidos: int = 1
    mostrar_resultados: bool = True
    mezclar_preguntas: bool = False
    mezclar_alternativas: bool = False

    @field_validator("fecha_inicio", "fecha_fin")
    @classmethod
    def _a_hora_peru(cls, v: Optional[datetime]) -> Optional[datetime]:
        return a_peru_naive(v)


class UpdateAsignacionRequest(BaseModel):
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    duracion_minutos: Optional[int] = None
    intentos_permitidos: int = 1
    mezclar_preguntas: bool = False
    mezclar_alternativas: bool = False
    is_active: bool = True

    @field_validator("fecha_inicio", "fecha_fin")
    @classmethod
    def _a_hora_peru(cls, v: Optional[datetime]) -> Optional[datetime]:
        return a_peru_naive(v)


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
        textos = await _cargar_textos(db, examen_lectura_id=asig.examen_id)
        lecturas = lecturas_dict(textos)
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
        textos = await _cargar_textos(db, examen_matematica_id=asig.examen_id)
        lecturas = lecturas_dict(textos)
        return {
            "titulo": examen.titulo or "Examen de Matemática",
            "tipo_examen": "matematica",
            "lecturas": lecturas,
            "instrucciones": examen.instrucciones or "",
        }
    raise HTTPException(400, "Tipo de examen no soportado")


# ─── Portal estudiante: listar exámenes ──────────────────────────────────────

@router.get("/estudiante/examenes")
async def listar_examenes_estudiante(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_estudiante_user),
):
    """Lista los exámenes asignados al estudiante."""
    matricula = await get_matricula_activa(db, current_user.id)
    ahora = ahora_peru()
    ahora_naive = ahora
    q = select(AsignacionExamen).where(
        AsignacionExamen.is_active == True,
        AsignacionExamen.institucion_educativa_id == current_user.institucion_educativa_id,
        or_(
            AsignacionExamen.año_escolar == None,
            AsignacionExamen.año_escolar == (matricula.año_escolar if matricula else datetime.now().year),
        ),
        or_(
            AsignacionExamen.grado_id == None,
            AsignacionExamen.grado_id == (matricula.grado_id if matricula else None),
        ),
        or_(
            AsignacionExamen.seccion == None,
            AsignacionExamen.seccion == (matricula.seccion if matricula else None),
        ),
        or_(
            AsignacionExamen.fecha_fin == None,
            AsignacionExamen.fecha_fin >= ahora,
            # Mostrar siempre si el estudiante ya completó el examen (aunque esté vencido)
            AsignacionExamen.id.in_(
                select(IntentoExamen.asignacion_id).where(
                    IntentoExamen.estudiante_id == current_user.id,
                    IntentoExamen.estado == "completado",
                ).distinct()
            ),
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

        inicio = _peru_naive(a.fecha_inicio)
        fin = _peru_naive(a.fecha_fin)
        disponible = (
            (inicio is None or inicio <= ahora_naive)
            and (fin is None or fin >= ahora_naive)
        )

        examenes_out.append({
            "id": a.id,
            "tipo_examen": a.tipo_examen,
            "titulo": titulo,
            "fecha_inicio": _iso_peru(a.fecha_inicio),
            "fecha_fin": _iso_peru(a.fecha_fin),
            "duracion_minutos": a.duracion_minutos,
            "intentos_permitidos": a.intentos_permitidos,
            "mis_intentos": mis_intentos,
            "completado": ultimo is not None,
            "puntaje": ultimo.puntaje_total if ultimo else None,
            "nivel_logro": ultimo.nivel_logro if ultimo else None,
            "nota_vigesimal": ultimo.nota_vigesimal if ultimo else None,
            "nivel_cneb": ultimo.nivel_cneb if ultimo else None,
            "disponible": disponible,
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

    # Usar hora Perú naive para comparar con las fechas almacenadas
    # SQLite no almacena timezone, así que comparamos naive-vs-naive
    ahora = ahora_peru()

    if asig.fecha_inicio and _peru_naive(asig.fecha_inicio) > ahora:
        raise HTTPException(400, "El examen aún no está habilitado")
    if asig.fecha_fin and _peru_naive(asig.fecha_fin) < ahora:
        raise HTTPException(400, "El horario del examen ya finalizó")

    # Verificar que el estudiante pertenece a este examen
    if asig.institucion_educativa_id and asig.institucion_educativa_id != current_user.institucion_educativa_id:
        raise HTTPException(403, "No tienes acceso a este examen")

    # Capturados como valores planos: con_reintento() puede hacer db.rollback() entre
    # reintentos, lo que expira los atributos ORM de todo lo cargado en esta sesión
    # (current_user, asig). Volver a tocar esos atributos después (current_user.id,
    # asig.tipo_examen, etc.) dispararía una carga perezosa fuera de un contexto
    # async-safe (sqlalchemy.exc.MissingGreenlet), así que de aquí en adelante solo
    # se usan estas variables planas, nunca los objetos ORM originales.
    estudiante_id = current_user.id
    asig_id = asig.id
    asig_intentos_permitidos = asig.intentos_permitidos
    asig_tipo_examen = asig.tipo_examen
    asig_examen_id = asig.examen_id
    asig_mezclar_preguntas = asig.mezclar_preguntas
    asig_mezclar_alternativas = asig.mezclar_alternativas
    asig_duracion_minutos = asig.duracion_minutos

    async def _obtener_o_crear_intento():
        # Bloquea (FOR UPDATE) todos los intentos de ESTE estudiante para ESTE examen.
        # Al ser un rango acotado por (asignacion_id, estudiante_id) — prefijo del índice
        # único uq_intento —, dos requests concurrentes del mismo estudiante (doble clic,
        # reintento de red) quedan serializadas aquí sin bloquear a otros estudiantes que
        # inician el mismo examen en paralelo. Cuando ambas colisionan en el mismo hueco
        # (ninguna fila existe todavía) InnoDB puede resolverlo como deadlock (1213) o,
        # bajo innodb_snapshot_isolation de MariaDB, como conflicto de snapshot (1020)
        # en vez de una espera silenciosa — con_reintento() reintenta la transacción.
        todos_r = await db.execute(
            select(IntentoExamen).where(
                IntentoExamen.asignacion_id == asignacion_id,
                IntentoExamen.estudiante_id == estudiante_id,
            ).with_for_update()
        )
        todos_intentos = todos_r.scalars().all()
        intento = next((i for i in todos_intentos if i.estado == "en_progreso"), None)

        if not intento:
            num_completados = sum(1 for i in todos_intentos if i.estado == "completado")
            if num_completados >= asig_intentos_permitidos:
                raise HTTPException(400, "Has agotado los intentos permitidos")

            intento = IntentoExamen(
                asignacion_id=asignacion_id,
                estudiante_id=estudiante_id,
                numero_intento=len(todos_intentos) + 1,
                estado="en_progreso",
                fecha_inicio=ahora_peru(),
            )
            db.add(intento)
            await db.flush()
            await db.refresh(intento)
        return intento

    intento = await con_reintento(db, _obtener_o_crear_intento)

    # Obtener preguntas desde la tabla normalizada
    if asig_tipo_examen == "lectura":
        ex_r = await db.execute(select(ExamenLectura).where(ExamenLectura.id == asig_examen_id))
        examen = ex_r.scalars().first()
        if not examen:
            raise HTTPException(404, "Examen de lectura no encontrado")
        preguntas_r = await db.execute(
            select(PreguntaExamen)
            .where(PreguntaExamen.examen_lectura_id == asig_examen_id)
            .order_by(PreguntaExamen.numero)
        )
        preguntas = preguntas_r.scalars().all()
        textos = await _cargar_textos(db, examen_lectura_id=asig_examen_id)
        lecturas = lecturas_dict(textos)
        lectura = texto_concatenado(textos)
        return {
            "titulo": examen.titulo or "Examen de Comunicación",
            "instrucciones": examen.instrucciones or "",
            "lectura": lectura,
            "lecturas": lecturas,
            "preguntas": examen_service.mezclar_examen(
                examen_service.preparar_preguntas(preguntas),
                mezclar_preguntas=asig_mezclar_preguntas,
                mezclar_alternativas=asig_mezclar_alternativas,
                seed_base=f"{asig_id}:{intento.id}:lectura",
            ),
            "duracion_minutos": asig_duracion_minutos,
            "intento_id": intento.id,
        }
    elif asig_tipo_examen == "matematica":
        ex_r = await db.execute(select(ExamenMatematica).where(ExamenMatematica.id == asig_examen_id))
        examen = ex_r.scalars().first()
        if not examen:
            raise HTTPException(404, "Examen de matemática no encontrado")
        preguntas_r = await db.execute(
            select(PreguntaExamen)
            .where(PreguntaExamen.examen_matematica_id == asig_examen_id)
            .order_by(PreguntaExamen.numero)
        )
        preguntas = preguntas_r.scalars().all()
        textos = await _cargar_textos(db, examen_matematica_id=asig_examen_id)
        lecturas = lecturas_dict(textos)
        situacion = texto_plano(textos)
        return {
            "titulo": examen.titulo or "Examen de Matemática",
            "instrucciones": examen.instrucciones or "",
            "lectura": situacion,
            "lecturas": lecturas,
            "preguntas": examen_service.mezclar_examen(
                examen_service.preparar_preguntas(preguntas),
                mezclar_preguntas=asig_mezclar_preguntas,
                mezclar_alternativas=asig_mezclar_alternativas,
                seed_base=f"{asig_id}:{intento.id}:matematica",
            ),
            "duracion_minutos": asig_duracion_minutos,
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
        "nota_vigesimal": ultimo.nota_vigesimal,
        "nivel_cneb": ultimo.nivel_cneb,
    }



@router.post("/estudiante/intentos/{intento_id}/finalizar")
async def finalizar_intento(
    intento_id: int,
    data: FinalizarIntentoRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_estudiante_user),
):
    """Finaliza el intento, califica y actualiza el progreso."""
    estudiante_id = current_user.id  # ver nota de MissingGreenlet en iniciar_examen

    # Reclamo atómico: producción corre en tablas MyISAM, que ignoran SELECT ... FOR
    # UPDATE y no tienen rollback real, así que un "leer estado, luego decidir" no
    # protege nada ahí. Una única sentencia UPDATE sí es atómica en el servidor
    # independientemente del motor — si esta llamada no logra pasar `rowcount == 1`,
    # perdió la carrera contra otra finalización concurrente (o el intento no existe/
    # no es suyo) y no debe tocar RespuestaIntento ni ProgresoEstudiante en absoluto,
    # evitando así cualquier escritura duplicada/parcial no reversible.
    claim = await db.execute(
        update(IntentoExamen)
        .where(
            IntentoExamen.id == intento_id,
            IntentoExamen.estudiante_id == estudiante_id,
            IntentoExamen.estado != "completado",
        )
        .values(estado="completado", fecha_fin=ahora_peru())
    )
    if claim.rowcount == 0:
        existe_r = await db.execute(
            select(IntentoExamen.id).where(
                IntentoExamen.id == intento_id, IntentoExamen.estudiante_id == estudiante_id
            )
        )
        if not existe_r.scalar():
            raise HTTPException(404, "Intento no encontrado")
        raise HTTPException(400, "Este intento ya fue completado")

    result = await db.execute(select(IntentoExamen).where(IntentoExamen.id == intento_id))
    intento = result.scalars().first()
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
    matricula_activa_r = await db.execute(
        select(Matricula.id).where(
            Matricula.estudiante_id == current_user.id,
            Matricula.is_active == True,
        ).limit(1)
    )
    matricula_id = matricula_activa_r.scalar()
    result = await db.execute(
        select(ProgresoEstudiante).where(ProgresoEstudiante.matricula_id == matricula_id)
        if matricula_id else select(ProgresoEstudiante).where(False)
    )
    progresos = result.scalars().all()
    return [
        {
            "area": p.area,
            "total_examenes_completados": p.total_examenes_completados,
            "puntaje_promedio": round(p.puntaje_promedio or 0, 2),
            "nivel_logro_actual": p.nivel_logro_actual,
            "nota_promedio_vigesimal": porcentaje_a_nota(p.puntaje_promedio),
            "nivel_cneb_actual": (
                nota_a_nivel(porcentaje_a_nota(p.puntaje_promedio))
                if p.puntaje_promedio is not None else None
            ),
            "ultima_actividad": _iso_peru(p.ultima_actividad),
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

    # Validar que el examen exista, tenga preguntas y que sean calificables
    # automáticamente (las abiertas requieren calificación manual, aún no soportada).
    if data.tipo_examen == "lectura":
        existe = await db.execute(select(ExamenLectura.id).where(ExamenLectura.id == data.examen_id))
        filtro_preguntas = PreguntaExamen.examen_lectura_id == data.examen_id
    else:
        existe = await db.execute(select(ExamenMatematica.id).where(ExamenMatematica.id == data.examen_id))
        filtro_preguntas = PreguntaExamen.examen_matematica_id == data.examen_id
    if not existe.scalar():
        raise HTTPException(404, "Examen no encontrado")

    total_preguntas = (await db.execute(
        select(func.count(PreguntaExamen.id)).where(filtro_preguntas)
    )).scalar() or 0
    if total_preguntas == 0:
        raise HTTPException(400, "El examen no tiene preguntas para asignar")

    abiertas = (await db.execute(
        select(func.count(PreguntaExamen.id)).where(
            filtro_preguntas, PreguntaExamen.tipo == "abierta"
        )
    )).scalar() or 0
    if abiertas > 0:
        raise HTTPException(
            400,
            "Este examen contiene preguntas abiertas que requieren calificación manual; "
            "por ahora no se puede asignar en línea.",
        )

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
        año_escolar=data.año_escolar or datetime.now().year,
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
        if a.tipo_examen == "lectura":
            r = await db.execute(select(ExamenLectura.titulo).where(ExamenLectura.id == a.examen_id))
            titulo = r.scalar()
        elif a.tipo_examen == "matematica":
            r = await db.execute(select(ExamenMatematica.titulo).where(ExamenMatematica.id == a.examen_id))
            titulo = r.scalar()

        # Nombre del grado al que se asignó (no el grado del examen)
        grado_nombre = None
        if a.grado_id:
            gn = await db.execute(select(Grado.nombre).where(Grado.id == a.grado_id))
            grado_nombre = gn.scalar()
        elif a.codigo_clase_id:
            gn = await db.execute(
                select(Grado.nombre)
                .join(CodigoClase, CodigoClase.grado_id == Grado.id)
                .where(CodigoClase.id == a.codigo_clase_id)
            )
            grado_nombre = gn.scalar()

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
            "fecha_inicio": _iso_peru(a.fecha_inicio),
            "fecha_fin": _iso_peru(a.fecha_fin),
            "duracion_minutos": a.duracion_minutos,
            "intentos_permitidos": a.intentos_permitidos,
            "mezclar_preguntas": a.mezclar_preguntas,
            "mezclar_alternativas": a.mezclar_alternativas,
            "is_active": a.is_active,
            "completados": completados,
            "fecha_creacion": _iso_peru(a.fecha_creacion),
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

    from sqlalchemy import and_
    estudiantes_q = (
        select(Estudiante, Matricula, Grado.nombre)
        .join(Matricula, and_(
            Matricula.estudiante_id == Estudiante.id,
            Matricula.is_active == True,
        ))
        .outerjoin(Grado, Grado.id == Matricula.grado_id)
        .where(Estudiante.institucion_educativa_id == asig.institucion_educativa_id)
    )
    if asig.grado_id is not None:
        estudiantes_q = estudiantes_q.where(Matricula.grado_id == asig.grado_id)
    if asig.seccion is not None:
        estudiantes_q = estudiantes_q.where(Matricula.seccion == asig.seccion)
    if asig.año_escolar is not None:
        estudiantes_q = estudiantes_q.where(Matricula.año_escolar == asig.año_escolar)

    estudiantes_r = await db.execute(
        estudiantes_q.order_by(Estudiante.apellidos, Estudiante.nombres)
    )
    estudiantes = estudiantes_r.all()

    resultado = []
    for estudiante, matricula, grado_nombre in estudiantes:
        intento = ultimo_intento_por_estudiante.get(estudiante.id)
        resultado.append({
            "estudiante": f"{estudiante.nombres or ''} {estudiante.apellidos or ''}".strip() or estudiante.codigo_estudiante,
            "codigo": estudiante.codigo_estudiante or estudiante.dni,
            "grado": grado_nombre,
            "seccion": matricula.seccion if matricula else None,
            "estado": intento.estado if intento else "sin_intento",
            "puntaje": intento.puntaje_total if intento else None,
            "nivel_logro": intento.nivel_logro if intento else None,
            "nota_vigesimal": intento.nota_vigesimal if intento else None,
            "nivel_cneb": intento.nivel_cneb if intento else None,
            "correctas": intento.preguntas_correctas if intento else None,
            "total": intento.preguntas_total if intento else None,
            "fecha": _iso_peru(intento.fecha_fin) if intento else None,
        })
    return resultado


# Mapea el literal CNEB (AD/A/B/C) de la nota vigesimal a los 4 niveles del sistema.
_CNEB_A_4NIVELES = {"AD": "satisfactorio", "A": "proceso", "B": "inicio", "C": "pre_inicio"}
_NIVELES_4 = ["pre_inicio", "inicio", "proceso", "satisfactorio"]
_NIVEL_4_LABEL = {
    "pre_inicio": "Pre Inicio",
    "inicio": "En Inicio",
    "proceso": "En Proceso",
    "satisfactorio": "Satisfactorio",
}
_AREA_REPORTE = {"lectura": "LectoSistem", "matematica": "MatSistem"}


@router.get("/examenes/asignaciones/clasificacion")
async def clasificacion_niveles(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_modulo("asignaciones")),
    ugel_id: Optional[int] = None,
    institucion_educativa_id: Optional[int] = None,
    docente_id: Optional[int] = None,
    grado_id: Optional[int] = None,
    seccion: Optional[str] = None,
    año_escolar: Optional[int] = None,
):
    """Distribución de estudiantes por nivel de logro (escala vigesimal de 4 niveles).

    Agrupa el último intento completado de cada estudiante por asignación, dentro del
    scope del rol del usuario (DRE ve todo, UGEL sus IEs, director/auxiliar su IE,
    docente sus propias asignaciones). Acepta filtros jerárquicos opcionales
    (`ugel_id` → `institucion_educativa_id` → `docente_id` → aula) que siempre se
    combinan con el scope del rol, por lo que nunca amplían el acceso.
    La nota vigesimal (0-20) se convierte a 4 niveles usando los umbrales del CNEB:
    0-10 pre_inicio, 11-14 inicio, 15-17 proceso, 18-20 satisfactorio.
    """
    from app.models.db_models import InstitucionEducativa
    rol = RolCodigo(current_user.rol_codigo)
    user_ie_id = current_user.institucion_educativa_id
    user_ugel_id = current_user.ugel_id
    DRE_ROLES = {RolCodigo.ESPECIALISTA_DRE_COMUNICACION, RolCodigo.ESPECIALISTA_DRE_MATEMATICA}
    GESTORES_IE = {RolCodigo.DIRECTOR, RolCodigo.AUXILIAR}

    condiciones = []
    if rol in DRE_ROLES:
        pass  # ve todo
    elif rol == RolCodigo.RESPONSABLE_UGEL and user_ugel_id:
        ie_ids_r = await db.execute(
            select(InstitucionEducativa.id).where(InstitucionEducativa.ugel_id == user_ugel_id)
        )
        ie_ids = [r[0] for r in ie_ids_r.all()]
        condiciones.append(AsignacionExamen.institucion_educativa_id.in_(ie_ids))
    elif rol in GESTORES_IE and user_ie_id:
        condiciones.append(AsignacionExamen.institucion_educativa_id == user_ie_id)
    else:
        condiciones.append(AsignacionExamen.asignado_por_id == current_user.id)

    # Filtros jerárquicos: se suman (AND) al scope del rol.
    if ugel_id is not None:
        ie_ids_r = await db.execute(
            select(InstitucionEducativa.id).where(InstitucionEducativa.ugel_id == ugel_id)
        )
        condiciones.append(
            AsignacionExamen.institucion_educativa_id.in_([r[0] for r in ie_ids_r.all()])
        )
    if institucion_educativa_id is not None:
        condiciones.append(AsignacionExamen.institucion_educativa_id == institucion_educativa_id)
    if docente_id is not None:
        condiciones.append(AsignacionExamen.asignado_por_id == docente_id)
    if grado_id is not None:
        condiciones.append(AsignacionExamen.grado_id == grado_id)
    if seccion is not None:
        condiciones.append(AsignacionExamen.seccion == seccion)
    if año_escolar is not None:
        condiciones.append(AsignacionExamen.año_escolar == año_escolar)

    asig_q = select(AsignacionExamen.id)
    if condiciones:
        asig_q = asig_q.where(*condiciones)

    asig_ids_r = await db.execute(asig_q)
    asig_ids = [r[0] for r in asig_ids_r.all()]

    vacio = {"total_clasificados": 0, "sin_nivel": 0}
    for n in _NIVELES_4:
        vacio[n] = 0
    if not asig_ids:
        return vacio

    intentos_r = await db.execute(
        select(
            IntentoExamen.asignacion_id,
            IntentoExamen.estudiante_id,
            IntentoExamen.numero_intento,
            IntentoExamen.nota_vigesimal,
        )
        .where(
            IntentoExamen.asignacion_id.in_(asig_ids),
            IntentoExamen.estado == "completado",
        )
        .order_by(
            IntentoExamen.asignacion_id,
            IntentoExamen.estudiante_id,
            IntentoExamen.numero_intento.desc(),
        )
    )

    ultimos: dict = {}
    for asig_id, est_id, _num, nota in intentos_r.all():
        clave = (asig_id, est_id)
        if clave not in ultimos:
            ultimos[clave] = nota

    conteo = {n: 0 for n in _NIVELES_4}
    conteo["sin_nivel"] = 0
    for nota in ultimos.values():
        if nota is None:
            conteo["sin_nivel"] += 1
            continue
        nivel = _CNEB_A_4NIVELES.get(nota_a_nivel(nota), "sin_nivel")
        conteo[nivel] += 1

    total_clasificados = sum(conteo[n] for n in _NIVELES_4)
    return {"total_clasificados": total_clasificados, **conteo}


@router.get("/examenes/asignaciones/filtros")
async def filtros_clasificacion(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_modulo("asignaciones")),
):
    """Opciones jerárquicas (UGEL → IE → docente → aula) para filtrar la clasificación.

    Se derivan de las asignaciones dentro del scope del rol, de modo que el filtro
    siempre ofrece las aulas que realmente tienen resultados:
    - DRE: todas las UGELs, IEs, docentes y aulas.
    - UGEL: sus IEs, docentes y aulas.
    - Director/auxiliar: su IE, sus docentes y aulas.
    - Docente: únicamente sus asignaciones.
    """
    from app.models.db_models import InstitucionEducativa, Ugel

    rol = RolCodigo(current_user.rol_codigo)
    DRE_ROLES = {RolCodigo.ESPECIALISTA_DRE_COMUNICACION, RolCodigo.ESPECIALISTA_DRE_MATEMATICA}
    GESTORES_IE = {RolCodigo.DIRECTOR, RolCodigo.AUXILIAR}
    user_ie_id = current_user.institucion_educativa_id
    user_ugel_id = current_user.ugel_id

    condiciones = []
    if rol in DRE_ROLES:
        pass  # toda la región
    elif rol == RolCodigo.RESPONSABLE_UGEL and user_ugel_id:
        ie_ids_r = await db.execute(
            select(InstitucionEducativa.id).where(InstitucionEducativa.ugel_id == user_ugel_id)
        )
        condiciones.append(
            AsignacionExamen.institucion_educativa_id.in_([r[0] for r in ie_ids_r.all()])
        )
    elif rol in GESTORES_IE and user_ie_id:
        condiciones.append(AsignacionExamen.institucion_educativa_id == user_ie_id)
    else:
        condiciones.append(AsignacionExamen.asignado_por_id == current_user.id)

    # Solo filas identificables por IE + grado.
    condiciones.append(AsignacionExamen.institucion_educativa_id.isnot(None))
    condiciones.append(AsignacionExamen.grado_id.isnot(None))

    filas = (
        await db.execute(
            select(
                AsignacionExamen.institucion_educativa_id,
                AsignacionExamen.grado_id,
                AsignacionExamen.seccion,
                AsignacionExamen.año_escolar,
                AsignacionExamen.asignado_por_id,
            )
            .where(*condiciones)
            .distinct()
        )
    ).all()

    if not filas:
        return {"ugeles": [], "instituciones": [], "docentes": [], "aulas": []}

    ie_ids_set = {f[0] for f in filas}
    grado_ids = {f[1] for f in filas}
    docente_ids = {f[4] for f in filas if f[4]}

    grados_r = await db.execute(select(Grado).where(Grado.id.in_(grado_ids)))
    grado_map = {g.id: g.nombre for g in grados_r.scalars().all()}

    ies_r = await db.execute(
        select(InstitucionEducativa).where(InstitucionEducativa.id.in_(ie_ids_set))
    )
    ies = ies_r.scalars().all()
    ie_map = {ie.id: ie for ie in ies}

    ugel_ids = {ie.ugel_id for ie in ies if ie.ugel_id}
    ugel_map: dict = {}
    if ugel_ids:
        ug_r = await db.execute(select(Ugel).where(Ugel.id.in_(ugel_ids)))
        ugel_map = {u.id: u.nombre for u in ug_r.scalars().all()}

    # Un docente puede tener asignaciones en varias IEs/UGELs.
    docente_ies: dict = {}
    docente_ugeles: dict = {}
    for ie_id, _grado_id, _seccion, _anio, docente_id in filas:
        if not docente_id:
            continue
        docente_ies.setdefault(docente_id, set()).add(ie_id)
        ie_f = ie_map.get(ie_id)
        if ie_f and ie_f.ugel_id:
            docente_ugeles.setdefault(docente_id, set()).add(ie_f.ugel_id)

    docentes_r = await db.execute(select(Usuario).where(Usuario.id.in_(docente_ids)))
    docente_map = {}
    docentes_out: dict = {}
    docentes_roles = {'docente', 'auxiliar', 'director'}
    for u in docentes_r.scalars().all():
        # El selector es de docentes/responsables, no de administradores DRE/UGEL.
        if u.rol_codigo not in docentes_roles:
            continue
        nombre = (
            " ".join(filter(None, [u.apellidos, u.nombres])).strip()
            or u.dni
            or f"Usuario {u.id}"
        )
        docente_map[u.id] = nombre
        docentes_out[u.id] = {
            "id": u.id,
            "nombre": nombre,
            "institucion_educativa_ids": sorted(docente_ies.get(u.id, set())),
            "ugel_ids": sorted(docente_ugeles.get(u.id, set())),
        }

    ugeles_out: dict = {}
    instituciones_out: dict = {}
    aulas_map: dict = {}

    for ie_id, grado_id, seccion, anio, docente_id in filas:
        ie = ie_map.get(ie_id)
        ugel_id_c = ie.ugel_id if ie else None
        ugel_nombre = ugel_map.get(ugel_id_c) if ugel_id_c else None

        if ugel_id_c and ugel_id_c not in ugeles_out:
            ugeles_out[ugel_id_c] = {"id": ugel_id_c, "nombre": ugel_nombre}
        if ie and ie.id not in instituciones_out:
            instituciones_out[ie.id] = {
                "id": ie.id,
                "nombre": ie.nombre,
                "ugel_id": ie.ugel_id,
            }

        clave = f"{ie_id}-{grado_id}-{seccion or ''}-{anio or ''}"
        aula = aulas_map.get(clave)
        if aula is None:
            aula = {
                "key": clave,
                "grado_id": grado_id,
                "grado_nombre": grado_map.get(grado_id),
                "seccion": seccion,
                "año_escolar": anio,
                "institucion_educativa_id": ie_id,
                "institucion_nombre": ie.nombre if ie else None,
                "ugel_id": ugel_id_c,
                "ugel_nombre": ugel_nombre,
                "docente_ids": [],
                "docente_nombres": [],
            }
            aulas_map[clave] = aula
        if docente_id and docente_id in docente_map and docente_id not in aula["docente_ids"]:
            aula["docente_ids"].append(docente_id)
            aula["docente_nombres"].append(docente_map[docente_id])

    aulas = sorted(
        aulas_map.values(),
        key=lambda a: (
            a["institucion_nombre"] or "",
            a["grado_id"],
            a["seccion"] or "",
            a["año_escolar"] or 0,
        ),
    )

    return {
        "ugeles": sorted(ugeles_out.values(), key=lambda u: (u["nombre"] or "")),
        "instituciones": sorted(
            instituciones_out.values(), key=lambda i: (i["nombre"] or "", i["id"])
        ),
        "docentes": sorted(
            docentes_out.values(), key=lambda d: (d["nombre"] or "", d["id"])
        ),
        "aulas": aulas,
    }


@router.get("/examenes/asignaciones/reporte-estudiantes")
async def reporte_estudiantes(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_modulo("asignaciones")),
    ugel_id: Optional[int] = None,
    institucion_educativa_id: Optional[int] = None,
    docente_id: Optional[int] = None,
    grado_id: Optional[int] = None,
    seccion: Optional[str] = None,
    año_escolar: Optional[int] = None,
    asignacion_id: Optional[int] = None,
):
    """Reporte plano de estudiantes evaluados (último intento completado por asignación).

    Devuelve una fila por estudiante y asignación con los datos del estudiante,
    su IE/UGEL, el docente responsable, el examen y el resultado (nota vigesimal,
    nivel CNEB, aciertos y fechas). Respeta el scope del rol y acepta los mismos
    filtros jerárquicos de la clasificación, que solo pueden acotar el acceso.
    """
    from app.models.db_models import InstitucionEducativa, Ugel

    rol = RolCodigo(current_user.rol_codigo)
    user_ie_id = current_user.institucion_educativa_id
    user_ugel_id = current_user.ugel_id
    DRE_ROLES = {RolCodigo.ESPECIALISTA_DRE_COMUNICACION, RolCodigo.ESPECIALISTA_DRE_MATEMATICA}
    GESTORES_IE = {RolCodigo.DIRECTOR, RolCodigo.AUXILIAR}

    condiciones = []
    if rol in DRE_ROLES:
        pass  # ve toda la región
    elif rol == RolCodigo.RESPONSABLE_UGEL and user_ugel_id:
        ie_ids_r = await db.execute(
            select(InstitucionEducativa.id).where(InstitucionEducativa.ugel_id == user_ugel_id)
        )
        condiciones.append(
            AsignacionExamen.institucion_educativa_id.in_([r[0] for r in ie_ids_r.all()])
        )
    elif rol in GESTORES_IE and user_ie_id:
        condiciones.append(AsignacionExamen.institucion_educativa_id == user_ie_id)
    else:
        condiciones.append(AsignacionExamen.asignado_por_id == current_user.id)

    # Filtros jerárquicos opcionales: se suman (AND) al scope del rol.
    if ugel_id is not None:
        ie_ids_r = await db.execute(
            select(InstitucionEducativa.id).where(InstitucionEducativa.ugel_id == ugel_id)
        )
        condiciones.append(
            AsignacionExamen.institucion_educativa_id.in_([r[0] for r in ie_ids_r.all()])
        )
    if institucion_educativa_id is not None:
        condiciones.append(AsignacionExamen.institucion_educativa_id == institucion_educativa_id)
    if docente_id is not None:
        condiciones.append(AsignacionExamen.asignado_por_id == docente_id)
    if grado_id is not None:
        condiciones.append(AsignacionExamen.grado_id == grado_id)
    if seccion is not None:
        condiciones.append(AsignacionExamen.seccion == seccion)
    if año_escolar is not None:
        condiciones.append(AsignacionExamen.año_escolar == año_escolar)
    if asignacion_id is not None:
        condiciones.append(AsignacionExamen.id == asignacion_id)

    asig_q = select(AsignacionExamen)
    if condiciones:
        asig_q = asig_q.where(*condiciones)
    asignaciones = (
        await db.execute(asig_q.order_by(AsignacionExamen.fecha_creacion.desc()))
    ).scalars().all()
    if not asignaciones:
        return []

    asig_map = {a.id: a for a in asignaciones}
    asig_ids = list(asig_map)

    # Solo intentos completados; el primero por (asignación, estudiante) es el más reciente.
    intentos_rows = (
        await db.execute(
            select(
                IntentoExamen.asignacion_id,
                IntentoExamen.estudiante_id,
                IntentoExamen.numero_intento,
                IntentoExamen.estado,
                IntentoExamen.puntaje_total,
                IntentoExamen.preguntas_correctas,
                IntentoExamen.preguntas_total,
                IntentoExamen.nota_vigesimal,
                IntentoExamen.nivel_logro,
                IntentoExamen.nivel_cneb,
                IntentoExamen.fecha_inicio,
                IntentoExamen.fecha_fin,
                Estudiante.nombres,
                Estudiante.apellidos,
                Estudiante.codigo_estudiante,
                Estudiante.dni,
                Estudiante.institucion_educativa_id,
            )
            .join(Estudiante, Estudiante.id == IntentoExamen.estudiante_id)
            .where(
                IntentoExamen.asignacion_id.in_(asig_ids),
                IntentoExamen.estado == "completado",
            )
            .order_by(
                IntentoExamen.asignacion_id,
                IntentoExamen.estudiante_id,
                IntentoExamen.numero_intento.desc(),
            )
        )
    ).all()

    ultimos: dict = {}
    for row in intentos_rows:
        clave = (row.asignacion_id, row.estudiante_id)
        if clave not in ultimos:
            ultimos[clave] = row
    if not ultimos:
        return []

    estudiante_ids = {row.estudiante_id for row in ultimos.values()}

    # Códigos de clase: resuelven grado/IE en asignaciones antiguas sin esos campos.
    codigo_clase_ids = {a.codigo_clase_id for a in asignaciones if a.codigo_clase_id}
    cc_info: dict = {}
    if codigo_clase_ids:
        cc_rows = (
            await db.execute(
                select(
                    CodigoClase.id,
                    CodigoClase.grado_id,
                    CodigoClase.institucion_educativa_id,
                ).where(CodigoClase.id.in_(codigo_clase_ids))
            )
        ).all()
        cc_info = {
            r[0]: {"grado_id": r[1], "ie_id": r[2]}
            for r in cc_rows
        }

    grado_ids = {a.grado_id for a in asignaciones if a.grado_id}
    grado_ids |= {v["grado_id"] for v in cc_info.values() if v["grado_id"]}
    grados_r = await db.execute(select(Grado).where(Grado.id.in_(grado_ids)))
    grado_map = {g.id: g.nombre for g in grados_r.scalars().all()}

    ie_ids = {a.institucion_educativa_id for a in asignaciones if a.institucion_educativa_id}
    ie_ids |= {v["ie_id"] for v in cc_info.values() if v["ie_id"]}
    ie_ids |= {
        row.institucion_educativa_id
        for row in ultimos.values()
        if row.institucion_educativa_id
    }
    ies_r = await db.execute(
        select(InstitucionEducativa).where(InstitucionEducativa.id.in_(ie_ids))
    )
    ies = ies_r.scalars().all()
    ie_map = {ie.id: ie for ie in ies}
    ugel_ids = {ie.ugel_id for ie in ies if ie.ugel_id}
    ugel_map: dict = {}
    if ugel_ids:
        ug_r = await db.execute(select(Ugel).where(Ugel.id.in_(ugel_ids)))
        ugel_map = {u.id: u.nombre for u in ug_r.scalars().all()}

    docente_ids = {a.asignado_por_id for a in asignaciones if a.asignado_por_id}
    docentes_r = await db.execute(select(Usuario).where(Usuario.id.in_(docente_ids)))
    docente_map = {}
    for u in docentes_r.scalars().all():
        docente_map[u.id] = (
            " ".join(filter(None, [u.apellidos, u.nombres])).strip()
            or u.dni
            or f"Usuario {u.id}"
        )

    # Títulos de los exámenes, separados por área.
    lectura_ids = {a.examen_id for a in asignaciones if a.tipo_examen == "lectura"}
    matematica_ids = {a.examen_id for a in asignaciones if a.tipo_examen == "matematica"}
    titulos: dict = {}
    if lectura_ids:
        rows = (
            await db.execute(
                select(ExamenLectura.id, ExamenLectura.titulo).where(
                    ExamenLectura.id.in_(lectura_ids)
                )
            )
        ).all()
        titulos.update({("lectura", r[0]): r[1] for r in rows})
    if matematica_ids:
        rows = (
            await db.execute(
                select(ExamenMatematica.id, ExamenMatematica.titulo).where(
                    ExamenMatematica.id.in_(matematica_ids)
                )
            )
        ).all()
        titulos.update({("matematica", r[0]): r[1] for r in rows})

    # Matrículas de los estudiantes; se elige la del año de la asignación.
    matriculas_rows = (
        await db.execute(
            select(
                Matricula.estudiante_id,
                Matricula.año_escolar,
                Matricula.grado_id,
                Matricula.seccion,
            )
            .where(Matricula.estudiante_id.in_(estudiante_ids))
            .order_by(Matricula.estudiante_id, Matricula.año_escolar.desc())
        )
    ).all()
    matriculas_por_estudiante: dict = {}
    for est_id, anio, mat_grado_id, mat_seccion in matriculas_rows:
        matriculas_por_estudiante.setdefault(est_id, []).append(
            (anio, mat_grado_id, mat_seccion)
        )

    out = []
    for (asig_id, _est_id), row in ultimos.items():
        asignacion = asig_map[asig_id]
        cc = cc_info.get(asignacion.codigo_clase_id) or {}
        ie_id = (
            asignacion.institucion_educativa_id
            or cc.get("ie_id")
            or row.institucion_educativa_id
        )
        ie = ie_map.get(ie_id)
        grado_id_asig = asignacion.grado_id or cc.get("grado_id")

        matriculas = matriculas_por_estudiante.get(row.estudiante_id, [])
        matricula = next(
            (m for m in matriculas if m[0] == asignacion.año_escolar),
            matriculas[0] if matriculas else None,
        )
        mat_anio, mat_grado_id, mat_seccion = matricula if matricula else (None, None, None)
        grado_id_final = mat_grado_id or grado_id_asig
        seccion_final = mat_seccion or asignacion.seccion
        anio_final = asignacion.año_escolar or mat_anio

        nota = row.nota_vigesimal
        cneb = nota_a_nivel(nota) if nota is not None else row.nivel_cneb
        nivel = _CNEB_A_4NIVELES.get(cneb) if cneb else None
        if nivel is None and row.nivel_logro in _NIVELES_4:
            nivel = row.nivel_logro

        out.append({
            "asignacion_id": asig_id,
            "ugel": ugel_map.get(ie.ugel_id) if ie else None,
            "institucion_educativa": ie.nombre if ie else None,
            "codigo_modular": ie.codigo_modular if ie else None,
            "docente": docente_map.get(asignacion.asignado_por_id),
            "area": _AREA_REPORTE.get(asignacion.tipo_examen, asignacion.tipo_examen),
            "examen": titulos.get((asignacion.tipo_examen, asignacion.examen_id))
            or f"Asignación #{asig_id}",
            "grado": grado_map.get(grado_id_final) or grado_map.get(grado_id_asig),
            "seccion": seccion_final,
            "año_escolar": anio_final,
            "codigo_estudiante": row.codigo_estudiante,
            "dni": row.dni,
            "estudiante": (
                " ".join(filter(None, [row.nombres, row.apellidos])).strip()
                or row.codigo_estudiante
                or row.dni
                or "Estudiante"
            ),
            "estado": row.estado,
            "numero_intento": row.numero_intento,
            "nota_vigesimal": round(nota, 2) if nota is not None else None,
            "nivel_logro": nivel,
            "nivel_logro_label": _NIVEL_4_LABEL.get(nivel) if nivel else None,
            "nivel_cneb": cneb,
            "puntaje_total": (
                round(row.puntaje_total, 2) if row.puntaje_total is not None else None
            ),
            "correctas": row.preguntas_correctas,
            "total_preguntas": row.preguntas_total,
            "fecha_inicio": _iso_peru(row.fecha_inicio),
            "fecha_fin": _iso_peru(row.fecha_fin),
            "fecha_asignacion": _iso_peru(asignacion.fecha_creacion),
        })

    out.sort(
        key=lambda r: (
            (r["ugel"] or "").casefold(),
            (r["institucion_educativa"] or "").casefold(),
            (r["grado"] or "").casefold(),
            (r["seccion"] or "").casefold(),
            (r["estudiante"] or "").casefold(),
            (r["examen"] or "").casefold(),
        )
    )
    return out


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


@router.patch("/examenes/asignaciones/{asig_id}/toggle-active")
async def toggle_asignacion_activa(
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
        raise HTTPException(403, "No tienes acceso a esta asignación")

    asig.is_active = not asig.is_active
    await db.flush()
    return {"id": asig.id, "is_active": asig.is_active}


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
