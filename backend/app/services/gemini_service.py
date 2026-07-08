from google import genai
from google.genai import types
import json
import asyncio
import logging
from typing import Optional, Type

from app.core.config import get_settings
from app.models.pregunta import Pregunta, TipoPregunta, OpcionMultiple
from app.models.ai_schemas import RespuestaPreguntas
from app.services.ai_base import AIService

settings = get_settings()
logger = logging.getLogger(__name__)


def _is_quota_error(e: Exception) -> bool:
    return "quota exceeded" in str(e).lower() or "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e)


class GeminiService(AIService):
    """Service for generating questions using Google Gemini 2.5 Flash (new SDK)."""

    def __init__(self):
        self.model_name = 'gemini-2.5-flash'
        self.clients = [genai.Client(api_key=key) for key in settings.google_api_keys]
        # Contador en memoria (se reinicia con cada despliegue/reinicio del proceso)
        # para observar cuánto se está usando cada clave de contingencia.
        self.stats = [{"llamadas_ok": 0, "errores_cuota": 0} for _ in self.clients]
        self.agotamientos_totales = 0

    def is_configured(self) -> bool:
        return len(self.clients) > 0

    async def _generate(self, config: "types.GenerateContentConfig", contents: str):
        """Try each configured API key in order, rotating to the next one on
        quota/429 errors. Non-quota errors (timeout, safety block, etc.) are
        raised immediately without rotating, since another key won't fix them.
        """
        if not self.clients:
            raise ValueError("Google API key no configurada")

        last_quota_error: Optional[Exception] = None

        for index, client in enumerate(self.clients):
            try:
                coro = client.aio.models.generate_content(
                    model=self.model_name,
                    contents=contents,
                    config=config,
                )
                response = await asyncio.wait_for(coro, timeout=45.0)

                if not response.candidates:
                    raise ValueError("Respuesta bloqueada por filtros de seguridad")

                text = response.text
                if not text or not text.strip():
                    raise ValueError("Gemini devolvió una respuesta vacía")

                self.stats[index]["llamadas_ok"] += 1
                return text
            except asyncio.TimeoutError:
                raise ValueError(
                    "La API de Google Gemini tardó demasiado en responder (Timeout). "
                    "Es posible que la cuota gratuita esté al límite. Intenta de nuevo o genera menos preguntas."
                )
            except ValueError:
                raise
            except Exception as e:
                if _is_quota_error(e):
                    self.stats[index]["errores_cuota"] += 1
                    last_quota_error = e
                    logger.warning(
                        "Gemini clave #%d agotó su cuota, rotando a la siguiente (%d/%d claves probadas)",
                        index + 1, index + 1, len(self.clients),
                    )
                    continue
                raise ValueError(f"Error al generar contenido con Gemini: {e}")

        self.agotamientos_totales += 1
        logger.error(
            "Gemini: las %d claves configuradas agotaron su cuota en esta petición (agotamientos totales: %d)",
            len(self.clients), self.agotamientos_totales,
        )
        raise ValueError(
            "Se excedió la cuota de peticiones a la API de Google Gemini en todas las claves configuradas. "
            "Por favor espera un minuto antes de reintentar."
        ) from last_quota_error

    async def generate_content(self, prompt: str) -> str:
        """Generate raw text content from Gemini.

        Thinking is disabled (budget=0) to keep latency and token usage
        predictable for short-form outputs like retroalimentación.
        """
        config = types.GenerateContentConfig(
            max_output_tokens=8192,
            thinking_config=types.ThinkingConfig(thinking_budget=0),
        )
        return await self._generate(config, prompt)

    async def generate_structured_content(self, prompt: str, schema: Type) -> dict:
        """Generate JSON output enforced by a Pydantic schema (Gemini structured output).

        thinking_budget=0 reserves all max_output_tokens for the actual JSON
        response, avoiding empty schemas caused by thinking tokens consuming
        the output budget.
        """
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=schema,
            max_output_tokens=8192,
            thinking_config=types.ThinkingConfig(thinking_budget=0),
        )
        try:
            text = await self._generate(config, prompt)
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Error al parsear la respuesta estructurada de Gemini: {e}")

    def _build_prompt(
        self,
        competencias: list[dict],
        cantidad: int,
        tipo: str,
        dificultad: str
    ) -> str:
        competencias_texto = "\n".join([
            f"- {c.get('nombre', '')}: {c.get('descripcion', '')}"
            for c in competencias
        ])

        return f"""Eres un experto en educación y evaluación de estudiantes.
Genera exactamente {cantidad} preguntas de opción múltiple (4 alternativas) con nivel de dificultad {dificultad}.

Las preguntas deben evaluar las siguientes competencias:
{competencias_texto}

IMPORTANTE: Responde ÚNICAMENTE con un JSON válido con la siguiente estructura, sin texto adicional:
{{
    "preguntas": [
        {{
            "enunciado": "texto de la pregunta",
            "tipo": "multiple",
            "opciones": [
                {{"texto": "opción a", "es_correcta": false}},
                {{"texto": "opción b", "es_correcta": true}},
                {{"texto": "opción c", "es_correcta": false}},
                {{"texto": "opción d", "es_correcta": false}}
            ],
            "respuesta_correcta": "texto de la respuesta correcta",
            "explicacion": "breve explicación de por qué es correcta",
            "dificultad": "{dificultad}",
            "competencia_asociada": "nombre de la competencia que evalúa"
        }}
    ]
}}
"""

    async def generar_preguntas(
        self,
        competencias: list[dict],
        cantidad: int = 5,
        tipo: str = "multiple",
        dificultad: str = "intermedio"
    ) -> list[Pregunta]:
        """Generate questions using Gemini structured output."""
        prompt = self._build_prompt(competencias, cantidad, tipo, dificultad)

        try:
            data = await self.generate_structured_content(prompt, RespuestaPreguntas)

            preguntas = []
            for p in data.get("preguntas", []):
                opciones = None
                if p.get("opciones"):
                    opciones = [
                        OpcionMultiple(texto=o["texto"], es_correcta=o.get("es_correcta", False))
                        for o in p["opciones"]
                    ]

                pregunta = Pregunta(
                    enunciado=p["enunciado"],
                    tipo=TipoPregunta(p.get("tipo", "multiple")),
                    opciones=opciones,
                    respuesta_correcta=p.get("respuesta_correcta"),
                    explicacion=p.get("explicacion"),
                    dificultad=p.get("dificultad", dificultad),
                    competencia_asociada=p.get("competencia_asociada")
                )
                preguntas.append(pregunta)

            return preguntas

        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Error al procesar preguntas con Gemini: {e}")


# Singleton instance
gemini_service = GeminiService()
