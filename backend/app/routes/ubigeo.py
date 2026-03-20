from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.api.dependencies import get_current_active_user
from app.models.ubigeo import Provincia, Distrito
from app.schemas.ubigeo import ProvinciaResponse, DistritoResponse

router = APIRouter()


@router.get("/provincias", response_model=List[ProvinciaResponse])
async def get_provincias(
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_active_user),
):
    result = await db.execute(select(Provincia).order_by(Provincia.nombre))
    return result.scalars().all()


@router.get("/provincias/{provincia_id}/distritos", response_model=List[DistritoResponse])
async def get_distritos(
    provincia_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_active_user),
):
    result = await db.execute(
        select(Distrito)
        .where(Distrito.provincia_id == provincia_id)
        .order_by(Distrito.nombre)
    )
    return result.scalars().all()
