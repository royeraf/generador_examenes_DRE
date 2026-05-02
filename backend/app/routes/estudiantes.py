"""
Rutas del portal estudiantil: exámenes, intentos y progreso.
"""
import json
import random
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
    PreguntaExamen, RespuestaIntento, Rol,
)
from app.models.usuario import Usuario
from app.models.enums import RolCodigo
from app.api.dependencies import get_estudiante_user, get_current_active_user, require_role, require_modulo
from app.services.ai_factory import ai_factory

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


def _validar_rango_horario(fecha_inicio: Optional[datetime], fecha_fin: Optional[datetime]) -> None:
    if not fecha_inicio and not fecha_fin:
        return
    if not fecha_inicio or not fecha_fin:
        raise HTTPException(400, "Debes definir la fecha con hora de inicio y hora de fin")
    if fecha_inicio.date() != fecha_fin.date():
        raise HTTPException(400, "El rango horario debe estar dentro de un solo día")
    if fecha_fin <= fecha_inicio:
        raise HTTPException(400, "La hora fin debe ser mayor que la hora inicio")


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

    # SQLite devuelve datetimes naive (sin timezone); usar utcnow() para comparar
    ahora = datetime.utcnow()
    def _naive(dt):
        if dt is None:
            return None
        return dt.replace(tzinfo=None) if dt.tzinfo else dt

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
            "preguntas": _mezclar_examen(
                _preparar_preguntas_db(preguntas),
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
            "preguntas": _mezclar_examen(
                _preparar_preguntas_db(preguntas),
                mezclar_preguntas=asig.mezclar_preguntas,
                mezclar_alternativas=asig.mezclar_alternativas,
                seed_base=f"{asig.id}:{intento.id}:matematica",
            ),
            "duracion_minutos": asig.duracion_minutos,
            "intento_id": intento.id,
        }
    else:
        raise HTTPException(400, "Tipo de examen no soportado")


def _preparar_preguntas_db(preguntas: list) -> list:
    """Convierte filas de PreguntaExamen al formato que espera el cliente."""
    return [
        {
            "numero": p.numero,
            "enunciado": p.enunciado,
            "opciones": [
                {"letra": "A", "valor": "A", "texto": p.opcion_a},
                {"letra": "B", "valor": "B", "texto": p.opcion_b},
                {"letra": "C", "valor": "C", "texto": p.opcion_c},
                {"letra": "D", "valor": "D", "texto": p.opcion_d},
            ],
            "nivel": p.nivel or "",
            "desempeno_codigo": p.desempeno_codigo or "",
        }
        for p in preguntas
    ]


def _mezclar_examen(preguntas: list[dict], *, mezclar_preguntas: bool, mezclar_alternativas: bool, seed_base: str) -> list[dict]:
    preguntas_preparadas = []
    for pregunta in preguntas:
        pregunta_out = {
            **pregunta,
            "opciones": [dict(opcion) for opcion in pregunta.get("opciones", [])],
        }

        if mezclar_alternativas and pregunta_out["opciones"]:
            option_rng = random.Random(f"{seed_base}:opciones:{pregunta_out['numero']}")
            option_rng.shuffle(pregunta_out["opciones"])
            letras_visibles = ["A", "B", "C", "D", "E"]
            for idx, opcion in enumerate(pregunta_out["opciones"]):
                opcion["letra"] = letras_visibles[idx]

        preguntas_preparadas.append(pregunta_out)

    if mezclar_preguntas and preguntas_preparadas:
        question_rng = random.Random(f"{seed_base}:preguntas")
        question_rng.shuffle(preguntas_preparadas)

    return preguntas_preparadas


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

    # Obtener asignación y preguntas normalizadas
    asig_r = await db.execute(select(AsignacionExamen).where(AsignacionExamen.id == intento.asignacion_id))
    asig = asig_r.scalars().first()

    filtro_pregunta = (
        PreguntaExamen.examen_lectura_id == asig.examen_id
        if asig.tipo_examen == "lectura"
        else PreguntaExamen.examen_matematica_id == asig.examen_id
    )
    preguntas_r = await db.execute(select(PreguntaExamen).where(filtro_pregunta))
    preguntas_map = {p.numero: p for p in preguntas_r.scalars().all()}

    # Calificar y crear RespuestaIntento por cada respuesta enviada
    correctas = 0
    for r in data.respuestas:
        pregunta = preguntas_map.get(r.pregunta_numero)
        if not pregunta:
            continue
        es_correcta = r.respuesta.upper() == pregunta.respuesta_correcta.upper()
        if es_correcta:
            correctas += 1
        db.add(RespuestaIntento(
            intento_id=intento.id,
            pregunta_id=pregunta.id,
            respuesta_dada=r.respuesta.upper(),
            es_correcta=es_correcta,
        ))

    total = len(preguntas_map)
    puntaje = round((correctas / total * 100) if total > 0 else 0, 2)
    nivel_logro = _puntaje_a_nivel(puntaje)

    # Actualizar intento
    intento.estado = "completado"
    intento.fecha_fin = datetime.now(timezone.utc)
    intento.puntaje_total = puntaje
    intento.preguntas_correctas = correctas
    intento.preguntas_total = total
    intento.nivel_logro = nivel_logro

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
        progreso.puntaje_promedio = (prom + puntaje) / (n + 1)
        progreso.nivel_logro_actual = nivel_logro
        progreso.ultima_actividad = datetime.now(timezone.utc)
    else:
        progreso = ProgresoEstudiante(
            estudiante_id=current_user.id,
            area=area,
            total_examenes_completados=1,
            puntaje_promedio=puntaje,
            nivel_logro_actual=nivel_logro,
            ultima_actividad=datetime.now(timezone.utc),
        )
        db.add(progreso)

    await db.flush()

    return {
        "puntaje_total": puntaje,
        "preguntas_correctas": correctas,
        "preguntas_total": total,
        "nivel_logro": nivel_logro,
    }


