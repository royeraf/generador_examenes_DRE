from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from app.database import get_db
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
def create_grado(grado: GradoCreate, db: Session = Depends(get_db)):
    db_grado = Grado(**grado.dict())
    db.add(db_grado)
    db.commit()
    db.refresh(db_grado)
    db.refresh(db_grado)
    return db_grado

@router.get("/grados", response_model=List[GradoResponse])
def get_grados(db: Session = Depends(get_db)):
    return db.query(Grado).order_by(Grado.orden).all()

@router.put("/grados/{grado_id}", response_model=GradoResponse)
def update_grado(grado_id: int, grado: GradoUpdate, db: Session = Depends(get_db)):
    db_grado = db.query(Grado).filter(Grado.id == grado_id).first()
    if not db_grado:
        raise HTTPException(status_code=404, detail="Grado not found")
    
    for key, value in grado.dict().items():
        setattr(db_grado, key, value)
    
    db.commit()
    db.refresh(db_grado)
    return db_grado

@router.delete("/grados/{grado_id}")
def delete_grado(grado_id: int, db: Session = Depends(get_db)):
    db_grado = db.query(Grado).filter(Grado.id == grado_id).first()
    if not db_grado:
        raise HTTPException(status_code=404, detail="Grado not found")
    
    db.delete(db_grado)
    db.commit()
    return {"message": "Grado deleted successfully"}


# --- Capacidad Endpoints ---

@router.post("/capacidades", response_model=CapacidadResponse)
def create_capacidad(capacidad: CapacidadCreate, db: Session = Depends(get_db)):
    db_capacidad = Capacidad(**capacidad.dict())
    db.add(db_capacidad)
    db.commit()
    db.refresh(db_capacidad)
    db.refresh(db_capacidad)
    return db_capacidad

@router.get("/capacidades", response_model=List[CapacidadResponse])
def get_capacidades(db: Session = Depends(get_db)):
    return db.query(Capacidad).all()

@router.put("/capacidades/{capacidad_id}", response_model=CapacidadResponse)
def update_capacidad(capacidad_id: int, capacidad: CapacidadUpdate, db: Session = Depends(get_db)):
    db_capacidad = db.query(Capacidad).filter(Capacidad.id == capacidad_id).first()
    if not db_capacidad:
        raise HTTPException(status_code=404, detail="Capacidad not found")
    
    for key, value in capacidad.dict().items():
        setattr(db_capacidad, key, value)
    
    db.commit()
    db.refresh(db_capacidad)
    return db_capacidad

@router.delete("/capacidades/{capacidad_id}")
def delete_capacidad(capacidad_id: int, db: Session = Depends(get_db)):
    db_capacidad = db.query(Capacidad).filter(Capacidad.id == capacidad_id).first()
    if not db_capacidad:
        raise HTTPException(status_code=404, detail="Capacidad not found")
    
    db.delete(db_capacidad)
    db.commit()
    return {"message": "Capacidad deleted successfully"}


# --- Desempeno Endpoints ---

@router.post("/desempenos", response_model=DesempenoResponse)
def create_desempeno(desempeno: DesempenoCreate, db: Session = Depends(get_db)):
    db_desempeno = Desempeno(**desempeno.dict())
    db.add(db_desempeno)
    db.commit()
    db.refresh(db_desempeno)
    return db_desempeno

@router.put("/desempenos/{desempeno_id}", response_model=DesempenoResponse)
def update_desempeno(desempeno_id: int, desempeno: DesempenoUpdate, db: Session = Depends(get_db)):
    db_desempeno = db.query(Desempeno).filter(Desempeno.id == desempeno_id).first()
    if not db_desempeno:
        raise HTTPException(status_code=404, detail="Desempeno not found")
    
    for key, value in desempeno.dict().items():
        setattr(db_desempeno, key, value)
    
    db.commit()
    db.refresh(db_desempeno)
    return db_desempeno

@router.delete("/desempenos/{desempeno_id}")
def delete_desempeno(desempeno_id: int, db: Session = Depends(get_db)):
    db_desempeno = db.query(Desempeno).filter(Desempeno.id == desempeno_id).first()
    if not db_desempeno:
        raise HTTPException(status_code=404, detail="Desempeno not found")
    
    db.delete(db_desempeno)
    db.commit()
    return {"message": "Desempeno deleted successfully"}
