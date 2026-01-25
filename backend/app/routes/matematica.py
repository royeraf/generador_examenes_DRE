"""
Rutas API para el módulo de Matemática (MatSistem).
Provee endpoints para consultar competencias, capacidades, estándares y desempeños.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from app.database import get_db
from app.models.db_models import (
    Grado,
    CompetenciaMatematica,
    CapacidadMatematica,
    EstandarMatematica,
    DesempenoMatematica
)


router = APIRouter()


# =============================================================================
# SCHEMAS
# =============================================================================

class CompetenciaMatResponse(BaseModel):
    """Esquema de respuesta para competencia matemática."""
    id: int
    codigo: int
    nombre: str
    descripcion: Optional[str] = None

    class Config:
        from_attributes = True


class CapacidadMatResponse(BaseModel):
    """Esquema de respuesta para capacidad matemática."""
    id: int
    orden: int
    nombre: str
    descripcion: Optional[str] = None
    competencia_id: int

    class Config:
        from_attributes = True


class CapacidadMatConCompetencia(CapacidadMatResponse):
    """Capacidad con información de la competencia."""
    competencia_codigo: int
    competencia_nombre: str


class EstandarMatResponse(BaseModel):
    """Esquema de respuesta para estándar matemático."""
    id: int
    descripcion: str
    ciclo: Optional[str] = None
    grado_id: int
    competencia_id: int

    class Config:
        from_attributes = True


class DesempenoMatResponse(BaseModel):
    """Esquema de respuesta para desempeño matemático."""
    id: int
    codigo: str
    descripcion: str
    grado_id: int
    capacidad_id: int

    class Config:
        from_attributes = True


class DesempenoMatCompleto(BaseModel):
    """Desempeño con información completa de capacidad y competencia."""
    id: int
    codigo: str
    descripcion: str
    grado_id: int
    capacidad_id: int
    capacidad_orden: int
    capacidad_nombre: str
    competencia_id: int
    competencia_codigo: int
    competencia_nombre: str

    class Config:
        from_attributes = True


class GradoMatResponse(BaseModel):
    """Esquema de respuesta para grado (incluye inicial)."""
    id: int
    nombre: str
    numero: int
    nivel: str
    orden: int

    class Config:
        from_attributes = True


class CurriculoMatematica(BaseModel):
    """Respuesta completa del currículo para un grado y competencia."""
    grado: GradoMatResponse
    competencia: CompetenciaMatResponse
    estandar: Optional[EstandarMatResponse] = None
    capacidades: List[CapacidadMatResponse]
    desempenos: List[DesempenoMatCompleto]


# =============================================================================
# ENDPOINTS - GRADOS
# =============================================================================

@router.get("/grados", response_model=List[GradoMatResponse])
def get_grados_matematica(db: Session = Depends(get_db)):
    """
    Obtiene todos los grados disponibles para Matemática.
    Incluye Inicial de 5 años, Primaria y Secundaria.
    """
    return db.query(Grado).order_by(Grado.orden).all()


# =============================================================================
# ENDPOINTS - COMPETENCIAS
# =============================================================================

@router.get("/competencias", response_model=List[CompetenciaMatResponse])
def get_competencias(db: Session = Depends(get_db)):
    """
    Obtiene las 4 competencias matemáticas.
    """
    return db.query(CompetenciaMatematica).order_by(CompetenciaMatematica.codigo).all()


@router.get("/competencias/{competencia_id}", response_model=CompetenciaMatResponse)
def get_competencia(competencia_id: int, db: Session = Depends(get_db)):
    """
    Obtiene una competencia específica por ID.
    """
    competencia = db.query(CompetenciaMatematica).filter(
        CompetenciaMatematica.id == competencia_id
    ).first()
    
    if not competencia:
        raise HTTPException(status_code=404, detail="Competencia no encontrada")
    
    return competencia


# =============================================================================
# ENDPOINTS - CAPACIDADES
# =============================================================================

@router.get("/capacidades", response_model=List[CapacidadMatConCompetencia])
def get_capacidades(
    competencia_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Obtiene las capacidades matemáticas.
    Opcionalmente filtra por competencia.
    """
    query = db.query(CapacidadMatematica).join(CompetenciaMatematica)
    
    if competencia_id:
        query = query.filter(CapacidadMatematica.competencia_id == competencia_id)
    
    capacidades = query.order_by(
        CompetenciaMatematica.codigo,
        CapacidadMatematica.orden
    ).all()
    
    result = []
    for cap in capacidades:
        result.append({
            "id": cap.id,
            "orden": cap.orden,
            "nombre": cap.nombre,
            "descripcion": cap.descripcion,
            "competencia_id": cap.competencia_id,
            "competencia_codigo": cap.competencia.codigo,
            "competencia_nombre": cap.competencia.nombre
        })
    
    return result


