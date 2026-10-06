from google import genai
from google.genai import types
import json
import asyncio
import logging
import time
from typing import Optional, Type

from app.core.config import get_settings
from app.models.pregunta import Pregunta, TipoPregunta, OpcionMultiple
from app.models.ai_schemas import RespuestaPreguntas
from app.services.ai_base import (
    AIService,
    PRESUPUESTO_IA_SEGUNDOS,
    TIMEOUT_INTENTO_SEGUNDOS,
    repair_latex_backslash_escapes,
    repair_stray_control_chars,
)

settings = get_settings()
logger = logging.getLogger(__name__)

# Tope de tokens de salida por llamada. 8192 no alcanza para un examen largo
# (20 preguntas + tabla de respuestas con justificación y retroalimentación):
# el JSON se cortaba a medias y la reparación lo cerraba en silencio.
MAX_OUTPUT_TOKENS_POR_DEFECTO = 8192
MAX_OUTPUT_TOKENS_TECHO = 65536

# Ping de sondeo: presupuesto total (repartido entre rondas) para encontrar una
# pareja (modelo, clave) que responda antes de lanzar la generación real.
# Los sondeos de una ronda corren en paralelo, así que el coste en tiempo es
# ~1 ping por ronda.
PING_PRESUPUESTO_SEGUNDOS = 14.0
PING_TIMEOUT_SEGUNDOS = 6.0
# Parejas sondeadas por ronda: la primera clave fresca de cada modelo, para
# cubrir todos los modelos sin hacer una tormenta de peticiones.
MAX_PAREJAS_SONDEO = 8
# Rondas de sondeo + generación que se llegan a probar en una misma petición.
MAX_PAREJAS_INTENTADAS = 3
# Cuánto se confía en el fallo reciente de un par (modelo, clave) antes de
# volver a probarlo. Evita reintentar en cada llamada un modelo que acaba de
# devolver 404/503/429.
TTL_FALLO_SEGUNDOS = 180.0


def _is_quota_error(e: Exception) -> bool:
    return "quota exceeded" in str(e).lower() or "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e)


def _codigo_error(e: Exception) -> str:
    """Clasifica el error de la API para decidir si se rota clave/modelo."""
    texto = str(e)
    if "404" in texto or "NOT_FOUND" in texto:
        return "404"
    if "400" in texto or "INVALID_ARGUMENT" in texto:
        return "400"
    if _is_quota_error(e):
        return "429"
    if "503" in texto or "UNAVAILABLE" in texto:
        return "503"
    return ""


