"""
Rutas API para el módulo de Matemática (MatSistem).
Provee endpoints para consultar competencias, capacidades, estándares y desempeños.
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload
from pydantic import BaseModel
from typing import List, Optional

from app.core.database import get_db
from app.models.db_models import (
    Grado,
    CompetenciaMatematica,
    CapacidadMatematica,
    EstandarMatematica,
    DesempenoMatematica,
    ExamenMatematica
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
async def get_grados_matematica(db: AsyncSession = Depends(get_db)):
    """
    Obtiene todos los grados disponibles para Matemática.
    Incluye Inicial de 5 años, Primaria y Secundaria.
    """
    result = await db.execute(select(Grado).order_by(Grado.orden))
    return result.scalars().all()


# =============================================================================
# ENDPOINTS - COMPETENCIAS
# =============================================================================

@router.get("/competencias", response_model=List[CompetenciaMatResponse])
async def get_competencias(db: AsyncSession = Depends(get_db)):
    """
    Obtiene las 4 competencias matemáticas.
    """
    result = await db.execute(select(CompetenciaMatematica).order_by(CompetenciaMatematica.codigo))
    return result.scalars().all()


@router.get("/competencias/{competencia_id}", response_model=CompetenciaMatResponse)
async def get_competencia(competencia_id: int, db: AsyncSession = Depends(get_db)):
    """
    Obtiene una competencia específica por ID.
    """
    result = await db.execute(select(CompetenciaMatematica).where(
        CompetenciaMatematica.id == competencia_id
    ))
    competencia = result.scalars().first()
    
    if not competencia:
        raise HTTPException(status_code=404, detail="Competencia no encontrada")
    
    return competencia


# =============================================================================
# ENDPOINTS - CAPACIDADES
# =============================================================================

@router.get("/capacidades", response_model=List[CapacidadMatConCompetencia])
async def get_capacidades(
    competencia_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene las capacidades matemáticas.
    Opcionalmente filtra por competencia.
    """
    query = select(CapacidadMatematica).join(CompetenciaMatematica).options(
        selectinload(CapacidadMatematica.competencia)
    )
    
    if competencia_id:
        query = query.where(CapacidadMatematica.competencia_id == competencia_id)
    
    query = query.order_by(
        CompetenciaMatematica.codigo,
        CapacidadMatematica.orden
    )
    
    result = await db.execute(query)
    capacidades = result.scalars().all()
    
    result_list = []
    for cap in capacidades:
        result_list.append({
            "id": cap.id,
            "orden": cap.orden,
            "nombre": cap.nombre,
            "descripcion": cap.descripcion,
            "competencia_id": cap.competencia_id,
            "competencia_codigo": cap.competencia.codigo,
            "competencia_nombre": cap.competencia.nombre
        })
    
    return result_list


@router.get("/competencias/{competencia_id}/capacidades", response_model=List[CapacidadMatResponse])
async def get_capacidades_por_competencia(competencia_id: int, db: AsyncSession = Depends(get_db)):
    """
    Obtiene las 4 capacidades de una competencia específica.
    """
    result = await db.execute(
        select(CapacidadMatematica)
        .where(CapacidadMatematica.competencia_id == competencia_id)
        .order_by(CapacidadMatematica.orden)
    )
    
    return result.scalars().all()


# =============================================================================
# ENDPOINTS - ESTÁNDARES
# =============================================================================