@router.get("/competencias/{competencia_id}/capacidades", response_model=List[CapacidadMatResponse])
def get_capacidades_por_competencia(competencia_id: int, db: Session = Depends(get_db)):
    """
    Obtiene las 4 capacidades de una competencia específica.
    """
    capacidades = db.query(CapacidadMatematica).filter(
        CapacidadMatematica.competencia_id == competencia_id
    ).order_by(CapacidadMatematica.orden).all()
    
    return capacidades


# =============================================================================
# ENDPOINTS - ESTÁNDARES
# =============================================================================

@router.get("/estandares", response_model=List[EstandarMatResponse])
def get_estandares(
    grado_id: Optional[int] = None,
    competencia_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Obtiene los estándares matemáticos.
    Opcionalmente filtra por grado y/o competencia.
    """
    query = db.query(EstandarMatematica)
    
    if grado_id:
        query = query.filter(EstandarMatematica.grado_id == grado_id)
    if competencia_id:
        query = query.filter(EstandarMatematica.competencia_id == competencia_id)
    
    return query.all()


@router.get("/grados/{grado_id}/competencias/{competencia_id}/estandar", response_model=Optional[EstandarMatResponse])
def get_estandar_especifico(grado_id: int, competencia_id: int, db: Session = Depends(get_db)):
    """
    Obtiene el estándar específico para un grado y competencia.
    """
    estandar = db.query(EstandarMatematica).filter(
        EstandarMatematica.grado_id == grado_id,
        EstandarMatematica.competencia_id == competencia_id
    ).first()
    
    return estandar


# =============================================================================
# ENDPOINTS - DESEMPEÑOS
# =============================================================================

@router.get("/desempenos", response_model=List[DesempenoMatCompleto])
def get_desempenos(
    grado_id: Optional[int] = None,
    competencia_id: Optional[int] = None,
    capacidad_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Obtiene los desempeños matemáticos con información completa.
    Opcionalmente filtra por grado, competencia y/o capacidad.
    """
    query = db.query(DesempenoMatematica).join(
        CapacidadMatematica
    ).join(
        CompetenciaMatematica
    )
    
    if grado_id:
        query = query.filter(DesempenoMatematica.grado_id == grado_id)
    if competencia_id:
        query = query.filter(CapacidadMatematica.competencia_id == competencia_id)
    if capacidad_id:
        query = query.filter(DesempenoMatematica.capacidad_id == capacidad_id)
    
    desempenos = query.order_by(
        CompetenciaMatematica.codigo,
        CapacidadMatematica.orden,
        DesempenoMatematica.codigo
    ).all()
    
    result = []
    for des in desempenos:
        cap = des.capacidad
        comp = cap.competencia
        result.append({
            "id": des.id,
            "codigo": des.codigo,
            "descripcion": des.descripcion,
            "grado_id": des.grado_id,
            "capacidad_id": des.capacidad_id,
            "capacidad_orden": cap.orden,
            "capacidad_nombre": cap.nombre,
            "competencia_id": comp.id,
            "competencia_codigo": comp.codigo,
            "competencia_nombre": comp.nombre
        })
    
    return result


@router.get("/grados/{grado_id}/desempenos", response_model=List[DesempenoMatCompleto])
def get_desempenos_por_grado(
    grado_id: int,
    competencia_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Obtiene los desempeños de un grado específico.
    Opcionalmente filtra por competencia.
    """
    return get_desempenos(grado_id=grado_id, competencia_id=competencia_id, db=db)


@router.get("/grados/{grado_id}/competencias/{competencia_id}/desempenos", response_model=List[DesempenoMatCompleto])
def get_desempenos_por_grado_y_competencia(
    grado_id: int,
    competencia_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene los desempeños de un grado y competencia específicos.
    """
    return get_desempenos(grado_id=grado_id, competencia_id=competencia_id, db=db)


# =============================================================================
# ENDPOINTS - CRUD DESEMPEÑOS
# =============================================================================

class DesempenoMatCreate(BaseModel):
    codigo: str
    descripcion: str
    grado_id: int
    capacidad_id: int


class DesempenoMatUpdate(BaseModel):
    codigo: Optional[str] = None
    descripcion: Optional[str] = None
    grado_id: Optional[int] = None
    capacidad_id: Optional[int] = None


@router.post("/desempenos", response_model=DesempenoMatResponse)
def create_desempeno(desempeno: DesempenoMatCreate, db: Session = Depends(get_db)):
    """
    Crea un nuevo desempeño matemático.
    """
    # Verificar si ya existe el código en ese grado (opcional, pero recomendado)
    existing = db.query(DesempenoMatematica).filter(
        DesempenoMatematica.codigo == desempeno.codigo,
        DesempenoMatematica.grado_id == desempeno.grado_id,
        DesempenoMatematica.capacidad_id == desempeno.capacidad_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Ya existe un desempeño con este código para el grado y capacidad seleccionados")

    db_desempeno = DesempenoMatematica(**desempeno.dict())
    db.add(db_desempeno)
    db.commit()
    db.refresh(db_desempeno)
    return db_desempeno


@router.put("/desempenos/{desempeno_id}", response_model=DesempenoMatResponse)
def update_desempeno(
    desempeno_id: int, 
    desempeno: DesempenoMatUpdate, 
    db: Session = Depends(get_db)
):
    """
    Actualiza un desempeño existente.
    """
    db_desempeno = db.query(DesempenoMatematica).filter(DesempenoMatematica.id == desempeno_id).first()
    if not db_desempeno:
        raise HTTPException(status_code=404, detail="Desempeño no encontrado")
    
    update_data = desempeno.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_desempeno, key, value)
    
    db.commit()
    db.refresh(db_desempeno)
    return db_desempeno


@router.delete("/desempenos/{desempeno_id}")
def delete_desempeno(desempeno_id: int, db: Session = Depends(get_db)):
    """
    Elimina un desempeño.
    """
    db_desempeno = db.query(DesempenoMatematica).filter(DesempenoMatematica.id == desempeno_id).first()
    if not db_desempeno:
        raise HTTPException(status_code=404, detail="Desempeño no encontrado")
    
    db.delete(db_desempeno)
    db.commit()
    return {"message": "Desempeño eliminado correctamente"}


# =============================================================================
# ENDPOINT - CURRÍCULO COMPLETO
# =============================================================================

@router.get("/grados/{grado_id}/competencias/{competencia_id}/curriculo", response_model=CurriculoMatematica)
def get_curriculo_completo(
    grado_id: int,
    competencia_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene el currículo completo para un grado y competencia:
    - Información del grado
    - Información de la competencia
    - Estándar de aprendizaje
    - Las 4 capacidades
    - Todos los desempeños
    """
    # Obtener grado
    grado = db.query(Grado).filter(Grado.id == grado_id).first()
    if not grado:
        raise HTTPException(status_code=404, detail="Grado no encontrado")
    
    # Obtener competencia
    competencia = db.query(CompetenciaMatematica).filter(
        CompetenciaMatematica.id == competencia_id
    ).first()
    if not competencia:
        raise HTTPException(status_code=404, detail="Competencia no encontrada")
    
    # Obtener estándar
    estandar = db.query(EstandarMatematica).filter(
        EstandarMatematica.grado_id == grado_id,
        EstandarMatematica.competencia_id == competencia_id
    ).first()
    
    # Obtener capacidades
    capacidades = db.query(CapacidadMatematica).filter(
        CapacidadMatematica.competencia_id == competencia_id
    ).order_by(CapacidadMatematica.orden).all()
    
    # Obtener desempeños
    desempenos_raw = get_desempenos(grado_id=grado_id, competencia_id=competencia_id, db=db)
    
    return {
        "grado": grado,
        "competencia": competencia,
        "estandar": estandar,
        "capacidades": capacidades,
        "desempenos": desempenos_raw
    }


# =============================================================================
# ENDPOINT - NIVELES DE LOGRO (para sistematización)
# =============================================================================

@router.get("/niveles-logro")
def get_niveles_logro_matematica():
    """
    Obtiene los niveles de logro para evaluación de matemáticas.
    Basado en el prompt de Matemática del MINEDU.
    """
    return {
        "niveles": [
            {
                "id": "preinicio",
                "nombre": "Pre-Inicio",
                "descripcion": "El estudiante no logra demostrar los aprendizajes esperados",
                "valor": 0,
                "color": "#ef4444"  # red-500
            },
            {
                "id": "inicio",
                "nombre": "Inicio",
                "descripcion": "El estudiante está empezando a desarrollar los aprendizajes previstos",
                "valor": 1,
                "color": "#f97316"  # orange-500
            },
            {
                "id": "proceso",
                "nombre": "En Proceso",
                "descripcion": "El estudiante está en camino de lograr los aprendizajes previstos",
                "valor": 2,
                "color": "#eab308"  # yellow-500
            },
            {
                "id": "logro_esperado",
                "nombre": "Logro Esperado",
                "descripcion": "El estudiante evidencia el logro de los aprendizajes previstos",
                "valor": 3,
                "color": "#22c55e"  # green-500
            },
            {
                "id": "logro_destacado",
                "nombre": "Logro Destacado",
                "descripcion": "El estudiante evidencia un nivel superior a lo esperado",
                "valor": 4,
                "color": "#3b82f6"  # blue-500
            }
        ]
    }


# =============================================================================
# ENDPOINT - GENERACIÓN DE EXAMEN DE MATEMÁTICA
# =============================================================================

class GenerarExamenMatRequest(BaseModel):
    """Esquema para solicitar generación de examen de matemática."""
    grado_id: int
    competencia_id: int
    desempeno_ids: List[int]
    cantidad: int = 3
    situacion_base: Optional[str] = None
    modelo: str = "gemini"


@router.post("/generar")
async def generar_examen_matematica(
    request: GenerarExamenMatRequest,
    db: Session = Depends(get_db)
):
    """
    Genera un examen de matemática con situación problemática integradora.
    
    A diferencia del generador de comprensión lectora, este crea:
    - Una SITUACIÓN PROBLEMÁTICA (no texto de lectura)
    - Preguntas que requieren razonamiento matemático
    - Criterios de evaluación por capacidad
    - Formato según el modelo MateJony del MINEDU
    """
    from app.services.matematica_service import matematica_service
    
    try:
        resultado = await matematica_service.generar_examen_matematica(
            db=db,
            grado_id=request.grado_id,
            competencia_id=request.competencia_id,
            desempeno_ids=request.desempeno_ids,
            cantidad=request.cantidad,
            situacion_base=request.situacion_base,
            modelo=request.modelo
        )
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar examen: {str(e)}")