class GeminiService(AIService):
    """Service for generating questions using Google Gemini (new SDK)."""

    def __init__(self):
        # Lista de modelos por si se necesita inspeccionarla/logging; la fuente
        # de verdad es settings.gemini_model_list (permite cambiar sin redeploy).
        self.model_name = (settings.gemini_model_list or [""])[0]
        self.clients = [genai.Client(api_key=key) for key in settings.google_api_keys]
        # Contador en memoria (se reinicia con cada despliegue/reinicio del proceso)
        # para observar cuánto se está usando cada clave de contingencia.
        self.stats = [{"llamadas_ok": 0, "errores_cuota": 0} for _ in self.clients]
        self.agotamientos_totales = 0
        # (modelo, índice de clave) -> momento del último fallo rotable.
        self._fallos: dict[tuple[str, int], float] = {}
        # Última pareja que respondió bien: se reutiliza sin volver a sondear.
        self._par_conocido: Optional[tuple[str, int]] = None
        # Modelos que rechazan thinking_config (400 INVALID_ARGUMENT): se les
        # pide la respuesta sin desactivar el razonamiento. Se preajusta con
        # los modelos "lite" (confirmado) y se aprende del resto en caliente.
        self._modelos_sin_pensamiento: set[str] = {
            m for m in settings.gemini_model_list if "lite" in m.lower()
        }

    def is_configured(self) -> bool:
        return len(self.clients) > 0

    def _parejas_candidatas(self) -> list[tuple[str, int]]:
        """Parejas (modelo, clave) en orden de preferencia, sin las fallidas."""
        parejas = [
            (modelo, indice)
            for modelo in settings.gemini_model_list
            for indice in range(len(self.clients))
        ]
        ahora = time.monotonic()
        frescas = [
            par for par in parejas
            if ahora - self._fallos.get(par, 0.0) >= TTL_FALLO_SEGUNDOS
        ]
        return frescas or parejas

    def _candidatas_sondeo(self) -> list[tuple[str, int]]:
        """Parejas a sondear en paralelo, cubriendo primero todos los modelos."""
        por_modelo: dict[str, list[int]] = {}
        for modelo, indice in self._parejas_candidatas():
            por_modelo.setdefault(modelo, []).append(indice)

        salida: list[tuple[str, int]] = []
        # Primera ronda: la primera clave fresca de cada modelo.
        for modelo, indices in por_modelo.items():
            salida.append((modelo, indices[0]))
        # Segunda ronda: el resto de claves, para modelos con 429/404 por clave.
        for modelo, indices in por_modelo.items():
            for indice in indices[1:]:
                if len(salida) >= MAX_PAREJAS_SONDEO:
                    return salida
                salida.append((modelo, indice))
        return salida[:MAX_PAREJAS_SONDEO]

    def _ping_config(self, modelo: str):
        """Configuración del sondeo para el modelo indicado.

        Con ``thinking_budget=0`` la respuesta "OK" llega en ~1s; sin esa
        bandera el modelo se pone a razonar y un ping de 8s se queda corto
        (parece que no responde y se descarta un modelo sano).
        """
        return self._config_para_modelo(
            types.GenerateContentConfig(
                max_output_tokens=8,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
            modelo,
        )

    async def _sondear(self, par: tuple[str, int], estado: dict, tope: float) -> Optional[tuple[str, int]]:
        """Devuelve ``par`` si responde a un ping mínimo; si no, lo marca fallido.

        Si el modelo rechaza ``thinking_config`` (400) se reintenta el sondeo
        sin esa bandera en vez de descartarlo por un problema de configuración.
        """
        modelo, indice = par
        config_ping = self._ping_config(modelo)
        reintento_config = False
        while True:
            try:
                await asyncio.wait_for(
                    self.clients[indice].aio.models.generate_content(
                        model=modelo,
                        contents="Responde únicamente: OK",
                        config=config_ping,
                    ),
                    timeout=tope,
                )
                break
            except Exception as e:
                codigo = "" if isinstance(e, asyncio.TimeoutError) else _codigo_error(e)
                if codigo == "400" and not reintento_config:
                    reintento_config = True
                    self._modelos_sin_pensamiento.add(modelo)
                    config_ping = self._ping_config(modelo)
                    logger.warning(
                        "Gemini ping: modelo=%s rechaza thinking_config, reintento sin él",
                        modelo,
                    )
                    continue
                self._fallos[par] = time.monotonic()
                if codigo == "429":
                    estado["cuota"] = True
                    self.stats[indice]["errores_cuota"] += 1
                if codigo == "503":
                    estado["indisponible"] = True
                estado["error"] = e
                logger.warning(
                    "Gemini ping: modelo=%s clave=#%d error=%s (%s)",
                    modelo, indice + 1, codigo or type(e).__name__, str(e)[:140],
                )
                return None
        self._fallos.pop(par, None)
        return par

    async def _elegir_par(self, presupuesto: float):
        """Busca una pareja (modelo, clave) que responda, con un ping barato.

        Google retira modelos (404), agota cuotas por clave (429) y suele
        devolver 503 por alta demanda. Sondear en paralelo y saltar directamente
        a una pareja que responde evita quemar el presupuesto de la petición
        (60s en el proxy de producción) con modelos caídos antes siquiera de
        empezar a generar.

        Devuelve ``(par, ultimo_error, agotamos_cuota, indisponible)``; ``par``
        es ``None`` si ninguna pareja respondió dentro del presupuesto indicado.
        """
        if (
            self._par_conocido is not None
            and time.monotonic() - self._fallos.get(self._par_conocido, 0.0) >= TTL_FALLO_SEGUNDOS
        ):
            return self._par_conocido, None, False, False

        candidatas = self._candidatas_sondeo()
        if not candidatas:
            return None, None, False, False

        estado: dict = {"error": None, "cuota": False, "indisponible": False}
        tope = max(1.0, min(PING_TIMEOUT_SEGUNDOS, presupuesto))
        t0 = time.monotonic()
        try:
            resultados = await asyncio.wait_for(
                asyncio.gather(*[self._sondear(par, estado, tope) for par in candidatas]),
                timeout=presupuesto + 1.0,
            )
        except asyncio.TimeoutError:
            resultados = [None] * len(candidatas)

        for par, resultado in zip(candidatas, resultados):
            if resultado is not None:
                logger.info(
                    "Gemini sondeo: %d parejas en %.1fs → %s (clave #%d)",
                    len(candidatas), time.monotonic() - t0, par[0], par[1] + 1,
                )
                return par, None, False, False
        logger.info(
            "Gemini sondeo: %d parejas en %.1fs → ninguna respondió",
            len(candidatas), time.monotonic() - t0,
        )
        return None, estado["error"], estado["cuota"], estado["indisponible"]

    def _config_para_modelo(self, config: "types.GenerateContentConfig", modelo: str):
        """Configuración válida para el modelo.

        Algunos modelos (lite y varios nuevos) rechazan ``thinking_config``
        con 400 INVALID_ARGUMENT; a esos se les pide la respuesta sin esa
        bandera. El caso se recuerda en :attr:`_modelos_sin_pensamiento`.
        """
        if not getattr(config, "thinking_config", None):
            return config
        if modelo in self._modelos_sin_pensamiento:
            return config.model_copy(update={"thinking_config": None})
        return config

    async def _generate(
        self,
        config: "types.GenerateContentConfig",
        contents: str,
        timeout: float = TIMEOUT_INTENTO_SEGUNDOS,
        deadline: Optional[float] = None,
    ):
        """Genera contenido probando las parejas (modelo, clave) disponibles.

        Primero elige con :meth:`_elegir_par` una pareja que responda y le da
        todo el presupuesto restante a la generación. Si esa pareja falla de
        forma rotable (429/404/503/timeout), se marca y se busca otra.

        - 429 (cuota agotada), 404 (modelo retirado del free tier para esa
          cuenta) y 503 (alta demanda) → se rota de pareja.
        - Las parejas que fallaron se saltan durante ``TTL_FALLO_SEGUNDOS``
          salvo que no quede ninguna fresca.
        - Errores no rotables (safety block...) → se lanzan ya.
        """
        if not self.clients:
            raise ValueError("Google API key no configurada")

        if not settings.gemini_model_list:
            raise ValueError("No hay modelos Gemini configurados (GEMINI_MODELS)")

        # Sin presupuesto explícito, todo (sondeo de modelos + generación) se
        # reparte dentro del presupuesto global: ping 14s + 45s de generación
        # superarían los 60s del proxy de producción.
        if deadline is None:
            deadline = time.monotonic() + PRESUPUESTO_IA_SEGUNDOS

        vistos_429 = False
        vistos_503 = False
        ultimo_error: Optional[Exception] = None
        ping_consumido = 0.0

        for _ in range(MAX_PAREJAS_INTENTADAS):
            presupuesto_ping = PING_PRESUPUESTO_SEGUNDOS - ping_consumido
            if deadline is not None:
                presupuesto_ping = min(presupuesto_ping, deadline - time.monotonic())
            if presupuesto_ping < 3.0:
                break
            t_ping = time.monotonic()
            par, error_ping, cuota_ping, indisponible_ping = await self._elegir_par(presupuesto_ping)
            ping_consumido += time.monotonic() - t_ping
            vistos_429 = vistos_429 or cuota_ping
            vistos_503 = vistos_503 or indisponible_ping
            ultimo_error = error_ping or ultimo_error
            if par is None:
                # Ninguna pareja respondió en esta ronda (503 transitorio, por
                # ejemplo): se vuelve a sondear; las fallidas ya quedaron
                # marcadas y las frescas son las candidatas.
                continue

            modelo, indice = par
            # El ping ya demostró que responde: se fija para que las rondas
            # siguientes no vuelvan a sondear (ahorramos presupuesto).
            self._par_conocido = par
            client = self.clients[indice]
            config_efectivo = self._config_para_modelo(config, modelo)
            reintento_config = False

            while True:
                # Se recalcula en cada intento: un reintento de configuración
                # (400 por thinking_config) consume presupuesto real.
                if deadline is not None:
                    restante = deadline - time.monotonic()
                    if restante < 2.0:
                        raise ValueError(
                            "Se agotó el tiempo de respuesta de la IA antes de completar el examen. "
                            "Prueba de nuevo o genera menos preguntas."
                        )
                    tiempo = min(timeout, restante)
                else:
                    tiempo = timeout
                if tiempo < 2.0:
                    break

                try:
                    coro = client.aio.models.generate_content(
                        model=modelo,
                        contents=contents,
                        config=config_efectivo,
                    )
                    t_llamada = time.monotonic()
                    response = await asyncio.wait_for(coro, timeout=tiempo)

                    if not response.candidates:
                        raise ValueError("Respuesta bloqueada por filtros de seguridad")

                    first_candidate = response.candidates[0]
                    finish_reason = getattr(first_candidate, "finish_reason", None)

                    text = response.text
                    if not text or not text.strip():
                        raise ValueError("Gemini devolvió una respuesta vacía")

                    usage = getattr(response, "usage_metadata", None)
                    logger.info(
                        "Gemini ok modelo=%s clave=#%d segundos=%.1f finish=%s tokens_entrada=%s tokens_salida=%s",
                        modelo, indice + 1, time.monotonic() - t_llamada, finish_reason,
                        getattr(usage, "prompt_token_count", None),
                        getattr(usage, "candidates_token_count", None),
                    )
                    self.stats[indice]["llamadas_ok"] += 1
                    self._fallos.pop(par, None)
                    self._par_conocido = par
                    return text, finish_reason, modelo
                except asyncio.TimeoutError:
                    if deadline is not None and time.monotonic() >= deadline:
                        raise ValueError(
                            "Se agotó el tiempo de respuesta de la IA antes de completar el examen. "
                            "Prueba de nuevo o genera menos preguntas."
                        )
                    # La pareja se colgó sin devolver error: se marca y se prueba otra.
                    self._fallos[par] = time.monotonic()
                    self._par_conocido = None
                    ultimo_error = TimeoutError("Gemini no respondió a tiempo")
                    logger.warning("Gemini rotando: modelo=%s clave=#%d timeout", modelo, indice + 1)
                    break
                except ValueError:
                    raise
                except Exception as e:
                    ultimo_error = e
                    codigo = _codigo_error(e)
                    if codigo == "400" and not reintento_config and config_efectivo is config:
                        # Este modelo no acepta thinking_config: se le pide la
                        # respuesta sin desactivar el razonamiento y se recuerda
                        # para las siguientes peticiones del proceso.
                        reintento_config = True
                        self._modelos_sin_pensamiento.add(modelo)
                        config_efectivo = config.model_copy(update={"thinking_config": None})
                        logger.warning(
                            "Gemini: modelo=%s rechaza thinking_config, reintento sin él (%s)",
                            modelo, str(e)[:140],
                        )
                        continue
                    if codigo in ("429", "404", "503"):
                        self._fallos[par] = time.monotonic()
                        self._par_conocido = None
                        if codigo == "429":
                            vistos_429 = True
                            self.stats[indice]["errores_cuota"] += 1
                        if codigo == "503":
                            vistos_503 = True
                        logger.warning(
                            "Gemini rotando: modelo=%s clave=#%d error=%s (%s)",
                            modelo, indice + 1, codigo, str(e)[:160],
                        )
                        break
                    raise ValueError(f"Error al generar contenido con Gemini: {e}")
            continue

        self.agotamientos_totales += 1
        logger.error(
            "Gemini: agotaron sus modelos/claves en esta petición (agotamientos totales: %d)",
            self.agotamientos_totales,
        )
        if vistos_429 and vistos_503:
            raise ValueError(
                "Gemini está temporalmente no disponible o sin cuota en todas las claves configuradas. "
                "Intenta de nuevo en unos segundos."
            ) from ultimo_error
        if vistos_429:
            raise ValueError(
                "Se excedió la cuota de peticiones a la API de Google Gemini en todas las claves configuradas. "
                "Por favor espera un minuto antes de reintentar."
            ) from ultimo_error
        if vistos_503:
            raise ValueError(
                "Los modelos de Gemini están con alta demanda (503). "
                "Intenta de nuevo en unos segundos."
            ) from ultimo_error
        raise ValueError(
            "Ningún modelo de Gemini respondió (posible indisponibilidad temporal del servicio). "
            "Intenta de nuevo en unos segundos."
        ) from ultimo_error

    async def generate_content(self, prompt: str) -> str:
        """Generate raw text content from Gemini.

        Thinking is disabled (budget=0) to keep latency and token usage
        predictable for short-form outputs like retroalimentación.
        """
        config = types.GenerateContentConfig(
            max_output_tokens=MAX_OUTPUT_TOKENS_POR_DEFECTO,
            thinking_config=types.ThinkingConfig(thinking_budget=0),
        )
        text, _, _ = await self._generate(config, prompt)
        return text

    async def generate_structured_content(
        self,
        prompt: str,
        schema: Type,
        max_output_tokens: Optional[int] = None,
        timeout: float = TIMEOUT_INTENTO_SEGUNDOS,
        deadline: Optional[float] = None,
    ) -> dict:
        """Generate JSON output enforced by a Pydantic schema (Gemini structured output).

        thinking_budget=0 reserves all max_output_tokens for the actual JSON
        response, avoiding empty schemas caused by thinking tokens consuming
        the output budget.

        ``max_output_tokens`` debe escalarse con el tamaño del examen: si el
        modelo se queda sin presupuesto, Gemini corta el JSON a la mitad y la
        reparación posterior lo cierra "en silencio" con filas incompletas.
        """
        limite = max(MAX_OUTPUT_TOKENS_POR_DEFECTO, int(max_output_tokens or 0))
        limite = min(MAX_OUTPUT_TOKENS_TECHO, limite)
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=schema,
            max_output_tokens=limite,
            thinking_config=types.ThinkingConfig(thinking_budget=0),
        )
        text, finish_reason, modelo = await self._generate(
            config, prompt, timeout=timeout, deadline=deadline
        )
        if "MAX_TOKENS" in str(finish_reason):
            raise ValueError(
                f"La respuesta de Gemini ({modelo}) se cortó por el límite de {limite} tokens "
                "y quedó incompleta. Vuelve a intentarlo; si persiste, reduce la cantidad de preguntas."
            )
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            # Reintento: puede haber comandos LaTeX (\frac, \times, \ne...)
            # con el backslash sin doblar. Ver repair_latex_backslash_escapes.
            try:
                data = json.loads(repair_latex_backslash_escapes(text))
            except json.JSONDecodeError:
                # Intento adicional de limpieza y reparación de JSON
                try:
                    cleaned = self.clean_json_response(text)
                    data = json.loads(cleaned)
                except json.JSONDecodeError as e:
                    finish_reason_str = str(finish_reason) if finish_reason else ""
                    if "MAX_TOKENS" in finish_reason_str:
                        raise ValueError(
                            "La respuesta generada por Gemini excedió la longitud máxima permitida (límite de tokens) "
                            "y quedó incompleta. Por favor intenta reduciendo la cantidad de preguntas o el tamaño del texto."
                        )
                    raise ValueError(f"Error al parsear la respuesta estructurada de Gemini: {e}")
        return repair_stray_control_chars(data)

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
