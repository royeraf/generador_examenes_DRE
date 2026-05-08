from typing import TypeVar
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


async def get_or_404(db: AsyncSession, model: type[T], obj_id: int, detail: str | None = None) -> T:
    result = await db.execute(select(model).where(model.id == obj_id))
    obj = result.scalars().first()
    if not obj:
        raise HTTPException(status_code=404, detail=detail or f"{model.__name__} no encontrado")
    return obj
