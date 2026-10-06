"""
Servicio para gestionar desempenos y generar preguntas de comprensión lectora.
"""
from typing import Optional
import logging
import re
import time
import unicodedata
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import random

from app.models.db_models import Grado, Capacidad, Desempeno
from app.models.ai_schemas import RespuestaLecto
from app.core.config import get_settings
from app.services.ai_factory import ai_factory
from app.services.prompt_fragments import NOTACION_MATEMATICA_BREVE
from app.services.ai_base import PRESUPUESTO_IA_SEGUNDOS

settings = get_settings()
logger = logging.getLogger(__name__)

# Presupuesto mínimo que debe quedar libre para un segundo intento de
# generación cuando el primero incumple los controles de calidad.
_MARGEN_REINTENTO_SEGUNDOS = 12.0


def _normalizar_codigo(codigo) -> str:
    """Uniformiza el código de un desempeño ("3" y "03" son el mismo código)."""
    texto = str(codigo if codigo is not None else "").strip()
    return texto.zfill(2) if texto.isdigit() and len(texto) == 1 else texto


def _normalizar_nivel(nivel) -> str:
    """Uniformiza el nivel ("CRÍTICO" y "CRITICO" son el mismo nivel)."""
    return str(nivel or "").strip().upper().replace("Í", "I")


def _normalizar_enunciado(texto: str) -> str:
    """Normaliza un enunciado para detectar repeticiones reales."""
    texto = unicodedata.normalize("NFD", texto or "")
    texto = "".join(caracter for caracter in texto if unicodedata.category(caracter) != "Mn")
    return re.sub(r"\W+", "", texto.lower())


def _codigo_suelto(texto: str) -> Optional[str]:
    """Detecta un desempeño escrito solo como código ("03", "(3)") sin texto."""
    coincidencia = re.fullmatch(r"\(?\s*(\d{1,3})\s*\)?", texto or "")
    return coincidencia.group(1) if coincidencia else None


def _completar_tabla_respuestas(
    examen: dict,
    desempenos_por_codigo: Optional[dict[str, str]] = None,
    desempenos_por_nivel: Optional[dict[str, list[str]]] = None,
) -> None:
    """Garantiza una clave con desempeño, nivel y justificación por pregunta.

    En exámenes extensos el modelo puede truncar ``tabla_respuestas`` antes de
    completar todas las preguntas, o bien escribir en la columna "desempeno" el
    código suelto ("03") en vez de "(03) descripción". Se preserva el contenido
    pedagógico que sí generó y se completa cualquier fila ausente o degradada
    con los datos verificables de la pregunta, para que la clave nunca quede
    incompleta ni muestre códigos crudos.
    """
    preguntas = examen.get("preguntas") or []
    filas_originales = examen.get("tabla_respuestas") or []
    filas_por_numero = {
        str(fila.get("pregunta", "")).strip(): fila
        for fila in filas_originales
        if isinstance(fila, dict)
    }
    mapa = desempenos_por_codigo or {}
    por_nivel = desempenos_por_nivel or {}
    filas_completas = []

    for indice, pregunta in enumerate(preguntas, start=1):
        if not isinstance(pregunta, dict):
            continue

        numero = pregunta.get("numero", indice)
        fila = filas_por_numero.get(str(numero).strip(), {}).copy()
        fila["pregunta"] = numero
        codigo_desempeno = _normalizar_codigo(pregunta.get("desempeno_codigo"))

        # La columna "desempeno" puede venir vacía, con un código suelto o con
        # el texto genérico de un relleno anterior: en los tres casos se
        # sustituye por la descripción real del desempeño.
        actual = str(fila.get("desempeno") or "").strip()
        if not actual or _codigo_suelto(actual) or actual.startswith("Desempeño asociado"):
            nivel_fila = _normalizar_nivel(fila.get("nivel") or pregunta.get("nivel"))
            candidatos = por_nivel.get(nivel_fila) or []
            por_nivel_texto = candidatos[indice % len(candidatos)] if candidatos else ""
            fila["desempeno"] = (
                mapa.get(codigo_desempeno)
                or por_nivel_texto
                or (f"({codigo_desempeno}) Desempeño asociado a la pregunta." if codigo_desempeno
                    else "Desempeño asociado a la pregunta.")
            )

        if not str(fila.get("nivel") or "").strip():
            fila["nivel"] = pregunta.get("nivel", "")

        opcion_correcta = next(
            (
                opcion for opcion in pregunta.get("opciones") or []
                if isinstance(opcion, dict) and opcion.get("es_correcta")
            ),
            None,
        )
        respuesta_correcta = (
            fila.get("respuesta_correcta")
            or pregunta.get("respuesta_correcta")
            or (opcion_correcta or {}).get("letra", "")
        )
        fila["respuesta_correcta"] = respuesta_correcta

        if not str(fila.get("justificacion") or "").strip():
            texto_opcion = (opcion_correcta or {}).get("texto", "")
            detalle_opcion = f' («{texto_opcion}»)' if texto_opcion else ""
            fila["justificacion"] = (
                f"La alternativa {respuesta_correcta}{detalle_opcion} es correcta "
                "porque responde al enunciado según la información evaluada."
                if respuesta_correcta
                else "La respuesta se fundamenta en la información evaluada en el enunciado."
            )

        filas_completas.append(fila)

    examen["tabla_respuestas"] = filas_completas


