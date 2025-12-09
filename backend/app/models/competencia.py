from pydantic import BaseModel, Field
from typing import Optional


class Competencia(BaseModel):
    """Modelo para representar una competencia educativa."""
    
    nombre: str = Field(..., description="Nombre de la competencia")
    descripcion: str = Field(..., description="Descripción detallada de la competencia")
    nivel: Optional[str] = Field(None, description="Nivel educativo (primaria, secundaria, etc.)")
    area: Optional[str] = Field(None, description="Área curricular")


class CompetenciaRequest(BaseModel):
    """Request model para enviar competencias."""
    
    competencias: list[Competencia] = Field(..., description="Lista de competencias a evaluar")
    cantidad_preguntas: int = Field(default=5, ge=1, le=20, description="Cantidad de preguntas a generar")
    tipo_preguntas: str = Field(
        default="multiple", 
        description="Tipo de preguntas: multiple, verdadero_falso, desarrollo, mixto"
    )
    dificultad: str = Field(
        default="intermedio",
        description="Nivel de dificultad: basico, intermedio, avanzado"
    )
