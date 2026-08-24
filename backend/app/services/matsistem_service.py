"""
Servicio para gestionar evaluaciones de Matemática (MatSistem).
Genera situaciones problemáticas y preguntas siguiendo el modelo MINEDU.
"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.db_models import (
    Grado,
    CompetenciaMatematica,
    CapacidadMatematica,
    DesempenoMatematica,
    EstandarMatematica
)
from app.models.ai_schemas import RespuestaMat, RespuestaActividad
from app.core.config import get_settings
from app.services.ai_factory import ai_factory
from app.services.prompt_fragments import NOTACION_MATEMATICA

settings = get_settings()


# Descripciones de los 5 tipos de producto
TIPOS_PRODUCTO = {
    1: {
        "nombre": "Situación Integradora + Preguntas Abiertas",
        "descripcion": "Una situación problemática integradora seguida de preguntas abiertas (distribuidas entre las capacidades seleccionadas), con espacio para que el estudiante desarrolle su solución.",
        "formato_preguntas": "abiertas"
    },
    2: {
        "nombre": "Situación Integradora + Preguntas Cerradas (5 alternativas)",
        "descripcion": "Una situación problemática integradora seguida de preguntas de opción múltiple con 5 alternativas (A, B, C, D, E), distribuidas entre las capacidades seleccionadas.",
        "formato_preguntas": "cerradas_5"
    },
    3: {
        "nombre": "Preguntas Cerradas Independientes por Criterio",
        "descripcion": "Preguntas de opción múltiple independientes (sin situación integradora), distribuidas entre las capacidades/criterios seleccionados. Cada pregunta tiene su propio contexto.",
        "formato_preguntas": "cerradas_4_independientes"
    },
    4: {
        "nombre": "Preguntas Abiertas Independientes por Criterio",
        "descripcion": "Preguntas abiertas independientes, distribuidas entre las capacidades/criterios seleccionados. Cada pregunta tiene su propio contexto y permite desarrollo.",
        "formato_preguntas": "abiertas_independientes"
    },
    5: {
        "nombre": "Actividad de Aprendizaje Completa (INICIO/DESARROLLO/CIERRE)",
        "descripcion": "Una sesión de aprendizaje completa con tres momentos: INICIO (motivación/saberes previos), DESARROLLO (actividades principales por capacidad), CIERRE (metacognición/evaluación).",
        "formato_preguntas": "actividad_aprendizaje"
    }
}


class MatSistemService:
    """Servicio para generar evaluaciones de matemática."""

    def __init__(self):
        pass

    def _build_criterios_evaluacion(self, capacidades_desempenos: dict) -> str:
        """Construye los criterios de evaluación formales para el prompt."""
        criterios = ""
        for orden, data in capacidades_desempenos.items():
            criterios += (
                f"\n**Criterio {orden} - {data['nombre']}:**\n"
                f"  [Habilidad] + [Contenido] + [Condición] + [Finalidad] = Criterio de evaluación formal\n"
                f"  Desempeños base:\n"
            )
            for des in data['desempenos']:
                criterios += f"    • {des['descripcion']}\n"
        return criterios

    def _build_json_format_by_tipo(self, tipo_producto: int, grado_nombre: str, competencia_nombre: str) -> str:
        """Devuelve el esquema JSON esperado según el tipo de producto."""

        nota_repeticion = "" if tipo_producto == 5 else (
            "\nEl ejemplo de abajo muestra solo UN objeto dentro de \"preguntas\" a modo ilustrativo: "
            "debes repetir ese objeto (con \"numero\" incremental) hasta alcanzar el total exacto de preguntas indicado arriba.\n"
        )
        base = f"""
