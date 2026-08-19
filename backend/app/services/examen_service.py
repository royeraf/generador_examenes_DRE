"""
Servicio de lógica de negocio para exámenes estudiantiles.
Centraliza calificación, mezcla, retroalimentación y construcción de revisiones.
"""
import json
import random
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from app.models.db_models import (
    AsignacionExamen, IntentoExamen, ProgresoEstudiante,
    ExamenLectura, ExamenMatematica,
    PreguntaExamen, RespuestaIntento,
)
from app.models.usuario import Usuario
from app.services.ai_factory import ai_factory


class ExamenService:

    # ── Conversión de puntaje ──────────────────────────────────────────────────

    @staticmethod
    def puntaje_a_nivel(puntaje: float) -> str:
        if puntaje < 20:
            return "pre_inicio"
        if puntaje < 40:
            return "inicio"
        if puntaje < 60:
            return "proceso"
        if puntaje < 80:
            return "satisfactorio"
        return "destacado"

    # ── Calificación ──────────────────────────────────────────────────────────

    @staticmethod
    def calificar(respuestas_estudiante: list[dict], tabla_respuestas: list[dict]) -> dict:
        """
        Califica respuestas del estudiante vs tabla de respuestas del examen.
        respuestas_estudiante: [{"pregunta_numero": 1, "respuesta": "A"}, ...]
        tabla_respuestas:      [{"pregunta": 1, "respuesta_correcta": "A", ...}, ...]
        """
        clave_map = {int(r["pregunta"]): r.get("respuesta_correcta", "").upper() for r in tabla_respuestas}
        student_map = {int(r["pregunta_numero"]): r["respuesta"].upper() for r in respuestas_estudiante}
        correctas = sum(1 for num, clave in clave_map.items() if student_map.get(num) == clave)
        total = len(tabla_respuestas)
        puntaje = (correctas / total * 100) if total > 0 else 0
        return {
            "correctas": correctas,
            "total": total,
            "puntaje": round(puntaje, 2),
            "nivel_logro": ExamenService.puntaje_a_nivel(puntaje),
        }

    # ── Validación de rango horario ────────────────────────────────────────────

    @staticmethod
    def validar_rango_horario(fecha_inicio: Optional[datetime], fecha_fin: Optional[datetime]) -> None:
        if not fecha_inicio and not fecha_fin:
            return
        if not fecha_inicio or not fecha_fin:
            raise HTTPException(400, "Debes definir la fecha con hora de inicio y hora de fin")
        TZ_PERU = timezone(timedelta(hours=-5))
        inicio_peru = fecha_inicio.astimezone(TZ_PERU)
        fin_peru = fecha_fin.astimezone(TZ_PERU)
        if inicio_peru.date() != fin_peru.date():
            raise HTTPException(400, "El rango horario debe estar dentro de un solo día")
        if fecha_fin <= fecha_inicio:
            raise HTTPException(400, "La hora fin debe ser mayor que la hora inicio")

    # ── Preparación y mezcla de preguntas ─────────────────────────────────────

    @staticmethod
    def preparar_preguntas(preguntas: list) -> list[dict]:
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

    @staticmethod
    def mezclar_examen(
        preguntas: list[dict],
        *,
        mezclar_preguntas: bool,
        mezclar_alternativas: bool,
        seed_base: str,
    ) -> list[dict]:
        resultado = []
        for pregunta in preguntas:
            pregunta_out = {**pregunta, "opciones": [dict(op) for op in pregunta.get("opciones", [])]}
            if mezclar_alternativas and pregunta_out["opciones"]:
                rng = random.Random(f"{seed_base}:opciones:{pregunta_out['numero']}")
                rng.shuffle(pregunta_out["opciones"])
                for idx, opcion in enumerate(pregunta_out["opciones"]):
                    opcion["letra"] = "ABCDE"[idx]
            resultado.append(pregunta_out)
        if mezclar_preguntas and resultado:
            random.Random(f"{seed_base}:preguntas").shuffle(resultado)
        return resultado

    # ── Retroalimentación IA ──────────────────────────────────────────────────

    async def generar_retroalimentacion(
        self,
        preguntas_data: list[dict],
        lectura_texto: str,
        nombre_estudiante: str,
    ) -> dict[int, str]:
        ai_service = ai_factory.get_service("gemini")
        if not ai_service.is_configured():
            return {}

        opciones_label = {0: "A", 1: "B", 2: "C", 3: "D"}
        preguntas_texto = ""
        for p in preguntas_data:
            opciones_str = "\n".join([
                f"  {opciones_label.get(i, chr(65 + i))}) {op}"
                for i, op in enumerate([p["opcion_a"], p["opcion_b"], p["opcion_c"], p["opcion_d"]])
            ])
            estado = "CORRECTA" if p["es_correcta"] else "INCORRECTA"
            preguntas_texto += (
                f"\nPregunta {p['numero']}: {p['enunciado']}\n"
                f"{opciones_str}\n"
                f"  Respuesta correcta: {p['respuesta_correcta']}\n"
                f"  Respuesta del estudiante: {p['respuesta_dada']} ({estado})\n"
            )

        lectura_seccion = ""
        if lectura_texto:
            lectura_seccion = (
                f'\nTEXTO DE LA LECTURA (para contextualizar tu retroalimentación):\n"""\n'
                f"{lectura_texto[:3000]}\n"
                '"""\n'
            )

        prompt = (
            f"Eres un docente peruano amable y motivador que revisa las respuestas de un examen de comprensión lectora.\n"
            f"El estudiante se llama {nombre_estudiante}.\n"
            f"{lectura_seccion}\n"
            f"PREGUNTAS, RESPUESTAS CORRECTAS Y RESPUESTAS DEL ESTUDIANTE:\n{preguntas_texto}\n\n"
            "Para cada pregunta, escribe una retroalimentación breve (2-4 oraciones) en español que:\n"
            "- Si la respuesta es CORRECTA: felicita al estudiante y explica brevemente por qué esa opción es la correcta.\n"
            "- Si la respuesta es INCORRECTA: explica amablemente por qué la opción que eligió no es la correcta y por qué la respuesta correcta sí lo es. Usa un tono motivador.\n"
            "- Siempre que sea posible, haz referencia al texto de la lectura.\n"
            "- Usa un lenguaje claro y adecuado para el nivel escolar.\n\n"
            'Responde ÚNICAMENTE con un JSON válido con esta estructura:\n'
            '{\n  "retroalimentacion": [\n'
            '    {"numero": 1, "texto": "Explicación breve y motivadora..."},\n'
            '    {"numero": 2, "texto": "..."}\n'
            '  ]\n}'
        )

        try:
            response_text = await ai_service.generate_content(prompt)
            response_text = ai_service.clean_json_response(response_text)
            data = json.loads(response_text)
            return {int(item["numero"]): item["texto"] for item in data.get("retroalimentacion", [])}
        except Exception as e:
            print(f"Error generando retroalimentación IA: {e}")
            return {}

    # ── Calificación persistida ────────────────────────────────────────────────

    async def calificar_y_persistir(
        self,
        db: AsyncSession,
        intento: IntentoExamen,
        asig: AsignacionExamen,
        respuestas_enviadas: list,
    ) -> dict:
        """
        Califica el intento, persiste RespuestaIntento por pregunta,
        actualiza IntentoExamen y hace upsert de ProgresoEstudiante.
        """
        filtro = (
            PreguntaExamen.examen_lectura_id == asig.examen_id
            if asig.tipo_examen == "lectura"
            else PreguntaExamen.examen_matematica_id == asig.examen_id
        )
        preguntas_r = await db.execute(select(PreguntaExamen).where(filtro))
        preguntas_map = {p.numero: p for p in preguntas_r.scalars().all()}

        correctas = 0
        for r in respuestas_enviadas:
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
        nivel_logro = self.puntaje_a_nivel(puntaje)

        # estado/fecha_fin ya fueron reclamados atómicamente por el caller (ver
        # finalizar_intento) antes de llegar aquí: a partir de ese punto este intento
        # es exclusivo de esta llamada, así que estos campos son un UPDATE normal
        # sin riesgo de carrera (nadie más puede estar calificando este mismo intento).
        intento.puntaje_total = puntaje
        intento.preguntas_correctas = correctas
        intento.preguntas_total = total
        intento.nivel_logro = nivel_logro
        await db.flush()

        area = "comunicacion" if asig.tipo_examen == "lectura" else "matematica"
        from app.services.matricula_service import get_matricula_activa
        matricula = await get_matricula_activa(db, intento.estudiante_id)
        if not matricula:
            # Sin matrícula no se puede registrar progreso
            return {
                "puntaje_total": puntaje,
                "preguntas_correctas": correctas,
                "preguntas_total": total,
                "nivel_logro": nivel_logro,
            }
        await self._upsert_progreso(db, matricula.id, area, puntaje, nivel_logro)

        return {
            "puntaje_total": puntaje,
            "preguntas_correctas": correctas,
            "preguntas_total": total,
            "nivel_logro": nivel_logro,
        }

    @staticmethod
    async def _upsert_progreso(db: AsyncSession, matricula_id: int, area: str, puntaje: float, nivel_logro: str) -> None:
        """Suma un examen más al progreso del área, a prueba de dos finalizaciones
        concurrentes (de exámenes distintos) sobre la misma fila.

        Producción corre en tablas MyISAM (sin FOR UPDATE ni rollback real), así que
        esto NO usa lectura-en-Python-luego-escritura ni locks: primero intenta un
        UPDATE de una sola sentencia con la fórmula del promedio calculada en SQL
        (atómico en el servidor sin importar el motor), y solo si no existía la fila
        (rowcount == 0) intenta el INSERT inicial. Si ese INSERT choca con otro
        concurrente (UNIQUE KEY uq_progreso_matricula_area), el conflicto se aísla en
        un SAVEPOINT (begin_nested) para no arrastrar en el rollback el resto de la
        transacción (RespuestaIntento ya insertadas, IntentoExamen ya actualizado) —
        y se reintenta el UPDATE, que esta vez sí encuentra la fila.
        """
        ahora = datetime.now(timezone.utc)
        upd = await db.execute(
            update(ProgresoEstudiante)
            .where(ProgresoEstudiante.matricula_id == matricula_id, ProgresoEstudiante.area == area)
            .values(
                total_examenes_completados=ProgresoEstudiante.total_examenes_completados + 1,
                puntaje_promedio=(
                    (ProgresoEstudiante.puntaje_promedio * ProgresoEstudiante.total_examenes_completados + puntaje)
                    / (ProgresoEstudiante.total_examenes_completados + 1)
                ),
                nivel_logro_actual=nivel_logro,
                ultima_actividad=ahora,
            )
        )
        if upd.rowcount:
            return

        try:
            async with db.begin_nested():
                db.add(ProgresoEstudiante(
                    matricula_id=matricula_id,
                    area=area,
                    total_examenes_completados=1,
                    puntaje_promedio=puntaje,
                    nivel_logro_actual=nivel_logro,
                    ultima_actividad=ahora,
                ))
                await db.flush()
        except IntegrityError:
            # Otra finalización concurrente ganó la creación de la fila; sumar ahí.
            await db.execute(
                update(ProgresoEstudiante)
                .where(ProgresoEstudiante.matricula_id == matricula_id, ProgresoEstudiante.area == area)
                .values(
                    total_examenes_completados=ProgresoEstudiante.total_examenes_completados + 1,
                    puntaje_promedio=(
                        (ProgresoEstudiante.puntaje_promedio * ProgresoEstudiante.total_examenes_completados + puntaje)
                        / (ProgresoEstudiante.total_examenes_completados + 1)
                    ),
                    nivel_logro_actual=nivel_logro,
                    ultima_actividad=ahora,
                )
            )

    # ── Revisión de intento ────────────────────────────────────────────────────

    async def construir_revision(
        self,
        db: AsyncSession,
        intento_id: int,
        current_user: Usuario,
    ) -> dict:
        """Construye la revisión completa de un intento con retroalimentación IA."""
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
        lecturas_out = []
        if asig.tipo_examen == "lectura":
            ex_r = await db.execute(select(ExamenLectura).where(ExamenLectura.id == asig.examen_id))
            examen = ex_r.scalars().first()
            if examen:
                titulo_examen = examen.titulo or ""
                lectura_texto = (
                    "\n\n".join(t.get("texto", "") for t in examen.lecturas)
                    if examen.lecturas
                    else (examen.lectura or "")
                )
                if examen.lecturas:
                    lecturas_out = [{"titulo": t.get("titulo", ""), "texto": t.get("texto", "")} for t in examen.lecturas]
                elif examen.lectura:
                    lecturas_out = [{"titulo": "Texto Principal", "texto": examen.lectura}]
        elif asig.tipo_examen == "matematica":
            ex_r = await db.execute(select(ExamenMatematica).where(ExamenMatematica.id == asig.examen_id))
            examen = ex_r.scalars().first()
            if examen:
                titulo_examen = examen.titulo or ""
                lectura_texto = examen.situacion_problematica or ""
                if examen.situacion_problematica:
                    lecturas_out = [{"titulo": "Situación Problemática", "texto": examen.situacion_problematica}]

        resp_r = await db.execute(select(RespuestaIntento).where(RespuestaIntento.intento_id == intento_id))
        respuestas = resp_r.scalars().all()

        preg_ids = [r.pregunta_id for r in respuestas]
        preg_r = await db.execute(select(PreguntaExamen).where(PreguntaExamen.id.in_(preg_ids)))
        preguntas_map = {p.id: p for p in preg_r.scalars().all()}

        # Poblar retroalimentacion_ia desde los campos pre-generados en PreguntaExamen.
        # Si la pregunta no tiene retroalimentación pre-generada (exámenes antiguos),
        # se genera en tiempo real con una sola llamada a la IA.
        respuestas_sin_retro = [r for r in respuestas if not r.retroalimentacion_ia]
        if respuestas_sin_retro:
            preguntas_con_retro_previa = [
                r for r in respuestas_sin_retro
                if (p := preguntas_map.get(r.pregunta_id))
                and (p.retroalimentacion_correcta or p.retroalimentacion_incorrecta)
            ]
            preguntas_sin_retro_previa = [
                r for r in respuestas_sin_retro
                if not (p := preguntas_map.get(r.pregunta_id))
                or not (p.retroalimentacion_correcta or p.retroalimentacion_incorrecta)
            ]

            # Usar retroalimentación pre-generada cuando esté disponible
            for r in preguntas_con_retro_previa:
                p = preguntas_map.get(r.pregunta_id)
                r.retroalimentacion_ia = (
                    p.retroalimentacion_correcta if r.es_correcta else p.retroalimentacion_incorrecta
                ) or ""

            # Fallback: llamar a la IA solo para preguntas de exámenes antiguos sin retroalimentación previa
            if preguntas_sin_retro_previa:
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
                    for r in preguntas_sin_retro_previa
                    if (p := preguntas_map.get(r.pregunta_id))
                ], key=lambda x: x["numero"])

                nombre = f"{current_user.nombres or ''} {current_user.apellidos or ''}".strip() or "estudiante"
                retro_map = await self.generar_retroalimentacion(preguntas_para_ia, lectura_texto, nombre)

                for r in preguntas_sin_retro_previa:
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
            "lecturas": lecturas_out,
        }


examen_service = ExamenService()
