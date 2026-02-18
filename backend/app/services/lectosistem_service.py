"""
Servicio para gestionar desempeños y generar preguntas de comprensión lectora.
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import json
import random

from app.models.db_models import Grado, Capacidad, Desempeno
from app.core.config import get_settings
from app.services.ai_factory import ai_factory

settings = get_settings()


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
        
        texto_instruccion = ""
        if texto_base:
            texto_instruccion = f"""
TEXTO BASE PARA LAS PREGUNTAS:
\"\"\"
{texto_base}
\"\"\"

Las preguntas deben basarse en este texto.
"""
        
        prompt = f"""Eres un experto pedagogo peruano, especialista en Comprensión Lectora y Evaluación Formativa según el Currículo Nacional de Educación Básica (CNEB).
Tu misión es crear un instrumento de evaluación de alta calidad para estudiantes de **{grado_nombre}**.

**CONTEXTO EDUCATIVO:**
- Grado: {grado_nombre}
- Área: Comunicación / Comprensión Lectora
- Enfoque: Comunicativo y Textual
- Contexto: Regional Peruano (usa nombres, lugares y situaciones culturalmente relevantes)

**ESPECIFICACIONES DEL CONTENIDO:**
1. **TEXTO BASE:**
   {f'Usa el siguiente texto proporcionado:' if texto_base else 'GENERA UN TEXTO NUEVO.'}
   {texto_instruccion if texto_base else 'El texto debe ser original, creativo, motivador y adecuado para la edad de estudiantes, con una extensión de 250-400 palabras. Temas sugeridos: Tradiciones peruanas, cuidado del medio ambiente, tecnología en la escuela, convivencia escolar.'}

2. **COMPETENCIA Y DESEMPEÑO A EVALUAR:**
   - Capacidad: {capacidad}
   - Desempeño Seleccionado: "{desempeno}"
   - Nivel de Logro Esperado: {nivel_logro}

3. **DISEÑO DE PREGUNTAS ({cantidad} preguntas):**
   - Todas las preguntas deben evaluar DIRECTAMENTE el desempeño indicado anteriormente.
   - Nivel de Dificultad: **{nivel_logro.upper()}**.
   - Tipo: Opción Múltiple con 4 alternativas (A, B, C, D).
   - Las alternativas deben ser plausibles. La respuesta correcta debe ser INEQUÍVOCA.
   
**FORMATO DE SALIDA (JSON ESTRICTO):**
Responde ÚNICAMENTE con un JSON válido que siga esta estructura exacta, sin comentarios ni texto adicional:

{{
    "saludo": "¡Hola colega maestro! Aquí tienes una propuesta de evaluación contextualizada...",
    "examen": {{
        "titulo": "Título creativo y motivador para la lectura",
        "grado": "{grado_nombre}",
        "instrucciones": "Lee atentamente el siguiente texto y marca la alternativa correcta.",
        "lectura": "Texto completo de la lectura...",
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
                "justificacion": "Explicación breve de por qué es la respuesta correcta"
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
            response_text = await ai_service.generate_content(prompt)
            response_text = ai_service.clean_json_response(response_text)
            
            try:
                data = json.loads(response_text)
            except json.JSONDecodeError as je:
                print(f"FAILED LECTOSISTEM (NIVEL) JSON: {response_text}")
                raise ValueError(f"Error al parsear respuesta JSON: {je}")
            
            return {
                "grado": grado.nombre,
                "nivel_logro": nivel_logro,
                "desempeno_base": desempeno.descripcion,
                "capacidad": capacidad_nombre,
                "preguntas": data.get("preguntas", []),
                "total": len(data.get("preguntas", []))
            }
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Error al parsear respuesta de {modelo}: {e}")
        except Exception as e:
            raise ValueError(f"Error al generar preguntas: {e}")
    
    async def generar_preguntas_por_desempenos(
        self,
        db: AsyncSession,
        grado_id: int,
        desempeno_ids: list[int],
        cantidad: int = 3,
        texto_base: Optional[str] = None,
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
                
            if not texto_base:
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

Selecciona de la lista de desempeños proporcionada aquellos que mejor se ajusten a cada nivel solicitado. Si no hay un desempeño explícito para un nivel, ADAPTA el enfoque de la pregunta para cumplir con el nivel exigido, pero manteniendo la coherencia con el grado.
"""
        
        # Texto de lectura
        texto_lectura = ""
        if texto_base:
            texto_lectura = f"""
TEXTO DE LECTURA:
\"\"\"
{texto_base}
\"\"\"
"""
        elif tipo_textual or formato_textual:
             texto_lectura = "Debes GENERAR un texto original que cumpla con el TIPO y FORMATO especificados arriba."

        
        # Prompt basado en el formato del usuario
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
2. Una sección para que los estudiantes ingresen sus 'Apellidos y Nombres' y la 'Fecha'
3. 'Instrucciones precisas en un párrafo' para responder el examen
4. La 'lectura completa' o 'un fragmento de la lectura' que utilizarás para que los estudiantes respondan las preguntas. SI SE ESPECIFICÓ UN FORMATO DISCONTINUO O MIXTO, REPRESENTA LOS ELEMENTOS VISUALES (TABLAS, GRÁFICOS) USANDO MARKDOWN O DESCRIBIÉNDOLOS CLARAMENTE.
5. Las preguntas con esquema de opción múltiple (4 alternativas A, B, C, D siendo una sola la correcta, en orden aleatorio)
6. Al final una 'tabla' indicando: los desempeños utilizados, número de pregunta, nivel (LITERAL/INFERENCIAL/CRÍTICO) y alternativa correcta. EN LA TABLA EL DESEMPEÑO DEBE TENER EL FORMATO EXACTO: "(CÓDIGO) DESCRIPCIÓN", por ejemplo: "(01) Obtiene información explícita..."

IMPORTANTE: Responde ÚNICAMENTE con un JSON válido con esta estructura exacta:
{{
    "saludo": "texto del saludo amable del experto",
    "examen": {{
        "titulo": "título motivador del examen",
        "grado": "{grado.nombre}",
        "instrucciones": "instrucciones precisas para responder el examen",
        "lectura": "texto de lectura completo o fragmento para las preguntas",
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
                "respuesta_correcta": "A|B|C|D"
            }}
        ]
    }}
}}
"""
        
        try:
            response_text = await ai_service.generate_content(prompt)
            response_text = ai_service.clean_json_response(response_text)
            
            try:
                data = json.loads(response_text)
            except json.JSONDecodeError as je:
                print(f"FAILED LECTOSISTEM (DESEMPEÑOS) JSON: {response_text}")
                raise ValueError(f"Error al parsear respuesta JSON de la IA: {je}")
            
            return {
                "grado": grado.nombre,
                "desempenos_usados": desempenos_texto,
                "saludo": data.get("saludo", ""),
                "examen": data.get("examen", {}),
                "total_preguntas": len(data.get("examen", {}).get("preguntas", []))
            }
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Error al parsear respuesta de {modelo}: {e}")
        except Exception as e:
            raise ValueError(f"Error al generar preguntas: {e}")


# Singleton instance
lectosistem_service = LectoSistemService()
