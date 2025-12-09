from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class TipoPregunta(str, Enum):
    """Tipos de preguntas disponibles."""
    MULTIPLE = "multiple"
    VERDADERO_FALSO = "verdadero_falso"
    DESARROLLO = "desarrollo"
    COMPLETAR = "completar"


class OpcionMultiple(BaseModel):
    """Opción para preguntas de selección múltiple."""
    
    texto: str = Field(..., description="Texto de la opción")
    es_correcta: bool = Field(default=False, description="Indica si es la respuesta correcta")


class Pregunta(BaseModel):
    """Modelo para representar una pregunta generada."""
    
    enunciado: str = Field(..., description="Enunciado de la pregunta")
    tipo: TipoPregunta = Field(..., description="Tipo de pregunta")
    opciones: Optional[list[OpcionMultiple]] = Field(None, description="Opciones para preguntas múltiples")
    respuesta_correcta: Optional[str] = Field(None, description="Respuesta correcta")
    explicacion: Optional[str] = Field(None, description="Explicación de la respuesta")
    dificultad: str = Field(default="intermedio", description="Nivel de dificultad")
    competencia_asociada: Optional[str] = Field(None, description="Competencia que evalúa")


class PreguntasResponse(BaseModel):
    """Response model para las preguntas generadas."""
    
    preguntas: list[Pregunta] = Field(..., description="Lista de preguntas generadas")
    modelo_ia: str = Field(..., description="Modelo de IA usado (gemini/chatgpt)")
    total: int = Field(..., description="Total de preguntas generadas")