# ─── Revisión con retroalimentación IA ───────────────────────────────────────

async def _generar_retroalimentacion(
    preguntas_data: list[dict],
    lectura_texto: str,
    nombre_estudiante: str,
) -> dict[int, str]:
    """
    Llama a la IA para generar retroalimentación por pregunta.
    Retorna un dict {numero_pregunta: texto_retroalimentacion}.
    """
    ai_service = ai_factory.get_service("gemini")
    if not ai_service.is_configured():
        return {}

    opciones_label = {0: "A", 1: "B", 2: "C", 3: "D"}
    preguntas_texto = ""
    for p in preguntas_data:
        opciones_str = "\n".join([
            f"  {opciones_label.get(i, chr(65+i))}) {op}"
            for i, op in enumerate([p["opcion_a"], p["opcion_b"], p["opcion_c"], p["opcion_d"]])
        ])
        estado = "CORRECTA" if p["es_correcta"] else "INCORRECTA"
        preguntas_texto += f"""
Pregunta {p["numero"]}: {p["enunciado"]}
{opciones_str}
  Respuesta correcta: {p["respuesta_correcta"]}
  Respuesta del estudiante: {p["respuesta_dada"]} ({estado})
"""

    lectura_seccion = ""
    if lectura_texto:
        lectura_seccion = f"""
TEXTO DE LA LECTURA (para contextualizar tu retroalimentación):
\"\"\"
{lectura_texto[:3000]}
\"\"\"
"""

    prompt = f"""Eres un docente peruano amable y motivador que revisa las respuestas de un examen de comprensión lectora.
El estudiante se llama {nombre_estudiante}.
{lectura_seccion}
PREGUNTAS, RESPUESTAS CORRECTAS Y RESPUESTAS DEL ESTUDIANTE:
{preguntas_texto}

Para cada pregunta, escribe una retroalimentación breve (2-4 oraciones) en español que:
- Si la respuesta es CORRECTA: felicita al estudiante y explica brevemente por qué esa opción es la correcta.
- Si la respuesta es INCORRECTA: explica amablemente por qué la opción que eligió no es la correcta y por qué la respuesta correcta sí lo es. Usa un tono motivador.
- Siempre que sea posible, haz referencia al texto de la lectura.
- Usa un lenguaje claro y adecuado para el nivel escolar.

Responde ÚNICAMENTE con un JSON válido con esta estructura:
{{
  "retroalimentacion": [
    {{"numero": 1, "texto": "Explicación breve y motivadora..."}},
    {{"numero": 2, "texto": "..."}}
  ]
}}
"""

    try:
        response_text = await ai_service.generate_content(prompt)
        response_text = ai_service.clean_json_response(response_text)
        data = json.loads(response_text)
        return {int(item["numero"]): item["texto"] for item in data.get("retroalimentacion", [])}
    except Exception as e:
        print(f"Error generando retroalimentación IA: {e}")
        return {}


