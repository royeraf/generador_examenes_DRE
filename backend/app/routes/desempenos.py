from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel, Field

from app.database import get_db
from app.models.db_models import Grado, Capacidad, Desempeno
from app.services.desempeno_service import desempeno_service
from app.services import file_service
from app.services.word_generator import generar_examen_word

router = APIRouter()


# Schemas
class GradoResponse(BaseModel):
    id: int
    nombre: str
    numero: int
    nivel: str
    
    class Config:
        from_attributes = True


class CapacidadResponse(BaseModel):
    id: int
    nombre: str
    tipo: str
    
    class Config:
        from_attributes = True


class DesempenoResponse(BaseModel):
    id: int
    codigo: str
    descripcion: str
    capacidad_tipo: Optional[str] = None
    
    class Config:
        from_attributes = True


class GenerarPreguntasRequest(BaseModel):
    grado_id: int = Field(..., description="ID del grado escolar")
    nivel_logro: str = Field(
        default="en_proceso", 
        description="Nivel de logro: pre_inicio, inicio, en_proceso, logro_esperado, logro_destacado"
    )
    nivel_dificultad: str = Field(
        default="intermedio",
        description="Nivel de dificultad: basico (simple, sencillo), intermedio (demanda cognitiva media), avanzado (complejo, alta demanda cognitiva)"
    )
    cantidad: int = Field(default=3, ge=1, le=10, description="Cantidad de preguntas a generar")
    texto_base: Optional[str] = Field(None, description="Texto de lectura para basar las preguntas")
    desempeno_ids: Optional[list[int]] = Field(None, description="IDs de desempeños seleccionados")
    modelo: Optional[str] = Field("gemini", description="Modelo de IA a usar: gemini o chatgpt")


# Endpoints
@router.get("/grados", response_model=list[GradoResponse])
async def listar_grados(db: Session = Depends(get_db)):
    """Lista todos los grados escolares disponibles."""
    grados = desempeno_service.get_grados(db)
    return grados


@router.get("/grados/{grado_id}/desempenos")
async def listar_desempenos_por_grado(
    grado_id: int,
    tipo_capacidad: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Lista los desempeños de un grado específico.
    
    - **grado_id**: ID del grado
    - **tipo_capacidad**: Filtrar por tipo (literal, inferencial, critico)
    """
    if tipo_capacidad:
        desempenos = desempeno_service.get_desempenos_por_capacidad(db, grado_id, tipo_capacidad)
    else:
        desempenos = desempeno_service.get_desempenos_por_grado(db, grado_id)
    
    return [
        {
            "id": d.id,
            "codigo": d.codigo,
            "descripcion": d.descripcion,
            "capacidad_tipo": d.capacidad.tipo if d.capacidad else None,
            "capacidad_nombre": d.capacidad.nombre if d.capacidad else None
        }
        for d in desempenos
    ]


@router.get("/niveles-logro")
async def listar_niveles_logro():
    """Lista los niveles de logro disponibles y su descripción."""
    return {
        "niveles": [
            {
                "id": "pre_inicio",
                "nombre": "Pre Inicio",
                "descripcion": "Desempeños del grado inferior (20%)",
                "recomendacion": "Estudiantes que aún no alcanzan los aprendizajes mínimos"
            },
            {
                "id": "inicio",
                "nombre": "Inicio",
                "descripcion": "Desempeños LITERALES del grado actual (20%)",
                "recomendacion": "Preguntas de nivel literal/explícito"
            },
            {
                "id": "en_proceso",
                "nombre": "En Proceso",
                "descripcion": "Desempeños INFERENCIALES del grado actual (20%)",
                "recomendacion": "Preguntas que requieren inferencia"
            },
            {
                "id": "logro_esperado",
                "nombre": "Logro Esperado",
                "descripcion": "Desempeños CRÍTICOS del grado actual (20%)",
                "recomendacion": "Preguntas de reflexión y evaluación crítica"
            },
            {
                "id": "logro_destacado",
                "nombre": "Logro Destacado",
                "descripcion": "Desempeños del grado superior (20%)",
                "recomendacion": "Desafíos para estudiantes avanzados"
            }
        ]
    }


@router.post("/generar")
async def generar_preguntas_lectura(
    request: GenerarPreguntasRequest,
    db: Session = Depends(get_db)
):
    """
    Genera preguntas de comprensión lectora basadas en desempeños seleccionados.
    """
    try:
        result = await desempeno_service.generar_preguntas_por_desempenos(
            db=db,
            grado_id=request.grado_id,
            desempeno_ids=request.desempeno_ids or [],
            cantidad=request.cantidad,
            texto_base=request.texto_base,
            modelo=request.modelo,
            nivel_dificultad=request.nivel_dificultad
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/capacidades")
async def listar_capacidades(db: Session = Depends(get_db)):
    """Lista todas las capacidades disponibles."""
    capacidades = db.query(Capacidad).all()
    return [
        {
            "id": c.id,
            "nombre": c.nombre,
            "tipo": c.tipo,
            "descripcion": c.descripcion
        }
        for c in capacidades
    ]


@router.post("/upload-texto")
async def upload_texto_base(files: list[UploadFile] = File(...)):
    """
    Sube uno o más archivos PDF o Word y extrae el texto para usarlo como base de preguntas.
    
    - **files**: Lista de archivos PDF (.pdf) o Word (.docx, .doc)
    
    Returns:
        - texto: Texto combinado extraído de todos los archivos
        - archivos: Lista con metadata de cada archivo procesado
        - total_palabras: Total de palabras en todos los archivos
    """
    textos = []
    archivos_metadata = []
    total_palabras = 0
    total_caracteres = 0
    
    for file in files:
        text, metadata = await file_service.extract_text_from_file(file)
        textos.append(f"=== {metadata['filename']} ===\n{text}")
        archivos_metadata.append(metadata)
        total_palabras += metadata['palabras']
        total_caracteres += metadata['caracteres']
    
    texto_combinado = "\n\n".join(textos)
    
    return {
        "texto": texto_combinado,
        "archivos": archivos_metadata,
        "total_archivos": len(archivos_metadata),
        "total_palabras": total_palabras,
        "total_caracteres": total_caracteres
    }


class ExamenWordRequest(BaseModel):
    """Schema para solicitar la generación del Word."""
    examen: dict = Field(..., description="Datos del examen generado")
    grado: str = Field(default="", description="Nombre del grado")


@router.post("/descargar-word")
async def descargar_examen_word(request: ExamenWordRequest):
    """
    Genera y descarga el examen en formato Word (.docx).
    
    - **examen**: Objeto con la estructura del examen generado
    - **grado**: Nombre del grado
    
    Returns:
        Archivo Word (.docx) para descargar
    """
    try:
        # Preparar datos para el generador
        data = {
            "examen": request.examen,
            "grado": request.grado
        }
        
        # Generar el documento Word
        word_buffer = generar_examen_word(data)
        
        # Generar nombre del archivo
        titulo = request.examen.get("titulo", "examen")
        filename = f"{titulo[:50].replace(' ', '_')}.docx"
        
        return StreamingResponse(
            word_buffer,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar el documento Word: {str(e)}")