**FORMATO JSON OBLIGATORIO:**
Responde ÚNICAMENTE con un JSON válido sin comentarios ni texto adicional:
{nota_repeticion}"""

        if tipo_producto == 1:
            return base + f"""
{{
    "saludo": "Mensaje motivador al docente...",
    "examen": {{
        "titulo": "Título motivador",
        "grado": "{grado_nombre}",
        "competencia": "{competencia_nombre}",
        "instrucciones": "Lee la situación y responde desarrollando tu solución.",
        "situacion_problematica": "Texto narrativo completo de la situación integradora...",
        "criterios_evaluacion": [
            {{"criterio": 1, "capacidad": "Nombre capacidad", "descripcion": "Habilidad + Contenido + Condición + Finalidad"}}
        ],
        "preguntas": [
            {{
                "numero": 1,
                "enunciado": "¿Pregunta abierta vinculada a la situación?",
                "tipo": "abierta",
                "espacio_respuesta": "Desarrolla tu respuesta aquí:",
                "capacidad": "Nombre de la capacidad asociada",
                "desempeno_codigo": "Código del desempeño",
                "criterio_evaluacion": "Criterio: [Habilidad] + [Contenido] + [Condición]"
            }}
        ],
        "tabla_respuestas": [
            {{"pregunta": 1, "capacidad": "Capacidad", "desempeno": "Resumen", "respuesta_esperada": "Elementos clave de la respuesta", "justificacion": "Explicación", "retroalimentacion_correcta": "Felicitación y refuerzo de los elementos clave que el estudiante demostró comprender.", "retroalimentacion_incorrecta": "Explicación amable de los elementos clave que debía considerar para responder correctamente."}}
        ]
    }}
}}"""

        elif tipo_producto == 2:
            return base + f"""
{{
    "saludo": "Mensaje motivador al docente...",
    "examen": {{
        "titulo": "Título motivador",
        "grado": "{grado_nombre}",
        "competencia": "{competencia_nombre}",
        "instrucciones": "Lee la situación y marca la alternativa correcta.",
        "situacion_problematica": "Texto narrativo completo de la situación integradora...",
        "criterios_evaluacion": [
            {{"criterio": 1, "capacidad": "Nombre capacidad", "descripcion": "Habilidad + Contenido + Condición + Finalidad"}}
        ],
        "preguntas": [
            {{
                "numero": 1,
                "enunciado": "¿Enunciado del problema?",
                "tipo": "cerrada",
                "opciones": [
                    {{"letra": "A", "texto": "Opción 1", "es_correcta": false}},
                    {{"letra": "B", "texto": "Opción 2 (Correcta)", "es_correcta": true}},
                    {{"letra": "C", "texto": "Opción 3", "es_correcta": false}},
                    {{"letra": "D", "texto": "Opción 4", "es_correcta": false}},
                    {{"letra": "E", "texto": "Opción 5", "es_correcta": false}}
                ],
                "capacidad": "Nombre de la capacidad",
                "desempeno_codigo": "Código del desempeño",
                "criterio_evaluacion": "Criterio: [Habilidad] + [Contenido] + [Condición]"
            }}
        ],
        "tabla_respuestas": [
            {{"pregunta": 1, "capacidad": "Capacidad", "desempeno": "Resumen", "respuesta_correcta": "B", "justificacion": "Explicación", "retroalimentacion_correcta": "Felicitación breve y refuerzo de por qué es correcta.", "retroalimentacion_incorrecta": "Explicación amable de por qué la opción elegida no es correcta y por qué la correcta sí lo es."}}
        ]
    }}
}}"""

        elif tipo_producto == 3:
            return base + f"""
{{
    "saludo": "Mensaje motivador al docente...",
    "examen": {{
        "titulo": "Título motivador",
        "grado": "{grado_nombre}",
        "competencia": "{competencia_nombre}",
        "instrucciones": "Lee cada situación y marca la alternativa correcta.",
        "criterios_evaluacion": [
            {{"criterio": 1, "capacidad": "Nombre capacidad", "descripcion": "Habilidad + Contenido + Condición + Finalidad"}}
        ],
        "preguntas": [
            {{
                "numero": 1,
                "contexto": "Mini-situación propia de esta pregunta...",
                "enunciado": "¿Enunciado del problema?",
                "tipo": "cerrada",
                "opciones": [
                    {{"letra": "A", "texto": "Opción 1", "es_correcta": false}},
                    {{"letra": "B", "texto": "Opción 2 (Correcta)", "es_correcta": true}},
                    {{"letra": "C", "texto": "Opción 3", "es_correcta": false}},
                    {{"letra": "D", "texto": "Opción 4", "es_correcta": false}}
                ],
                "capacidad": "Nombre de la capacidad",
                "desempeno_codigo": "Código del desempeño",
                "criterio_evaluacion": "Criterio: [Habilidad] + [Contenido] + [Condición]"
            }}
        ],
        "tabla_respuestas": [
            {{"pregunta": 1, "capacidad": "Capacidad", "desempeno": "Resumen", "respuesta_correcta": "B", "justificacion": "Explicación", "retroalimentacion_correcta": "Felicitación breve y refuerzo de por qué es correcta.", "retroalimentacion_incorrecta": "Explicación amable de por qué la opción elegida no es correcta y por qué la correcta sí lo es."}}
        ]
    }}
}}"""

        elif tipo_producto == 4:
            return base + f"""
{{
    "saludo": "Mensaje motivador al docente...",
    "examen": {{
        "titulo": "Título motivador",
        "grado": "{grado_nombre}",
        "competencia": "{competencia_nombre}",
        "instrucciones": "Lee cada situación y desarrolla tu respuesta.",
        "criterios_evaluacion": [
            {{"criterio": 1, "capacidad": "Nombre capacidad", "descripcion": "Habilidad + Contenido + Condición + Finalidad"}}
        ],
        "preguntas": [
            {{
                "numero": 1,
                "contexto": "Mini-situación propia de esta pregunta...",
                "enunciado": "¿Pregunta abierta?",
                "tipo": "abierta",
                "espacio_respuesta": "Desarrolla tu respuesta aquí:",
                "capacidad": "Nombre de la capacidad",
                "desempeno_codigo": "Código del desempeño",
                "criterio_evaluacion": "Criterio: [Habilidad] + [Contenido] + [Condición]"
            }}
        ],
        "tabla_respuestas": [
            {{"pregunta": 1, "capacidad": "Capacidad", "desempeno": "Resumen", "respuesta_esperada": "Elementos clave", "justificacion": "Explicación", "retroalimentacion_correcta": "Felicitación y refuerzo de los elementos clave que el estudiante demostró comprender.", "retroalimentacion_incorrecta": "Explicación amable de los elementos clave que debía considerar para responder correctamente."}}
        ]
    }}
}}"""

        else:  # tipo_producto == 5 - Actividad de Aprendizaje
            return base + f"""
{{
    "saludo": "Mensaje motivador al docente...",
    "actividad": {{
        "titulo": "Título de la sesión de aprendizaje",
        "grado": "{grado_nombre}",
        "competencia": "{competencia_nombre}",
        "duracion": "90 minutos",
        "proposito": "Propósito de la sesión de aprendizaje...",
        "criterios_evaluacion": [
            {{"criterio": 1, "capacidad": "Nombre capacidad", "descripcion": "Habilidad + Contenido + Condición + Finalidad"}}
        ],
        "inicio": {{
            "duracion": "15 minutos",
            "actividades": [
                {{"tipo": "motivacion", "descripcion": "Actividad motivadora o situación provocadora..."}},
                {{"tipo": "saberes_previos", "descripcion": "Preguntas para rescatar saberes previos..."}},
                {{"tipo": "proposito", "descripcion": "Comunicar el propósito de la sesión..."}}
            ]
        }},
        "desarrollo": {{
            "duracion": "60 minutos",
            "actividades": [
                {{
                    "capacidad": "Nombre capacidad 1",
                    "descripcion": "Descripción de la actividad principal...",
                    "materiales": ["Material 1", "Material 2"],
                    "preguntas_guia": ["¿Pregunta reflexiva 1?", "¿Pregunta reflexiva 2?"]
                }}
            ]
        }},
        "cierre": {{
            "duracion": "15 minutos",
            "actividades": [
                {{"tipo": "metacognicion", "preguntas": ["¿Qué aprendiste?", "¿Para qué te sirve?", "¿Cómo lo aprendiste?"]}},
                {{"tipo": "evaluacion_formativa", "descripcion": "Actividad de evaluación final breve..."}}
            ]
        }}
    }}
}}"""

    def _build_prompt_matematica(
        self,
        grado_nombre: str,
        competencia_nombre: str,
        capacidades_desempenos: dict,
        cantidad: int,
        estandar_descripcion: Optional[str] = None,
        situacion_base: Optional[str] = None,
        nivel_dificultad: str = "intermedio",
        contenido_tematico: Optional[str] = None,
        tipo_producto: int = 1
    ) -> str:
        """
        Construye el prompt para generar un instrumento de evaluación de matemática
        siguiendo el formato oficial del MINEDU.
        """

        # Formatear desempeños por capacidad
        desempenos_formateados = ""
        for orden, data in capacidades_desempenos.items():
            desempenos_formateados += f"\n**Capacidad {orden}: {data['nombre']}**\n"
            for des in data['desempenos']:
                desempenos_formateados += f"  - {des['codigo']}: {des['descripcion']}\n"

        # Estándar de aprendizaje
        estandar_texto = ""
        if estandar_descripcion:
            estandar_texto = f"""
