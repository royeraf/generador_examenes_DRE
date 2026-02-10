from openai import AsyncOpenAI
import json
from typing import Optional

from app.core.config import get_settings
from app.models.pregunta import Pregunta, TipoPregunta, OpcionMultiple
from app.services.ai_base import AIService

settings = get_settings()


class ChatGPTService(AIService):
    """Service for generating questions using OpenAI ChatGPT API."""
    
    def __init__(self):
        if settings.openai_api_key:
            self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        else:
            self.client = None
            
    def is_configured(self) -> bool:
        return self.client is not None
        
    async def generate_content(self, prompt: str) -> str:
        """Generate content implementation for ChatGPT."""
        if not self.client:
            raise ValueError("OpenAI API key no configurada")
            
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system", 
                        "content": "Eres un experto en educación. Siempre respondes en formato JSON válido."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            return response.choices[0].message.content
        except Exception as e:
            raise ValueError(f"Error al generar contenido con ChatGPT: {e}")
    
    def _build_prompt(
        self, 
        competencias: list[dict], 
        cantidad: int, 
        tipo: str, 
        dificultad: str
    ) -> str:
        """Build the prompt for question generation."""
        
        competencias_texto = "\n".join([
            f"- {c.get('nombre', '')}: {c.get('descripcion', '')}" 
            for c in competencias
        ])
        
        prompt = f"""Eres un experto en educación y evaluación de estudiantes. 
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
        return prompt
    
    async def generar_preguntas(
        self,
        competencias: list[dict],
        cantidad: int = 5,
        tipo: str = "multiple",
        dificultad: str = "intermedio"
    ) -> list[Pregunta]:
        """Generate questions using OpenAI ChatGPT API."""
        
        prompt = self._build_prompt(competencias, cantidad, tipo, dificultad)
        response_text = await self.generate_content(prompt)
        
        try:
            data = json.loads(response_text)
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
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Error al parsear respuesta de ChatGPT: {e}")
        except Exception as e:
            raise ValueError(f"Error al generar preguntas con ChatGPT: {e}")


# Singleton instance
chatgpt_service = ChatGPTService()