def _validar_calidad_examen(
    examen: dict,
    cantidad: int,
    niveles_por_codigo: dict[str, str],
    niveles_programados: Optional[list[str]] = None,
    desempenos_por_nivel: Optional[dict[str, list[str]]] = None,
) -> tuple[list[str], list[str]]:
    """Repara lo reparable y devuelve (errores, advertencias).

    **Repara sobre el propio examen** (para no desperdiciar un intento):
    - un código de desempeño ausente o no seleccionado se sustituye por uno
      seleccionado del mismo nivel, en orden, y se avisa;
    - la etiqueta ``nivel`` se fuerza al nivel programado para esa posición
      (el prompt fija el orden) y se avisa, para que el docente pueda revisar
      si el enunciado de verdad lo exige.

    **Errores** (no se pueden reparar y obligan a regenerar): número de
    preguntas incorrecto, enunciados vacíos o repetidos.

    **Advertencias**: todo lo demás (nivel del desempeño no coincidente,
    pregunta CRÍTICA sin valoración explícita, reparaciones aplicadas).
    """
    preguntas = examen.get("preguntas") or []
    errores: list[str] = []
    advertencias: list[str] = []

    if len(preguntas) != cantidad:
        errores.append(f"Se recibieron {len(preguntas)} preguntas en lugar de {cantidad}.")

    marcadores_criticos = (
        "opin", "piensas", "consideras", "evalu", "valora", "juicio",
        "argument", "postura", "acuerdo", "desacuerdo", "perspectiva", "critica",
        "recomienda", "conveniente", "deberia", "merece", "importancia",
        "impacto", "eficaz", "efectiv", "convinc", "persuas", "util", "adecuad",
        "justifica", "sustenta", "califica", "mejor", "peor",
    )
    enunciados_vistos: set[str] = set()

    for indice, pregunta in enumerate(preguntas, start=1):
        if not isinstance(pregunta, dict):
            errores.append(f"La pregunta {indice} no tiene un formato válido.")
            continue

        numero = pregunta.get("numero", indice)
        enunciado = _normalizar_enunciado(str(pregunta.get("enunciado", "")))
        if not enunciado:
            errores.append(f"La pregunta {indice} no tiene enunciado.")
        elif enunciado in enunciados_vistos:
            errores.append(f"La pregunta {numero} está repetida.")
        else:
            enunciados_vistos.add(enunciado)

        nivel_programado = (
            niveles_programados[indice - 1]
            if niveles_programados and indice <= len(niveles_programados)
            else ""
        )
        nivel_recibido = _normalizar_nivel(pregunta.get("nivel"))

        # 1) Código de desempeño ausente o no seleccionado → se asigna uno
        #    seleccionado del nivel que corresponde a esa posición.
        codigo = _normalizar_codigo(pregunta.get("desempeno_codigo"))
        if codigo not in niveles_por_codigo:
            nivel_objetivo = nivel_programado or nivel_recibido
            reemplazo = (desempenos_por_nivel or {}).get(nivel_objetivo) or []
            if reemplazo:
                nuevo = reemplazo[indice % len(reemplazo)]
                pregunta["desempeno_codigo"] = _normalizar_codigo(
                    re.match(r"\(([^)]+)\)", nuevo).group(1)
                    if re.match(r"\(([^)]+)\)", nuevo)
                    else nuevo
                )
                advertencias.append(
                    f"La pregunta {numero} usaba un desempeño no seleccionado "
                    f"({codigo or 'sin código'}); se le asignó {nuevo} para el nivel {nivel_objetivo}."
                )
                codigo = pregunta["desempeno_codigo"]
            else:
                errores.append(
                    f"La pregunta {numero} usa un desempeño no seleccionado ({codigo or 'sin código'})."
                )

        # 2) Nivel de la pregunta distinto del programado para esa posición
        #    (p. ej. una INFERENCIAL en el bloque CRÍTICO 15-20) → se corrige
        #    la etiqueta y se avisa para que el docente revise el enunciado.
        if nivel_programado and nivel_recibido != nivel_programado:
            pregunta["nivel"] = nivel_programado
            advertencias.append(
                f"La pregunta {numero} estaba marcada como {nivel_recibido or 'SIN NIVEL'} "
                f"pero corresponde a nivel {nivel_programado}: se corrigió la etiqueta, "
                "revisa que el enunciado realmente exija ese nivel."
            )
            nivel_recibido = nivel_programado

        # 3) Nivel del desempeño seleccionado ≠ nivel de la pregunta.
        nivel_esperado = _normalizar_nivel(niveles_por_codigo.get(codigo, ""))
        if nivel_esperado and nivel_recibido and nivel_recibido != nivel_esperado:
            advertencias.append(
                f"La pregunta {numero} es de nivel {nivel_recibido}, distinto del nivel "
                f"{nivel_esperado} de su desempeño seleccionado ({codigo})."
            )

        # 4) Una CRÍTICA debe pedir juicio/valoración, no solo localizar o inferir.
        tiene_marcador_critico = any(marcador in enunciado for marcador in marcadores_criticos)
        # "¿Qué crees que es la intención...?” pide inferir, no valorar. En
        # cambio, “¿qué impacto crees...?” sí formula una evaluación crítica.
        if "crees" in enunciado and not any(
            marcador in enunciado
            for marcador in ("intencion", "sentido", "significado", "mensaje")
        ):
            tiene_marcador_critico = True
        if nivel_recibido == "CRITICO" and not tiene_marcador_critico:
            advertencias.append(
                f"La pregunta {numero} está marcada como CRÍTICO pero no solicita "
                "juicio, valoración, argumentación o toma de postura."
            )

    return errores, advertencias