**ESTÁNDAR DE APRENDIZAJE (Nivel esperado del ciclo):**
\"\"\"{estandar_descripcion}\"\"\"
Este estándar define el nivel de desempeño esperado. Asegúrate que el instrumento evalúe competencias acordes a este nivel.
"""

        # Contenido temático
        contenido_texto = ""
        if contenido_tematico:
            contenido_texto = f"""
**CONTENIDO TEMÁTICO ESPECÍFICO:**
El instrumento debe abordar específicamente: **{contenido_tematico}**
Integra este contenido de manera coherente en la situación y las preguntas.
"""

        # Situación base
        situacion_texto = ""
        if situacion_base:
            situacion_texto = f"""
**SITUACIÓN PROBLEMÁTICA PROPORCIONADA:**
\"\"\"{situacion_base}\"\"\"
Usa esta situación como base o adaptación para el problema.
"""

        # Instrucciones de dificultad
        dificultad_instrucciones = {
            "basico": """
**NIVEL DE DIFICULTAD: BÁSICO**
- Situación SENCILLA y fácil de comprender
- Números pequeños, operaciones directas (1-2 pasos)
- Contextos cotidianos, datos explícitos
- Alternativas incorrectas claramente distinguibles""",
            "intermedio": """
**NIVEL DE DIFICULTAD: INTERMEDIO**
- Complejidad moderada (2-3 pasos)
- Requiere identificar datos relevantes y organizar información
- Alternativas incorrectas plausibles
- Combina diferentes operaciones o conceptos""",
            "avanzado": """
