from pydantic import BaseModel, Field
from typing import Optional


class Rubrica(BaseModel):
    """Modelo para representar una rúbrica de evaluación."""
    
    criterio: str = Field(..., description="Criterio de evaluación")
    descripcion: str = Field(..., description="Descripción del criterio")
    niveles: list[str] = Field(
        default=["En inicio", "En proceso", "Logrado", "Destacado"],
        description="Niveles de logro"
    )
    peso: Optional[float] = Field(None, ge=0, le=100, description="Peso porcentual del criterio")


class RubricaRequest(BaseModel):
    """Request model para enviar rúbricas."""
    
    rubricas: list[Rubrica] = Field(..., description="Lista de rúbricas a usar")
    cantidad_preguntas: int = Field(default=5, ge=1, le=20, description="Cantidad de preguntas a generar")
    tipo_preguntas: str = Field(
        default="multiple", 
        description="Tipo de preguntas: multiple, verdadero_falso, desarrollo, mixto"
    )
    nivel_educativo: Optional[str] = Field(None, description="Nivel educativo objetivo")
