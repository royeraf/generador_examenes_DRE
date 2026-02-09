"""
Servicio para gestionar desempeños y generar preguntas de comprensión lectora.
"""
from typing import Optional
from sqlalchemy.orm import Session
import json

from app.models.db_models import Grado, Capacidad, Desempeno
from app.config import get_settings
from app.services.ai_factory import ai_factory

settings = get_settings()


class DesempenoService:
    """Servicio para consultar desempeños y generar preguntas."""
    
    def __init__(self):
        pass
    
    def get_grados(self, db: Session) -> list:
        """Obtiene todos los grados ordenados."""
        return db.query(Grado).order_by(Grado.orden).all()
    
    def get_desempenos_por_grado(self, db: Session, grado_id: int) -> list:
        """Obtiene desempeños de un grado específico."""
        return db.query(Desempeno).filter(
            Desempeno.grado_id == grado_id
        ).all()
    
    def get_desempenos_por_capacidad(
        self, 
        db: Session, 
        grado_id: int, 
        tipo_capacidad: str
    ) -> list:
        """Obtiene desempeños de un grado y tipo de capacidad específicos."""
        return db.query(Desempeno).join(Capacidad).filter(
            Desempeno.grado_id == grado_id,
            Capacidad.tipo == tipo_capacidad
        ).all()
    
    def get_grado_adyacente(
        self, 
        db: Session, 
        grado_id: int, 
        direccion: str = "inferior"
    ) -> Optional[Grado]:
        """Obtiene el grado inferior o superior al dado."""
        grado_actual = db.query(Grado).filter(Grado.id == grado_id).first()
        if not grado_actual:
            return None
        
        if direccion == "inferior":
            return db.query(Grado).filter(
                Grado.orden == grado_actual.orden - 1
            ).first()
        else:
            return db.query(Grado).filter(
                Grado.orden == grado_actual.orden + 1
            ).first()
    
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
        
        prompt = f"""Eres un experto en evaluación educativa y comprensión lectora del Perú.
Genera exactamente {cantidad} preguntas de comprensión lectora para estudiantes de {grado_nombre}.

DESEMPEÑO A EVALUAR:
{desempeno}

CAPACIDAD: {capacidad}
NIVEL DE LOGRO: {nivel_logro}
{texto_instruccion}
INSTRUCCIONES:
1. Las preguntas deben evaluar específicamente el desempeño indicado
2. El nivel de dificultad debe corresponder al nivel de logro ({nivel_logro})
3. Genera preguntas de opción múltiple (4 alternativas A, B, C, D)
4. Incluye la respuesta correcta y una breve explicación

IMPORTANTE: Responde ÚNICAMENTE con un JSON válido con esta estructura exacta:
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
            "respuesta_correcta": "texto de la respuesta",
            "explicacion": "explicación breve",
            "desempeno_evaluado": "{desempeno[:100]}..."
        }}
    ]
}}
"""
        return prompt

    async def generar_preguntas_por_nivel(
        self,
        db: Session,
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
        
        grado = db.query(Grado).filter(Grado.id == grado_id).first()
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
            grado_objetivo = self.get_grado_adyacente(db, grado_id, direccion)
            if not grado_objetivo:
                # Si no hay grado adyacente, usar el actual
                grado_objetivo = grado
        else:
            grado_objetivo = grado
        
        # Obtener desempeños
        if tipo_capacidad:
            desempenos = self.get_desempenos_por_capacidad(db, grado_objetivo.id, tipo_capacidad)
        else:
            desempenos = self.get_desempenos_por_grado(db, grado_objetivo.id)
        
        if not desempenos:
            raise ValueError(f"No se encontraron desempeños para el nivel {nivel_logro}")
        
        # Usar el primer desempeño o uno aleatorio
        import random
        desempeno = random.choice(desempenos)
        
        # Obtener nombre de capacidad
        capacidad_nombre = desempeno.capacidad.nombre if desempeno.capacidad else "Comprensión lectora"
        
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
            
            data = json.loads(response_text)
            
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
        db: Session,
        grado_id: int,
        desempeno_ids: list[int],
        cantidad: int = 3,
        texto_base: Optional[str] = None,
        modelo: str = "gemini",
        nivel_dificultad: str = "intermedio"
    ) -> dict:
        """
        Genera un examen completo basado en desempeños específicos seleccionados.
        
        Args:
            nivel_dificultad: 'basico' (simple), 'intermedio' (demanda media), 'avanzado' (alta demanda cognitiva)
        """
        ai_service = ai_factory.get_service(modelo)
        
        if not ai_service.is_configured():
            raise ValueError(f"Configuración de API para {modelo} incompleta")
        
        if not desempeno_ids:
            raise ValueError("Debe seleccionar al menos un desempeño")
        
        grado = db.query(Grado).filter(Grado.id == grado_id).first()
        if not grado:
            raise ValueError(f"Grado con id {grado_id} no encontrado")
        
        # Obtener desempeños seleccionados
        desempenos = db.query(Desempeno).filter(Desempeno.id.in_(desempeno_ids)).all()
        
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
        
        # Texto de lectura
        texto_lectura = ""
        if texto_base:
            texto_lectura = f"""
TEXTO DE LECTURA:
\"\"\"
{texto_base}
\"\"\"
"""
        
        # Prompt basado en el formato del usuario
        prompt = f"""Eres un experto en la elaboración de preguntas de comprensión lectora que trabaja con estudiantes de Perú. Piensa 10 veces antes de responder.

Primero saluda muy amablemente como un experto en la elaboración de preguntas de comprensión lectora.

El examen debe tener exactamente {cantidad} preguntas para estudiantes de {grado.nombre}.
{texto_lectura}
Usarás los siguientes desempeños que están enumerados e indican entre paréntesis si es de nivel LITERAL, INFERENCIAL o CRÍTICO:
{desempenos_texto}

{instruccion_dificultad}

El examen debe presentar:
1. Un 'título' motivador para el examen
2. Una sección para que los estudiantes ingresen sus 'Apellidos y Nombres' y la 'Fecha'
3. 'Instrucciones precisas en un párrafo' para responder el examen
4. La 'lectura completa' o 'un fragmento de la lectura' que utilizarás para que los estudiantes respondan las preguntas
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
            
            data = json.loads(response_text)
            
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
desempeno_service = DesempenoService()