**NIVEL DE DIFICULTAD: AVANZADO (Alta demanda cognitiva)**
- Situación COMPLEJA y desafiante (3+ pasos)
- Requiere razonamiento, estrategia y análisis
- Alternativas muy plausibles (distractores bien elaborados)
- Puede requerir conceptos combinados de diferentes capacidades"""
        }
        instruccion_dificultad = dificultad_instrucciones.get(nivel_dificultad.lower(), dificultad_instrucciones["intermedio"])

        # Tipo de producto
        tipo_info = TIPOS_PRODUCTO.get(tipo_producto, TIPOS_PRODUCTO[1])
        instruccion_tipo = f"""
**TIPO DE PRODUCTO A GENERAR: Tipo {tipo_producto} - {tipo_info['nombre']}**
{tipo_info['descripcion']}
"""

        # Criterios de evaluación
        criterios = self._build_criterios_evaluacion(capacidades_desempenos)

        # Formato JSON
        formato_json = self._build_json_format_by_tipo(tipo_producto, grado_nombre, competencia_nombre)

        # Nota sobre cantidad de preguntas o actividades
        nota_cantidad = ""
        if tipo_producto == 5:
            nota_cantidad = "La actividad debe tener al menos una sub-actividad por cada capacidad seleccionada."
        else:
            num_capacidades = len(capacidades_desempenos)
            nota_cantidad = (
                f"Genera EXACTAMENTE {cantidad} preguntas en total, ni más ni menos (el arreglo \"preguntas\" del JSON debe tener {cantidad} elementos). "
                f"Hay {num_capacidades} capacidad(es) evaluada(s): distribúyelas de forma equilibrada entre ellas. "
                f"Si {cantidad} es mayor que {num_capacidades}, genera varias preguntas para algunas o todas las capacidades hasta completar el total. "
                f"Si {cantidad} es menor que {num_capacidades}, prioriza cubrir la mayor cantidad de capacidades posible."
            )

        prompt = f"""Eres un especialista pedagógico en Matemática del MINEDU (Perú), experto en diseño de instrumentos de evaluación por competencias.
Diseña el siguiente instrumento para estudiantes de **{grado_nombre}**.

**PARÁMETROS CURRICULARES:**
- **Competencia:** {competencia_nombre}
- **Grado:** {grado_nombre}
- **Contexto:** Regional Peruano (mercados locales, ferias, turismo, geografía, biodiversidad del Perú).

{estandar_texto}
{contenido_texto}
{instruccion_tipo}

**INSUMO BASE:**
{situacion_texto if situacion_base else "CREA UNA SITUACIÓN ORIGINAL basada en un contexto real y motivador para la edad del estudiante."}

**DESEMPEÑOS A EVALUAR:**
{desempenos_formateados}

**CRITERIOS DE EVALUACIÓN FORMAL (uno por capacidad):**
{criterios}
Construye un criterio formal para cada capacidad según el formato: [Habilidad] + [Contenido] + [Condición] + [Finalidad].

{instruccion_dificultad}

**REQUERIMIENTOS:**
{nota_cantidad}
Cada pregunta o actividad debe vincularse a UNO de los desempeños listados.
El contexto debe ser PERUANO, auténtico y motivador para la edad del estudiante.