async def _revision_data(intento_id: int, current_user: Usuario, db: AsyncSession) -> dict:
    """Lógica compartida para construir la revisión de un intento."""
    intento_r = await db.execute(select(IntentoExamen).where(IntentoExamen.id == intento_id))
    intento = intento_r.scalars().first()
    if not intento or intento.estudiante_id != current_user.id:
        raise HTTPException(404, "Intento no encontrado")
    if intento.estado != "completado":
        raise HTTPException(400, "El intento aún no está completado")

    asig_r = await db.execute(select(AsignacionExamen).where(AsignacionExamen.id == intento.asignacion_id))
    asig = asig_r.scalars().first()

    lectura_texto = ""
    titulo_examen = ""
    if asig.tipo_examen == "lectura":
        ex_r = await db.execute(select(ExamenLectura).where(ExamenLectura.id == asig.examen_id))
        examen = ex_r.scalars().first()
        if examen:
            titulo_examen = examen.titulo or ""
            lectura_texto = "\n\n".join(t.get("texto", "") for t in examen.lecturas) if examen.lecturas else (examen.lectura or "")
    elif asig.tipo_examen == "matematica":
        ex_r = await db.execute(select(ExamenMatematica).where(ExamenMatematica.id == asig.examen_id))
        examen = ex_r.scalars().first()
        if examen:
            titulo_examen = examen.titulo or ""
            lectura_texto = examen.situacion_problematica or ""

    resp_r = await db.execute(select(RespuestaIntento).where(RespuestaIntento.intento_id == intento_id))
    respuestas = resp_r.scalars().all()

    preg_ids = [r.pregunta_id for r in respuestas]
    preg_r = await db.execute(select(PreguntaExamen).where(PreguntaExamen.id.in_(preg_ids)))
    preguntas_map = {p.id: p for p in preg_r.scalars().all()}

    if not all(r.retroalimentacion_ia for r in respuestas):
        preguntas_para_ia = sorted([
            {
                "numero": p.numero,
                "enunciado": p.enunciado,
                "opcion_a": p.opcion_a,
                "opcion_b": p.opcion_b,
                "opcion_c": p.opcion_c,
                "opcion_d": p.opcion_d,
                "respuesta_correcta": p.respuesta_correcta,
                "respuesta_dada": r.respuesta_dada,
                "es_correcta": r.es_correcta,
            }
            for r in respuestas
            if (p := preguntas_map.get(r.pregunta_id))
        ], key=lambda x: x["numero"])

        nombre = f"{current_user.nombres or ''} {current_user.apellidos or ''}".strip() or "estudiante"
        retro_map = await _generar_retroalimentacion(preguntas_para_ia, lectura_texto, nombre)

        for r in respuestas:
            p = preguntas_map.get(r.pregunta_id)
            if p and p.numero in retro_map:
                r.retroalimentacion_ia = retro_map[p.numero]
        await db.flush()

    preguntas_out = sorted([
        {
            "numero": p.numero,
            "enunciado": p.enunciado,
            "opciones": [
                {"letra": "A", "texto": p.opcion_a},
                {"letra": "B", "texto": p.opcion_b},
                {"letra": "C", "texto": p.opcion_c},
                {"letra": "D", "texto": p.opcion_d},
            ],
            "respuesta_correcta": p.respuesta_correcta,
            "respuesta_dada": r.respuesta_dada,
            "es_correcta": r.es_correcta,
            "justificacion": p.justificacion or "",
            "retroalimentacion_ia": r.retroalimentacion_ia or "",
            "nivel": p.nivel or "",
        }
        for r in respuestas
        if (p := preguntas_map.get(r.pregunta_id))
    ], key=lambda x: x["numero"])

    return {
        "titulo": titulo_examen,
        "puntaje_total": intento.puntaje_total,
        "preguntas_correctas": intento.preguntas_correctas,
        "preguntas_total": intento.preguntas_total,
        "nivel_logro": intento.nivel_logro,
        "preguntas": preguntas_out,
    }


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
    return await _revision_data(ultimo.id, current_user, db)


@router.get("/estudiante/intentos/{intento_id}/revision")
async def revision_intento(
    intento_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_estudiante_user),
):
    """Revisión detallada de un intento específico con retroalimentación IA."""
    return await _revision_data(intento_id, current_user, db)


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
    _validar_rango_horario(data.fecha_inicio, data.fecha_fin)

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

    _validar_rango_horario(data.fecha_inicio, data.fecha_fin)

    asig.fecha_inicio = data.fecha_inicio
    asig.fecha_fin = data.fecha_fin
    asig.duracion_minutos = data.duracion_minutos
    asig.intentos_permitidos = data.intentos_permitidos
    asig.mezclar_preguntas = data.mezclar_preguntas
    asig.mezclar_alternativas = data.mezclar_alternativas
    asig.is_active = data.is_active

    await db.flush()
    return {"ok": True}
