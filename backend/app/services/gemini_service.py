import google.generativeai as genai
import json
from typing import Optional

from app.core.config import get_settings
from app.models.pregunta import Pregunta, TipoPregunta, OpcionMultiple
from app.services.ai_base import AIService

settings = get_settings()


class GeminiService(AIService):
    """Service for generating questions using Google Gemini API."""
    
    def __init__(self):
        self.model_name = 'gemini-2.5-flash'
        if settings.google_api_key:
            genai.configure(api_key=settings.google_api_key)
            self.model = genai.GenerativeModel(self.model_name)
        else:
            self.model = None
            
    def is_configured(self) -> bool:
        return self.model is not None
        
    async def generate_content(self, prompt: str) -> str:
        """Generate content implementation for Gemini."""
        if not self.model:
            raise ValueError("Google API key no configurada")
            
        try:
            response = await self.model.generate_content_async(prompt)
            return response.text
        except Exception as e:
            raise ValueError(f"Error al generar contenido con Gemini: {e}")
    
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
        """Generate questions using Gemini API."""
        
        prompt = self._build_prompt(competencias, cantidad, tipo, dificultad)
        response_text = await self.generate_content(prompt)
        
        try:
            response_text = self.clean_json_response(response_text)
            
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
            raise ValueError(f"Error al parsear respuesta de Gemini: {e}")
        except Exception as e:
            raise ValueError(f"Error al procesar preguntas con Gemini: {e}")


# Singleton instance
gemini_service = GeminiService()