{NOTACION_MATEMATICA}

{formato_json}
"""
        return prompt

    async def generar_examen_matematica(
        self,
        db: AsyncSession,
        grado_id: int,
        competencia_id: int,
        desempeno_ids: List[int],
        cantidad: int = 3,
        situacion_base: Optional[str] = None,
        modelo: str = "gemini",
        nivel_dificultad: str = "intermedio",
        contenido_tematico: Optional[str] = None,
        tipo_producto: int = 1
    ) -> dict:
        """
        Genera un instrumento de evaluación de matemática basado en desempeños específicos.
        """
        ai_service = ai_factory.get_service(modelo)

        if not ai_service.is_configured():
            raise ValueError(f"Configuración de API para {modelo} incompleta")

        if not desempeno_ids:
            raise ValueError("Debe seleccionar al menos un desempeño")

        # Obtener grado
        result_grado = await db.execute(select(Grado).where(Grado.id == grado_id))
        grado = result_grado.scalars().first()
        if not grado:
            raise ValueError(f"Grado con id {grado_id} no encontrado")

        # Obtener competencia
        result_comp = await db.execute(select(CompetenciaMatematica).where(CompetenciaMatematica.id == competencia_id))
        competencia = result_comp.scalars().first()
        if not competencia:
            raise ValueError(f"Competencia con id {competencia_id} no encontrada")

        # Obtener estándar de aprendizaje
        result_est = await db.execute(
            select(EstandarMatematica).where(
                EstandarMatematica.grado_id == grado_id,
                EstandarMatematica.competencia_id == competencia_id
            )
        )
        estandar = result_est.scalars().first()
        estandar_descripcion = estandar.descripcion if estandar else None

        # Obtener desempeños seleccionados con sus capacidades
        result_desempenos = await db.execute(
            select(DesempenoMatematica)
            .where(DesempenoMatematica.id.in_(desempeno_ids))
            .options(selectinload(DesempenoMatematica.capacidad))
        )
        desempenos = result_desempenos.scalars().all()

        if not desempenos:
            raise ValueError("No se encontraron los desempeños seleccionados")

        # Organizar desempeños por capacidad
        capacidades_desempenos = {}
        for d in desempenos:
            cap = d.capacidad
            if cap.orden not in capacidades_desempenos:
                capacidades_desempenos[cap.orden] = {
                    'nombre': cap.nombre,
                    'desempenos': []
                }
            capacidades_desempenos[cap.orden]['desempenos'].append({
                'codigo': d.codigo,
                'descripcion': d.descripcion
            })

        # Construir prompt
        prompt = self._build_prompt_matematica(
            grado_nombre=grado.nombre,
            competencia_nombre=competencia.nombre,
            capacidades_desempenos=capacidades_desempenos,
            cantidad=cantidad,
            estandar_descripcion=estandar_descripcion,
            situacion_base=situacion_base,
            nivel_dificultad=nivel_dificultad,
            contenido_tematico=contenido_tematico,
            tipo_producto=tipo_producto
        )

        # Seleccionar schema según tipo de producto
        schema = RespuestaActividad if tipo_producto == 5 else RespuestaMat

        try:
            data = await ai_service.generate_structured_content(prompt, schema)

            desempenos_texto = "\n".join([
                f"{d.codigo}. {d.descripcion} (Cap: {d.capacidad.nombre})"
                for d in desempenos
            ])

            tipo_info = TIPOS_PRODUCTO.get(tipo_producto, TIPOS_PRODUCTO[1])
            is_actividad = tipo_producto == 5
            examen_data = data.get("actividad" if is_actividad else "examen", {})

            if is_actividad:
                desarrollo = examen_data.get("desarrollo", {})
                total = len(desarrollo.get("actividades", []) if isinstance(desarrollo, dict) else [])
            else:
                total = len(examen_data.get("preguntas", []) if isinstance(examen_data, dict) else [])

            return {
                "grado": grado.nombre,
                "competencia": competencia.nombre,
                "desempenos_usados": desempenos_texto,
                "estandar": estandar_descripcion,
                "tipo_producto": tipo_producto,
                "tipo_producto_nombre": tipo_info["nombre"],
                "saludo": data.get("saludo", ""),
                "examen": examen_data,
                "es_actividad": is_actividad,
                "total_preguntas": total
            }

        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Error al generar examen de matemática: {e}")


# Singleton instance
matsistem_service = MatSistemService()
