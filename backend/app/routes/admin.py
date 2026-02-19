from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional

from app.core.database import get_db
from app.models.db_models import Grado, Capacidad, Desempeno
from app.models.docente import Docente as DocenteModel
from app.schemas.docente import Docente, DocenteAdminCreate, DocenteUpdate
from app.services.docente_service import docente_service
from app.api.dependencies import get_current_superuser

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


# --- Grado Endpoints ---

@router.post("/grados", response_model=GradoResponse)
async def create_grado(
    grado: GradoCreate,
    db: AsyncSession = Depends(get_db),
    _: DocenteModel = Depends(get_current_superuser)
):
    db_grado = Grado(**grado.dict())
    db.add(db_grado)
    await db.commit()
    await db.refresh(db_grado)
    return db_grado


@router.get("/grados", response_model=List[GradoResponse])
async def get_grados(
    db: AsyncSession = Depends(get_db),
    _: DocenteModel = Depends(get_current_superuser)
):
    result = await db.execute(select(Grado).order_by(Grado.orden))
    return result.scalars().all()


@router.put("/grados/{grado_id}", response_model=GradoResponse)
async def update_grado(
    grado_id: int,
    grado: GradoUpdate,
    db: AsyncSession = Depends(get_db),
    _: DocenteModel = Depends(get_current_superuser)
):
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
async def delete_grado(
    grado_id: int,
    db: AsyncSession = Depends(get_db),
    _: DocenteModel = Depends(get_current_superuser)
):
    result = await db.execute(select(Grado).where(Grado.id == grado_id))
    db_grado = result.scalars().first()

    if not db_grado:
        raise HTTPException(status_code=404, detail="Grado not found")

    await db.delete(db_grado)
    await db.commit()
    return {"message": "Grado deleted successfully"}


# --- Capacidad Endpoints ---

@router.post("/capacidades", response_model=CapacidadResponse)
async def create_capacidad(
    capacidad: CapacidadCreate,
    db: AsyncSession = Depends(get_db),
    _: DocenteModel = Depends(get_current_superuser)
):
    db_capacidad = Capacidad(**capacidad.dict())
    db.add(db_capacidad)
    await db.commit()
    await db.refresh(db_capacidad)
    return db_capacidad


@router.get("/capacidades", response_model=List[CapacidadResponse])
async def get_capacidades(
    db: AsyncSession = Depends(get_db),
    _: DocenteModel = Depends(get_current_superuser)
):
    result = await db.execute(select(Capacidad))
    return result.scalars().all()


@router.put("/capacidades/{capacidad_id}", response_model=CapacidadResponse)
async def update_capacidad(
    capacidad_id: int,
    capacidad: CapacidadUpdate,
    db: AsyncSession = Depends(get_db),
    _: DocenteModel = Depends(get_current_superuser)
):
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
async def delete_capacidad(
    capacidad_id: int,
    db: AsyncSession = Depends(get_db),
    _: DocenteModel = Depends(get_current_superuser)
):
    result = await db.execute(select(Capacidad).where(Capacidad.id == capacidad_id))
    db_capacidad = result.scalars().first()

    if not db_capacidad:
        raise HTTPException(status_code=404, detail="Capacidad not found")

    await db.delete(db_capacidad)
    await db.commit()
    return {"message": "Capacidad deleted successfully"}


# --- Desempeno Endpoints ---

@router.post("/desempenos", response_model=DesempenoResponse)
async def create_desempeno(
    desempeno: DesempenoCreate,
    db: AsyncSession = Depends(get_db),
    _: DocenteModel = Depends(get_current_superuser)
):
    db_desempeno = Desempeno(**desempeno.dict())
    db.add(db_desempeno)
    await db.commit()
    await db.refresh(db_desempeno)
    return db_desempeno


@router.put("/desempenos/{desempeno_id}", response_model=DesempenoResponse)
async def update_desempeno(
    desempeno_id: int,
    desempeno: DesempenoUpdate,
    db: AsyncSession = Depends(get_db),
    _: DocenteModel = Depends(get_current_superuser)
):
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
async def delete_desempeno(
    desempeno_id: int,
    db: AsyncSession = Depends(get_db),
    _: DocenteModel = Depends(get_current_superuser)
):
    result = await db.execute(select(Desempeno).where(Desempeno.id == desempeno_id))
    db_desempeno = result.scalars().first()

    if not db_desempeno:
        raise HTTPException(status_code=404, detail="Desempeno not found")

    await db.delete(db_desempeno)
    await db.commit()
    return {"message": "Desempeno deleted successfully"}


# --- Docentes (Usuarios) Endpoints ---

from app.schemas.pagination import PaginatedResponse
import math

@router.get("/docentes", response_model=PaginatedResponse[Docente])
async def list_docentes(
    page: int = 1,
    size: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: DocenteModel = Depends(get_current_superuser)
):
    """Listar usuarios con paginación."""
    skip = (page - 1) * size
    items, total = await docente_service.get_paginated_docentes(db, skip=skip, limit=size)
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size) if total > 0 else 0
    )


@router.post("/docentes", response_model=Docente, status_code=201)
async def create_docente(
    docente_in: DocenteAdminCreate,
    db: AsyncSession = Depends(get_db),
    current_user: DocenteModel = Depends(get_current_superuser)
):
    """Crear un nuevo usuario (solo admin)."""
    try:
        return await docente_service.create_docente(db, docente_in, creado_por_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/docentes/{docente_id}", response_model=Docente)
async def get_docente(
    docente_id: int,
    db: AsyncSession = Depends(get_db),
    _: DocenteModel = Depends(get_current_superuser)
):
    """Obtener un usuario por ID."""
    from app.repositories.docente_repository import docente_repository
    docente = await docente_repository.get(db, docente_id)
    if not docente:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return docente


@router.put("/docentes/{docente_id}", response_model=Docente)
async def update_docente(
    docente_id: int,
    docente_in: DocenteUpdate,
    db: AsyncSession = Depends(get_db),
    _: DocenteModel = Depends(get_current_superuser)
):
    """Actualizar un usuario."""
    docente = await docente_service.update_docente(db, docente_id, docente_in)
    if not docente:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return docente


@router.delete("/docentes/{docente_id}")
async def delete_docente(
    docente_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: DocenteModel = Depends(get_current_superuser)
):
    """Eliminar un usuario. No se puede eliminar a sí mismo."""
    if current_user.id == docente_id:
        raise HTTPException(status_code=400, detail="No puedes eliminar tu propio usuario")
    deleted = await docente_service.delete_docente(db, docente_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"message": "Usuario eliminado correctamente"}


@router.patch("/docentes/{docente_id}/toggle-active", response_model=Docente)
async def toggle_active(
    docente_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: DocenteModel = Depends(get_current_superuser)
):
    """Activar o desactivar un usuario."""
    if current_user.id == docente_id:
        raise HTTPException(status_code=400, detail="No puedes desactivar tu propio usuario")
    from app.repositories.docente_repository import docente_repository
    docente = await docente_repository.get(db, docente_id)
    if not docente:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    update_data = {"is_active": not docente.is_active}
    return await docente_repository.update(db, docente, update_data)