@router.get("/estandares", response_model=List[EstandarMatResponse])
async def get_estandares(
    grado_id: Optional[int] = None,
    competencia_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene los estándares matemáticos.
    Opcionalmente filtra por grado y/o competencia.
    """
    query = select(EstandarMatematica)
    
    if grado_id:
        query = query.where(EstandarMatematica.grado_id == grado_id)
    if competencia_id:
        query = query.where(EstandarMatematica.competencia_id == competencia_id)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/grados/{grado_id}/competencias/{competencia_id}/estandar", response_model=Optional[EstandarMatResponse])
async def get_estandar_especifico(grado_id: int, competencia_id: int, db: AsyncSession = Depends(get_db)):
    """
    Obtiene el estándar específico para un grado y competencia.
    """
    result = await db.execute(select(EstandarMatematica).where(
        EstandarMatematica.grado_id == grado_id,
        EstandarMatematica.competencia_id == competencia_id
    ))
    
    return result.scalars().first()


# =============================================================================
# ENDPOINTS - DESEMPEÑOS
# =============================================================================

@router.get("/desempenos", response_model=List[DesempenoMatCompleto])
async def get_desempenos(
    grado_id: Optional[int] = None,
    competencia_id: Optional[int] = None,
    capacidad_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene los desempeños matemáticos con información completa.
    Opcionalmente filtra por grado, competencia y/o capacidad.
    """
    # Necesitamos cargar relaciones para construir la respuesta completa
    query = select(DesempenoMatematica).options(
        selectinload(DesempenoMatematica.capacidad).selectinload(CapacidadMatematica.competencia)
    )

    if grado_id:
        query = query.where(DesempenoMatematica.grado_id == grado_id)
    if competencia_id:
        # Filtrar por competencia a través de la capacidad
        query = query.join(CapacidadMatematica).where(CapacidadMatematica.competencia_id == competencia_id)
    if capacidad_id:
        query = query.where(DesempenoMatematica.capacidad_id == capacidad_id)

    # Ordenar por competencia, capacidad y desempeño
    query = query.order_by(DesempenoMatematica.codigo)
    
    result = await db.execute(query)
    desempenos = result.scalars().all()
    
    result_list = []
    for des in desempenos:
        # Con selectinload, estas propiedades están disponibles sin I/O adicional
        cap = des.capacidad
        comp = cap.competencia
        result_list.append({
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
    
    return result_list


@router.get("/grados/{grado_id}/desempenos", response_model=List[DesempenoMatCompleto])
async def get_desempenos_por_grado(
    grado_id: int,
    competencia_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene los desempeños de un grado específico.
    Opcionalmente filtra por competencia.
    """
    return await get_desempenos(grado_id=grado_id, competencia_id=competencia_id, db=db)


@router.get("/grados/{grado_id}/competencias/{competencia_id}/desempenos", response_model=List[DesempenoMatCompleto])
async def get_desempenos_por_grado_y_competencia(
    grado_id: int,
    competencia_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene los desempeños de un grado y competencia específicos.
    """
    return await get_desempenos(grado_id=grado_id, competencia_id=competencia_id, db=db)


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
async def create_desempeno(desempeno: DesempenoMatCreate, db: AsyncSession = Depends(get_db)):
    """
    Crea un nuevo desempeño matemático.
    """
    # Verificar si ya existe el código en ese grado (opcional, pero recomendado)
    result = await db.execute(select(DesempenoMatematica).where(
        DesempenoMatematica.codigo == desempeno.codigo,
        DesempenoMatematica.grado_id == desempeno.grado_id,
        DesempenoMatematica.capacidad_id == desempeno.capacidad_id
    ))
    existing = result.scalars().first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Ya existe un desempeño con este código para el grado y capacidad seleccionados")

    db_desempeno = DesempenoMatematica(**desempeno.dict())
    db.add(db_desempeno)
    await db.commit()
    await db.refresh(db_desempeno)
    return db_desempeno


@router.put("/desempenos/{desempeno_id}", response_model=DesempenoMatResponse)
async def update_desempeno(
    desempeno_id: int, 
    desempeno: DesempenoMatUpdate, 
    db: AsyncSession = Depends(get_db)
):
    """
    Actualiza un desempeño existente.
    """
    result = await db.execute(select(DesempenoMatematica).where(DesempenoMatematica.id == desempeno_id))
    db_desempeno = result.scalars().first()
    
    if not db_desempeno:
        raise HTTPException(status_code=404, detail="Desempeño no encontrado")
    
    update_data = desempeno.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_desempeno, key, value)
    
    await db.commit()
    await db.refresh(db_desempeno)
    return db_desempeno


@router.delete("/desempenos/{desempeno_id}")
async def delete_desempeno(desempeno_id: int, db: AsyncSession = Depends(get_db)):
    """
    Elimina un desempeño.
    """
    result = await db.execute(select(DesempenoMatematica).where(DesempenoMatematica.id == desempeno_id))
    db_desempeno = result.scalars().first()
    
    if not db_desempeno:
        raise HTTPException(status_code=404, detail="Desempeño no encontrado")
    
    await db.delete(db_desempeno)
    await db.commit()
    return {"message": "Desempeño eliminado correctamente"}


# =============================================================================
# ENDPOINT - CURRÍCULO COMPLETO
# =============================================================================

@router.get("/grados/{grado_id}/competencias/{competencia_id}/curriculo", response_model=CurriculoMatematica)
async def get_curriculo_completo(
    grado_id: int,
    competencia_id: int,
    db: AsyncSession = Depends(get_db)
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
    result_grado = await db.execute(select(Grado).where(Grado.id == grado_id))
    grado = result_grado.scalars().first()
    if not grado:
        raise HTTPException(status_code=404, detail="Grado no encontrado")
    
    # Obtener competencia
    result_comp = await db.execute(select(CompetenciaMatematica).where(
        CompetenciaMatematica.id == competencia_id
    ))
    competencia = result_comp.scalars().first()
    if not competencia:
        raise HTTPException(status_code=404, detail="Competencia no encontrada")
    
    # Obtener estándar
    result_est = await db.execute(select(EstandarMatematica).where(
        EstandarMatematica.grado_id == grado_id,
        EstandarMatematica.competencia_id == competencia_id
    ))
    estandar = result_est.scalars().first()
    
    # Obtener capacidades
    result_cap = await db.execute(
        select(CapacidadMatematica)
        .where(CapacidadMatematica.competencia_id == competencia_id)
        .order_by(CapacidadMatematica.orden)
    )
    capacidades = result_cap.scalars().all()
    
    # Obtener desempeños
    desempenos_raw = await get_desempenos(grado_id=grado_id, competencia_id=competencia_id, db=db)
    
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
async def get_niveles_logro_matematica():
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
                "color": "#ef4444"
            },
            {
                "id": "inicio",
                "nombre": "Inicio",
                "descripcion": "El estudiante está empezando a desarrollar los aprendizajes previstos",
                "valor": 1,
                "color": "#f97316"
            },
            {
                "id": "proceso",
                "nombre": "En Proceso",
                "descripcion": "El estudiante está en camino de lograr los aprendizajes previstos",
                "valor": 2,
                "color": "#eab308"
            },
            {
                "id": "logro_esperado",
                "nombre": "Logro Esperado",
                "descripcion": "El estudiante evidencia el logro de los aprendizajes previstos",
                "valor": 3,
                "color": "#22c55e"
            },
            {
                "id": "logro_destacado",
                "nombre": "Logro Destacado",
                "descripcion": "El estudiante evidencia un nivel superior a lo esperado",
                "valor": 4,
                "color": "#3b82f6"
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
    nivel_dificultad: str = "intermedio"  # basico, intermedio, avanzado


@router.post("/generar")
async def generar_examen_matematica(
    request: GenerarExamenMatRequest,
    req: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Genera un examen de matemática con situación problemática integradora.
    Si el request incluye un token JWT válido, el exámen se guarda automáticamente.
    """
    from app.services.matsistem_service import matsistem_service

    try:
        resultado = await matsistem_service.generar_examen_matematica(
            db=db,
            grado_id=request.grado_id,
            competencia_id=request.competencia_id,
            desempeno_ids=request.desempeno_ids,
            cantidad=request.cantidad,
            situacion_base=request.situacion_base,
            modelo=request.modelo,
            nivel_dificultad=request.nivel_dificultad
        )

        return resultado
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar examen: {str(e)}")
