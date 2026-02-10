from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional

from app.core.database import get_db
from app.models.db_models import Grado, Capacidad, Desempeno

router = APIRouter()

# --- Schemas ---

class GradoSchema(BaseModel):
    nombre: str
    numero: int
    nivel: str
    orden: int

    class Config:
        from_attributes = True

class GradoCreate(GradoSchema):
    pass

class GradoUpdate(GradoSchema):
    pass

class GradoResponse(GradoSchema):
    id: int


class CapacidadSchema(BaseModel):
    nombre: str
    tipo: str
    descripcion: Optional[str] = None

    class Config:
        from_attributes = True

class CapacidadCreate(CapacidadSchema):
    pass

class CapacidadUpdate(CapacidadSchema):
    pass

class CapacidadResponse(CapacidadSchema):
    id: int


class DesempenoSchema(BaseModel):
    codigo: str
    descripcion: str
    grado_id: int
    capacidad_id: int

    class Config:
        from_attributes = True

class DesempenoCreate(DesempenoSchema):
    pass

class DesempenoUpdate(DesempenoSchema):
    pass

class DesempenoResponse(DesempenoSchema):
    id: int
    # Optional nested info could be added if needed


# --- Grado Endpoints ---

@router.post("/grados", response_model=GradoResponse)
async def create_grado(grado: GradoCreate, db: AsyncSession = Depends(get_db)):
    db_grado = Grado(**grado.dict())
    db.add(db_grado)
    await db.commit()
    await db.refresh(db_grado)
    return db_grado

@router.get("/grados", response_model=List[GradoResponse])
async def get_grados(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Grado).order_by(Grado.orden))
    return result.scalars().all()

@router.put("/grados/{grado_id}", response_model=GradoResponse)
async def update_grado(grado_id: int, grado: GradoUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Grado).where(Grado.id == grado_id))
    db_grado = result.scalars().first()
    
    if not db_grado:
        raise HTTPException(status_code=404, detail="Grado not found")
    
    for key, value in grado.dict().items():
        setattr(db_grado, key, value)
    
    await db.commit()
    await db.refresh(db_grado)
    return db_grado

@router.delete("/grados/{grado_id}")
async def delete_grado(grado_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Grado).where(Grado.id == grado_id))
    db_grado = result.scalars().first()
    
    if not db_grado:
        raise HTTPException(status_code=404, detail="Grado not found")
    
    await db.delete(db_grado)
    await db.commit()
    return {"message": "Grado deleted successfully"}


# --- Capacidad Endpoints ---

@router.post("/capacidades", response_model=CapacidadResponse)
async def create_capacidad(capacidad: CapacidadCreate, db: AsyncSession = Depends(get_db)):
    db_capacidad = Capacidad(**capacidad.dict())
    db.add(db_capacidad)
    await db.commit()
    await db.refresh(db_capacidad)
    return db_capacidad

@router.get("/capacidades", response_model=List[CapacidadResponse])
async def get_capacidades(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Capacidad))
    return result.scalars().all()

@router.put("/capacidades/{capacidad_id}", response_model=CapacidadResponse)
async def update_capacidad(capacidad_id: int, capacidad: CapacidadUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Capacidad).where(Capacidad.id == capacidad_id))
    db_capacidad = result.scalars().first()
    
    if not db_capacidad:
        raise HTTPException(status_code=404, detail="Capacidad not found")
    
    for key, value in capacidad.dict().items():
        setattr(db_capacidad, key, value)
    
    await db.commit()
    await db.refresh(db_capacidad)
    return db_capacidad

@router.delete("/capacidades/{capacidad_id}")
async def delete_capacidad(capacidad_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Capacidad).where(Capacidad.id == capacidad_id))
    db_capacidad = result.scalars().first()
    
    if not db_capacidad:
        raise HTTPException(status_code=404, detail="Capacidad not found")
    
    await db.delete(db_capacidad)
    await db.commit()
    return {"message": "Capacidad deleted successfully"}


# --- Desempeno Endpoints ---

@router.post("/desempenos", response_model=DesempenoResponse)
async def create_desempeno(desempeno: DesempenoCreate, db: AsyncSession = Depends(get_db)):
    db_desempeno = Desempeno(**desempeno.dict())
    db.add(db_desempeno)
    await db.commit()
    await db.refresh(db_desempeno)
    return db_desempeno

@router.put("/desempenos/{desempeno_id}", response_model=DesempenoResponse)
async def update_desempeno(desempeno_id: int, desempeno: DesempenoUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Desempeno).where(Desempeno.id == desempeno_id))
    db_desempeno = result.scalars().first()
    
    if not db_desempeno:
        raise HTTPException(status_code=404, detail="Desempeno not found")
    
    for key, value in desempeno.dict().items():
        setattr(db_desempeno, key, value)
    
    await db.commit()
    await db.refresh(db_desempeno)
    return db_desempeno

@router.delete("/desempenos/{desempeno_id}")
async def delete_desempeno(desempeno_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Desempeno).where(Desempeno.id == desempeno_id))
    db_desempeno = result.scalars().first()
    
    if not db_desempeno:
        raise HTTPException(status_code=404, detail="Desempeno not found")
    
    await db.delete(db_desempeno)
    await db.commit()
    return {"message": "Desempeno deleted successfully"}