class LectoSistemService:
    """Servicio para consultar desempeños y generar preguntas."""
    
    def __init__(self):
        pass
    
    async def get_grados(self, db: AsyncSession) -> list:
        """Obtiene todos los grados ordenados."""
        result = await db.execute(select(Grado).order_by(Grado.orden))
        return result.scalars().all()
    
    async def get_desempenos_por_grado(self, db: AsyncSession, grado_id: int) -> list:
        """Obtiene desempeños de un grado específico."""
        result = await db.execute(
            select(Desempeno)
            .where(Desempeno.grado_id == grado_id)
            .options(selectinload(Desempeno.capacidad))
        )
        return result.scalars().all()
    
    async def get_desempenos_por_capacidad(
        self, 
        db: AsyncSession, 
        grado_id: int, 
        tipo_capacidad: str
    ) -> list:
        """Obtiene desempeños de un grado y tipo de capacidad específicos."""
        result = await db.execute(
            select(Desempeno)
            .join(Capacidad)
            .where(
                Desempeno.grado_id == grado_id,
                Capacidad.tipo == tipo_capacidad
            )
            .options(selectinload(Desempeno.capacidad))
        )
        return result.scalars().all()
    
    async def get_grado_adyacente(
        self, 
        db: AsyncSession, 
        grado_id: int, 
        direccion: str = "inferior"
    ) -> Optional[Grado]:
        """Obtiene el grado inferior o superior al dado."""
        result = await db.execute(select(Grado).where(Grado.id == grado_id))
        grado_actual = result.scalars().first()
        
        if not grado_actual:
            return None
        
        target_orden = grado_actual.orden - 1 if direccion == "inferior" else grado_actual.orden + 1
        
        result = await db.execute(select(Grado).where(Grado.orden == target_orden))
        return result.scalars().first()
    
    def _build_prompt(
        self,
        desempeno: str,
        grado_nombre: str,
        capacidad: str,
        nivel_logro: str,
        cantidad: int,
        texto_base: Optional[str] = None
    ) -> str:
        """Construye el prompt para generar preguntas."""
        
        if texto_base:
            texto_instruccion = f"""
TEXTO BASE PARA LAS PREGUNTAS:
\"\"\"
{texto_base}
\"\"\"

Las preguntas deben basarse estrictamente en este texto. IMPORTANTE: En el campo 'lectura' del JSON responde EXACTAMENTE '[Texto base proporcionado]' y NO repitas el texto base para no exceder los límites de tokens.
"""
            texto_base_header = "Usa el siguiente texto proporcionado (en el campo 'lectura' del JSON responde '[Texto base proporcionado]'):"
            placeholder_lectura = "[Texto base proporcionado]"
        else:
            texto_instruccion = "El texto debe ser original, creativo, motivador y adecuado para la edad de estudiantes, con una extensión de 250-400 palabras. Temas sugeridos: Tradiciones peruanas, cuidado del medio ambiente, tecnología en la escuela, convivencia escolar."
            texto_base_header = "GENERA UN TEXTO NUEVO."
            placeholder_lectura = "Texto completo de la lectura..."
        
        prompt = f"""Eres un experto pedagogo peruano, especialista en Comprensión Lectora y Evaluación Formativa según el Currículo Nacional de Educación Básica (CNEB).
Tu misión es crear un instrumento de evaluación de alta calidad para estudiantes de **{grado_nombre}**.

**CONTEXTO EDUCATIVO:**
- Grado: {grado_nombre}
- Área: Comunicación / Comprensión Lectora
- Enfoque: Comunicativo y Textual
- Contexto: Regional Peruano (usa nombres, lugares y situaciones culturalmente relevantes)

**ESPECIFICACIONES DEL CONTENIDO:**
1. **TEXTO BASE:**
   {texto_base_header}
   {texto_instruccion}

2. **COMPETENCIA Y DESEMPEÑO A EVALUAR:**
   - Capacidad: {capacidad}
   - Desempeño Seleccionado: "{desempeno}"
   - Nivel de Logro Esperado: {nivel_logro}

3. **DISEÑO DE PREGUNTAS ({cantidad} preguntas):**
   - Todas las preguntas deben evaluar DIRECTAMENTE el desempeño indicado anteriormente.
   - Nivel de Dificultad: **{nivel_logro.upper()}**.
   - Tipo: Opción Múltiple con 4 alternativas (A, B, C, D).
   - Las alternativas deben ser plausibles. La respuesta correcta debe ser INEQUÍVOCA.

{NOTACION_MATEMATICA_BREVE}

**FORMATO DE SALIDA (JSON ESTRICTO):**
Responde ÚNICAMENTE con un JSON válido que siga esta estructura exacta, sin comentarios ni texto adicional:

{{
    "saludo": "¡Hola colega maestro! Aquí tienes una propuesta de evaluación contextualizada...",
    "examen": {{
        "titulo": "Título creativo y motivador para la lectura",
        "grado": "{grado_nombre}",
        "instrucciones": "Lee atentamente el siguiente texto y marca la alternativa correcta.",
        "lectura": "{placeholder_lectura}",
        "preguntas": [
            {{
                "numero": 1,
                "enunciado": "¿Pregunta clara y precisa?",
                "opciones": [
                    {{"letra": "A", "texto": "Alternativa 1", "es_correcta": false}},
                    {{"letra": "B", "texto": "Alternativa 2", "es_correcta": true}},
                    {{"letra": "C", "texto": "Alternativa 3", "es_correcta": false}},
                    {{"letra": "D", "texto": "Alternativa 4", "es_correcta": false}}
                ],
                "nivel": "Literal/Inferencial/Crítico",
                "desempeno_codigo": "Código o ID del desempeño (si aplica)"
            }}
        ],
        "tabla_respuestas": [
            {{
                "pregunta": 1,
                "desempeno": "Descripción del desempeño evaluado",
                "nivel": "Nivel cognitivo",
                "respuesta_correcta": "B",
                "justificacion": "Explicación breve de por qué es la respuesta correcta y por qué las demás son incorrectas"
            }}
        ]
    }}
}}
"""
        return prompt

    async def generar_preguntas_por_nivel(
        self,
        db: AsyncSession,
        grado_id: int,
        nivel_logro: str,
        cantidad: int = 3,
        texto_base: Optional[str] = None,
        modelo: str = "gemini"
    ) -> dict:
        """
        Genera preguntas según el nivel de logro del estudiante.
        """
        ai_service = ai_factory.get_service(modelo)
        
        if not ai_service.is_configured():
            raise ValueError(f"Configuración de API para {modelo} incompleta")
        
        result = await db.execute(select(Grado).where(Grado.id == grado_id))
        grado = result.scalars().first()
        
        if not grado:
            raise ValueError(f"Grado con id {grado_id} no encontrado")
        
        # Determinar qué desempeños usar según nivel
        nivel_map = {
            "pre_inicio": ("inferior", None),
            "inicio": (None, "literal"),
            "en_proceso": (None, "inferencial"),
            "logro_esperado": (None, "critico"),
            "logro_destacado": ("superior", None),
        }
        
        direccion, tipo_capacidad = nivel_map.get(nivel_logro.lower().replace(" ", "_"), (None, "literal"))
        
        # Obtener grado objetivo
        if direccion:
            grado_objetivo = await self.get_grado_adyacente(db, grado_id, direccion)
            if not grado_objetivo:
                # Si no hay grado adyacente, usar el actual
                grado_objetivo = grado
        else:
            grado_objetivo = grado
        
        # Obtener desempeños
        if tipo_capacidad:
            desempenos = await self.get_desempenos_por_capacidad(db, grado_objetivo.id, tipo_capacidad)
        else:
            desempenos = await self.get_desempenos_por_grado(db, grado_objetivo.id)
        
        if not desempenos:
            raise ValueError(f"No se encontraron desempeños para el nivel {nivel_logro}")
        
        # Usar el primer desempeño o uno aleatorio
        desempeno = random.choice(desempenos)
        
        # Obtener nombre de capacidad
        # Cargar la relación si no está cargada (lazy loading en async puede fallar, pero si usamos join arriba debería estar)
        # SQLAlchemy Async requiere cargar relaciones explícitamente o usar lazy='subquery' / 'selectin'.
        # Para evitar líos con lazy loading, asumiremos que se cargó o haremos una query separada si es necesario.
        # En este caso, accessing .capacidad direct might fail if not eager loaded.
        # Mejor opción simple: re-query o eager load en los métodos get.
        # Vamos a confiar en que la sesión está abierta y ver. SI falla, añadiremos selectinload.
        # Pero el objeto desempeño viene de un query.
        
        # CORRECCIÓN: Para evitar "Missing Greenlet" errors, vamos a cargar la capacidad explícitamente si es necesario
        # O mejor, en las queries de arriba usar joinedload.
        # Por ahora, usaré una lógica segura:
        capacidad_nombre = "Comprensión lectora"
        if desempeno.capacidad_id:
             result_cap = await db.execute(select(Capacidad).where(Capacidad.id == desempeno.capacidad_id))
             cap = result_cap.scalars().first()
             if cap:
                 capacidad_nombre = cap.nombre

        # Construir y enviar prompt
        prompt = self._build_prompt(
            desempeno=desempeno.descripcion,
            grado_nombre=grado.nombre,
            capacidad=capacidad_nombre,
            nivel_logro=nivel_logro,
            cantidad=cantidad,
            texto_base=texto_base
        )
        
        try:
            data = await ai_service.generate_structured_content(
                prompt,
                RespuestaLecto,
                max_output_tokens=min(65536, 8192 + cantidad * 1536),
            )
            examen = data.get("examen", {})
            _completar_tabla_respuestas(
                examen,
                {desempeno.codigo: f"({desempeno.codigo}) {desempeno.descripcion}"},
                {desempeno.capacidad.tipo.upper(): [
                    f"({desempeno.codigo}) {desempeno.descripcion}"
                ]} if desempeno.capacidad else None,
            )
            if texto_base:
                examen["lectura"] = texto_base
            preguntas = examen.get("preguntas", [])
            return {
                "grado": grado.nombre,
                "nivel_logro": nivel_logro,
                "desempeno_base": desempeno.descripcion,
                "capacidad": capacidad_nombre,
                "preguntas": preguntas,
                "total": len(preguntas),
                "examen": examen
            }
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Error al generar preguntas: {e}")
    
    async def generar_preguntas_por_desempenos(
        self,
        db: AsyncSession,
        grado_id: int,
        desempeno_ids: list[int],
        cantidad: int = 3,
        textos_base: Optional[list[dict]] = None,
        modelo: str = "gemini",
        nivel_dificultad: str = "intermedio",
        tipo_textual: Optional[str] = None,
        formato_textual: Optional[str] = None,
        cantidad_literal: Optional[int] = None,
        cantidad_inferencial: Optional[int] = None,
        cantidad_critico: Optional[int] = None
    ) -> dict:
        """
        Genera un examen completo basado en desempeños específicos seleccionados.
        """
        ai_service = ai_factory.get_service(modelo)
        
        if not ai_service.is_configured():
            raise ValueError(f"Configuración de API para {modelo} incompleta")
        
        if not desempeno_ids:
            raise ValueError("Debe seleccionar al menos un desempeño")
        
        result_grado = await db.execute(select(Grado).where(Grado.id == grado_id))
        grado = result_grado.scalars().first()
        
        if not grado:
            raise ValueError(f"Grado con id {grado_id} no encontrado")
        
        # Obtener desempeños seleccionados
        # Necesitamos cargar la capacidad también para el prompt
        from sqlalchemy.orm import selectinload
        result_desempenos = await db.execute(
            select(Desempeno)
            .where(Desempeno.id.in_(desempeno_ids))
            .options(selectinload(Desempeno.capacidad))
        )
        desempenos = result_desempenos.scalars().all()
        
        if not desempenos:
            raise ValueError("No se encontraron los desempeños seleccionados")
        
        # Construir lista de desempeños con nivel para el prompt
        desempenos_texto = "\n".join([
            f"{d.codigo}. {d.descripcion} ({d.capacidad.tipo.upper() if d.capacidad else 'GENERAL'})"
            for d in desempenos
        ])
        
        # Configurar instrucciones según nivel de dificultad
        dificultad_instrucciones = {
            "basico": """
**NIVEL DE DIFICULTAD: BÁSICO (Simple y sencillo)**
- Las preguntas deben ser DIRECTAS y de fácil comprensión
- Usar vocabulario simple y accesible para el grado
- Las alternativas incorrectas deben ser claramente distinguibles
- Enfocarse en la comprensión LITERAL del texto
- Evitar preguntas que requieran inferencias complejas
- La lectura debe ser corta y con estructura clara
- Las preguntas deben extraer información EXPLÍCITA del texto""",
            "intermedio": """
**NIVEL DE DIFICULTAD: INTERMEDIO (Demanda cognitiva media)**
- Las preguntas deben requerir comprensión y algo de análisis
- Incluir algunas preguntas inferenciales además de las literales
- Las alternativas incorrectas deben ser plausibles pero distinguibles
- La lectura puede tener complejidad moderada
- Algunas preguntas pueden requerir relacionar información del texto
- Equilibrar preguntas de diferentes niveles de complejidad""",
            "avanzado": """
**NIVEL DE DIFICULTAD: AVANZADO (Alta demanda cognitiva)**
- Las preguntas deben ser COMPLEJAS y desafiantes
- Priorizar preguntas INFERENCIALES y CRÍTICAS
- Incluir preguntas de reflexión y evaluación del contenido
- Las alternativas incorrectas deben ser PLAUSIBLES (distractores bien elaborados)
- La lectura puede tener mayor complejidad y extensión
- Requerir que el estudiante analice, sintetice y evalúe información
- Incluir preguntas que requieran establecer relaciones entre partes del texto
- Algunas preguntas pueden requerir conocimientos previos para contextualizare"""
        }
        
        instruccion_dificultad = dificultad_instrucciones.get(
            nivel_dificultad.lower(), 
            dificultad_instrucciones["intermedio"]
        )

        # Instrucciones de Diversidad Textual
        instruccion_diversidad = ""
        if tipo_textual or formato_textual:
            instruccion_diversidad = "\n**ESPECIFICACIONES DE DIVERSIDAD TEXTUAL (Muy Importante):**\n"
            
            if tipo_textual:
                tipos_info = {
                    "narrativo": "Narrativo: relata una secuencia de hechos (cuento, noticia, biografía, crónica).",
                    "descriptivo": "Descriptivo: caracteriza a personas, animales, objetos o lugares (guía turística, artículo enciclopédico).",
                    "instructivo": "Instructivo: brinda procedimientos o recomendaciones (receta, manual, ley).",
                    "argumentativo": "Argumentativo: defiende una opinión con razones (columna de opinión, ensayo).",
                    "expositivo": "Expositivo: explica fenómenos o conceptos (artículo de divulgación, informe)."
                }
                desc = tipos_info.get(tipo_textual.lower(), tipo_textual)
                instruccion_diversidad += f"- TIPO TEXTUAL REQUERIDO: {tipo_textual.upper()}. ({desc})\n"
                
            if formato_textual:
                formatos_info = {
                    "continuo": "Continuo: sucesión de oraciones estructuradas en párrafos.",
                    "discontinuo": "Discontinuo: organizado visualmente en columnas, tablas, cuadros, gráficos, etc.",
                    "mixto": "Mixto: presenta secciones continuas y otras discontinuas.",
                    "multiple": "Múltiple: incluye dos o más textos de fuentes diferentes."
                }
                desc = formatos_info.get(formato_textual.lower(), formato_textual)
                instruccion_diversidad += f"- FORMATO TEXTUAL REQUERIDO: {formato_textual.upper()}. ({desc})\n"
                
            if not textos_base:
                instruccion_diversidad += "Genera el texto de la lectura cumpliendo ESTRICTAMENTE estas características."
            else:
                instruccion_diversidad += "Asegúrate de que las preguntas y el análisis respeten estas características del texto base."
        
        # Instrucciones de distribución de preguntas
        instruccion_distribucion = ""
        if cantidad_literal is not None and cantidad_inferencial is not None and cantidad_critico is not None:
             instruccion_distribucion = f"""
**DISTRIBUCIÓN OBLIGATORIA DE PREGUNTAS (TOTAL {cantidad}):**
Debes generar EXACTAMENTE:
- {cantidad_literal} preguntas de nivel LITERAL.
- {cantidad_inferencial} preguntas de nivel INFERENCIAL.
- {cantidad_critico} preguntas de nivel CRÍTICO.

ORDEN OBLIGATORIO: numera primero las {cantidad_literal} preguntas LITERALES, luego las {cantidad_inferencial} INFERENCIALES y deja las preguntas {cantidad_literal + cantidad_inferencial + 1} a {cantidad} exclusivamente para nivel CRÍTICO. No repitas ningún enunciado, situación ni alternativa entre preguntas.

Una pregunta CRÍTICA debe solicitar explícitamente emitir una opinión o juicio, valorar, evaluar, argumentar, asumir una postura, recomendar o decidir a partir del texto; NO puede limitarse a localizar o inferir información.

Formula las preguntas CRÍTICAS como una valoración sustentada: pregunta qué opina/considera el lector, si una decisión fue adecuada, qué tan eficaz o convincente fue un argumento, qué impacto o consecuencias tuvo una acción, o qué postura recomienda y por qué. Evita etiquetar como CRÍTICAS preguntas que solo pidan explicar el sentido de una metáfora, identificar la intención del autor o inferir un mensaje: esas son INFERENCIALES si no solicitan además una valoración argumentada.

Selecciona de la lista de desempeños proporcionada aquellos que mejor se ajusten a cada nivel solicitado. Si no hay un desempeño explícito para un nivel, ADAPTA el enfoque de la pregunta para cumplir con el nivel exigido, pero manteniendo la coherencia con el grado.
"""
        
        # Texto(s) de lectura
        texto_lectura = ""
        if textos_base:
            if len(textos_base) == 1:
                t = textos_base[0]
                titulo_label = f'"{t["titulo"]}"' if t.get("titulo") else ""
                texto_lectura = f"""
TEXTO DE LECTURA {titulo_label}:
\"\"\"
{t["texto"]}
\"\"\"
IMPORTANTE: El texto de lectura ya fue proporcionado por el usuario. En el campo 'lectura' del JSON responde EXACTAMENTE '[Texto base proporcionado]'. NO repitas el texto de lectura en el JSON para no agotar el límite de tokens y concentrar toda la respuesta en la calidad pedagógica de las preguntas.
"""
            else:
                bloques = []
                for i, t in enumerate(textos_base, 1):
                    titulo_label = f': "{t["titulo"]}"' if t.get("titulo") else ""
                    bloques.append(f'TEXTO {i}{titulo_label}:\n"""\n{t["texto"]}\n"""')
                texto_lectura = "\nTEXTOS DE LECTURA PROPORCIONADOS (genera preguntas que cubran TODOS estos textos, distribuyendo las preguntas entre los textos):\n\n" + "\n\n".join(bloques) + "\nIMPORTANTE: En el campo 'lectura' del JSON, escribe EXACTAMENTE '[Ver textos proporcionados]'. Las preguntas deben referenciar el texto correspondiente en su enunciado si es necesario. NO repitas los textos en el JSON.\n"
        elif tipo_textual or formato_textual:
            texto_lectura = "Debes GENERAR un texto original que cumpla con el TIPO y FORMATO especificados arriba."

        instruccion_lectura_item = (
            "3. La lectura ya fue proporcionada por el usuario, por lo que en el campo 'lectura' del JSON debes escribir ÚNICAMENTE '[Texto base proporcionado]' (o '[Ver textos proporcionados]') sin duplicar el texto en la respuesta."
            if textos_base
            else "3. La 'lectura completa' o 'un fragmento de la lectura' que redactarás para que los estudiantes respondan las preguntas. SI SE ESPECIFICÓ UN FORMATO DISCONTINUO O MIXTO, REPRESENTA LOS ELEMENTOS VISUALES (TABLAS, GRÁFICOS) USANDO MARKDOWN O DESCRIBIÉNDOLOS CLARAMENTE."
        )
        placeholder_lectura = (
            ("[Ver textos proporcionados]" if len(textos_base) > 1 else "[Texto base proporcionado]")
            if textos_base
            else "texto de lectura completo o fragmento para las preguntas"
        )
        
        # Prompt basado en el formato del usuario.
        # No se le pide a la IA una sección de "Apellidos y Nombres"/"Fecha": ese
        # bloque lo agrega siempre generar_examen_word() (word_generator.py) al
        # exportar a Word, de forma independiente y para LectoSistem, MatSistem y
        # Generador por igual, así que pedírselo aquí a la IA era redundante.
        prompt = f"""Eres un experto en la elaboración de preguntas de comprensión lectora que trabaja con estudiantes de Perú. Utiliza el Currículo Nacional de Educación Básica (CNEB).

Primero saluda muy amablemente como un experto en la elaboración de preguntas de comprensión lectora.

El examen debe tener exactamente {cantidad} preguntas para estudiantes de {grado.nombre}.
{texto_lectura}
Usarás los siguientes desempeños que están enumerados e indican entre paréntesis si es de nivel LITERAL, INFERENCIAL o CRÍTICO:
{desempenos_texto}

{instruccion_dificultad}
{instruccion_diversidad}
{instruccion_distribucion}

El examen debe presentar:
1. Un 'título' motivador para el examen
2. 'Instrucciones precisas en un párrafo' para responder el examen
{instruccion_lectura_item}
4. Las preguntas con esquema de opción múltiple (4 alternativas A, B, C, D siendo una sola la correcta, en orden aleatorio)
5. Al final una 'tabla' indicando: los desempeños utilizados, número de pregunta, nivel (LITERAL/INFERENCIAL/CRÍTICO), alternativa correcta y una justificación breve indicando por qué es correcta. EN LA TABLA EL DESEMPEÑO DEBE TENER EL FORMATO EXACTO: "(CÓDIGO) DESCRIPCIÓN", por ejemplo: "(01) Obtiene información explícita...".
   La clave `tabla_respuestas` debe contener EXACTAMENTE {cantidad} filas: una para cada pregunta, del 1 al {cantidad}. Ninguna fila puede tener la `justificacion` vacía.

{NOTACION_MATEMATICA_BREVE}

IMPORTANTE: Responde ÚNICAMENTE con un JSON válido con esta estructura exacta:
{{
    "saludo": "texto del saludo amable del experto",
    "examen": {{
        "titulo": "título motivador del examen",
        "grado": "{grado.nombre}",
        "instrucciones": "instrucciones precisas para responder el examen",
        "lectura": "{placeholder_lectura}",
        "preguntas": [
            {{
                "numero": 1,
                "enunciado": "texto de la pregunta",
                "opciones": [
                    {{"letra": "A", "texto": "opción a", "es_correcta": false}},
                    {{"letra": "B", "texto": "opción b", "es_correcta": true}},
                    {{"letra": "C", "texto": "opción c", "es_correcta": false}},
                    {{"letra": "D", "texto": "opción d", "es_correcta": false}}
                ],
                "desempeno_codigo": "01",
                "nivel": "LITERAL|INFERENCIAL|CRITICO"
            }}
        ],
        "tabla_respuestas": [
            {{
                "pregunta": 1,
                "desempeno": "(01) Descripción o texto del desempeño...",
                "nivel": "LITERAL|INFERENCIAL|CRITICO",
                "respuesta_correcta": "A|B|C|D",
                "justificacion": "Breve explicación de por qué es correcta",
                "retroalimentacion_correcta": "2-3 oraciones motivadoras para el estudiante que respondió correctamente. Felicítalo y refuerza por qué esa opción es la correcta, referenciando el texto.",
                "retroalimentacion_incorrecta": "2-3 oraciones amables y motivadoras para el estudiante que se equivocó. Explica por qué su opción no es correcta y por qué la respuesta correcta sí lo es, referenciando el texto."
            }}
        ]
    }}
}}
"""
        
        # Datos de referencia para validar/reparar lo que devuelva el modelo.
        niveles_por_codigo = {
            _normalizar_codigo(d.codigo): _normalizar_nivel(d.capacidad.tipo if d.capacidad else "")
            for d in desempenos
        }
        mapa_desempenos = {d.codigo: f"({d.codigo}) {d.descripcion}" for d in desempenos}
        desempenos_por_nivel: dict[str, list[str]] = {}
        for d in desempenos:
            desempenos_por_nivel.setdefault(
                _normalizar_nivel(d.capacidad.tipo if d.capacidad else ""), []
            ).append(f"({d.codigo}) {d.descripcion}")

        # Orden obligatorio del prompt (literales, luego inferenciales, luego
        # críticos). Solo se exige si la distribución pedida cuadra con el total.
        niveles_programados: Optional[list[str]] = None
        if (
            None not in (cantidad_literal, cantidad_inferencial, cantidad_critico)
            and cantidad_literal + cantidad_inferencial + cantidad_critico == cantidad
        ):
            niveles_programados = (
                ["LITERAL"] * cantidad_literal
                + ["INFERENCIAL"] * cantidad_inferencial
                + ["CRITICO"] * cantidad_critico
            )

        # Un examen de 20 preguntas con su tabla de respuestas ronda los 12k
        # tokens de salida: con 8192 el JSON quedaba cortado a mitad de tabla.
        max_output_tokens = min(65536, 8192 + cantidad * 1536)
        deadline = time.monotonic() + PRESUPUESTO_IA_SEGUNDOS
        intentos = 2

        try:
            errores_calidad: list[str] = []
            advertencias_calidad: list[str] = []
            for intento in range(intentos):
                restante = deadline - time.monotonic()
                data = await ai_service.generate_structured_content(
                    prompt,
                    RespuestaLecto,
                    max_output_tokens=max_output_tokens,
                    timeout=max(5.0, restante),
                    deadline=deadline,
                )
                examen = data.get("examen", {})
                errores_calidad, advertencias_calidad = _validar_calidad_examen(
                    examen,
                    cantidad,
                    niveles_por_codigo,
                    niveles_programados,
                    desempenos_por_nivel,
                )
                if not errores_calidad:
                    logger.info(
                        "LectoSistem: examen válido en el intento %d/%d (%d advertencias de calidad)",
                        intento + 1, intentos, len(advertencias_calidad),
                    )
                    break
                logger.warning(
                    "LectoSistem: validación falló en el intento %d/%d (%d errores): %s",
                    intento + 1, intentos, len(errores_calidad),
                    "; ".join(errores_calidad)[:600],
                )
                if intento == 0 and (deadline - time.monotonic()) >= _MARGEN_REINTENTO_SEGUNDOS:
                    prompt += (
                        "\n\nVALIDACIÓN DEL INTENTO ANTERIOR FALLÓ. Genera un examen NUEVO y completo, "
                        "sin reutilizar preguntas. Corrige obligatoriamente estos problemas:\n- "
                        + "\n- ".join(errores_calidad)
                    )
                else:
                    raise ValueError(
                        "No se pudo generar un examen válido: "
                        + "; ".join(errores_calidad)
                        + ". Vuelve a intentarlo."
                    )

            _completar_tabla_respuestas(examen, mapa_desempenos, desempenos_por_nivel)
            if textos_base:
                lecturas_out = textos_base
                if len(textos_base) == 1:
                    examen["lectura"] = textos_base[0]["texto"]
                else:
                    parts = []
                    for i, t in enumerate(textos_base, 1):
                        titulo = t.get("titulo", "").strip()
                        header = f"TEXTO {i}: {titulo}" if titulo else f"TEXTO {i}"
                        parts.append(f"{'─' * 40}\n{header}\n{'─' * 40}\n{t['texto']}")
                    examen["lectura"] = "\n\n".join(parts)
            else:
                lectura_ia = examen.get("lectura", "")
                lecturas_out = [{"titulo": "", "texto": lectura_ia}] if lectura_ia else []

            return {
                "grado": grado.nombre,
                "desempenos_usados": desempenos_texto,
                "saludo": data.get("saludo", ""),
                "examen": examen,
                "lecturas": lecturas_out,
                "total_preguntas": len(examen.get("preguntas", [])),
                "advertencias_calidad": advertencias_calidad,
            }

        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Error al generar preguntas: {e}")


# Singleton instance
lectosistem_service = LectoSistemService()
