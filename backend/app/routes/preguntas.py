from fastapi import APIRouter, HTTPException
from typing import Literal

from app.models.competencia import CompetenciaRequest
from app.models.rubrica import RubricaRequest
from app.models.pregunta import PreguntasResponse
from app.services.ai_factory import ai_factory

router = APIRouter()


@router.post("/generar", response_model=PreguntasResponse)
async def generar_preguntas(
    request: CompetenciaRequest,
    modelo: Literal["gemini", "chatgpt"] = "gemini"
):
    """
    Genera preguntas basadas en competencias usando IA.
    
    - **modelo**: Selecciona el modelo de IA a usar (gemini o chatgpt)
    - **competencias**: Lista de competencias a evaluar
    - **cantidad_preguntas**: Número de preguntas a generar (1-20)
    - **tipo_preguntas**: Tipo de preguntas (multiple, verdadero_falso, desarrollo, mixto)
    - **dificultad**: Nivel de dificultad (basico, intermedio, avanzado)
    """
    try:
        competencias_dict = [c.model_dump() for c in request.competencias]
        
        ai_service = ai_factory.get_service(modelo)
        
        preguntas = await ai_service.generar_preguntas(
            competencias=competencias_dict,
            cantidad=request.cantidad_preguntas,
            tipo=request.tipo_preguntas,
            dificultad=request.dificultad
        )
        
        return PreguntasResponse(
            preguntas=preguntas,
            modelo_ia=modelo,
            total=len(preguntas)
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.post("/generar-por-rubrica", response_model=PreguntasResponse)
async def generar_preguntas_por_rubrica(
    request: RubricaRequest,
    modelo: Literal["gemini", "chatgpt"] = "gemini"
):
    """
    Genera preguntas basadas en rúbricas de evaluación usando IA.
    
    - **modelo**: Selecciona el modelo de IA a usar (gemini o chatgpt)
    - **rubricas**: Lista de rúbricas a usar
    - **cantidad_preguntas**: Número de preguntas a generar (1-20)
    - **tipo_preguntas**: Tipo de preguntas (multiple, verdadero_falso, desarrollo, mixto)
    """
    try:
        # Convert rubrics to competencies format for the AI service
        competencias_dict = [
            {
                "nombre": r.criterio,
                "descripcion": f"{r.descripcion}. Niveles de logro: {', '.join(r.niveles)}"
            }
            for r in request.rubricas
        ]
        
        ai_service = ai_factory.get_service(modelo)
        
        preguntas = await ai_service.generar_preguntas(
            competencias=competencias_dict,
            cantidad=request.cantidad_preguntas,
            tipo=request.tipo_preguntas,
            dificultad="intermedio"
        )
        
        return PreguntasResponse(
            preguntas=preguntas,
            modelo_ia=modelo,
            total=len(preguntas)
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/modelos")
async def listar_modelos():
    """Lista los modelos de IA disponibles."""
    return {
        "modelos": ai_factory.get_available_services()
    }


@router.get("/tipos-preguntas")
async def listar_tipos_preguntas():
    """Lista los tipos de preguntas disponibles."""
    return {
        "tipos": [
            {"id": "multiple", "nombre": "Opción Múltiple", "descripcion": "4 alternativas, una correcta"}
        ],
        "dificultades": [
            {"id": "basico", "nombre": "Básico"},
            {"id": "intermedio", "nombre": "Intermedio"},
            {"id": "avanzado", "nombre": "Avanzado"}
        ]
    }
