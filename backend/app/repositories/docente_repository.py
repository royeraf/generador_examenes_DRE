from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.docente import Docente
from app.schemas.docente import DocenteCreate, DocenteUpdate
from app.repositories.base_repository import BaseRepository


class DocenteRepository(BaseRepository[Docente, DocenteCreate, DocenteUpdate]):
    """Docente-specific repository."""

    def __init__(self):
        super().__init__(Docente)

    async def get(self, db, id: int) -> Optional[Docente]:
        result = await db.execute(
            select(Docente)
            .options(selectinload(Docente.provincia), selectinload(Docente.distrito))
            .where(Docente.id == id)
        )
        return result.scalars().first()

    async def get_by_dni(self, db: AsyncSession, dni: str) -> Optional[Docente]:
        """Get docente by DNI."""
        result = await db.execute(
            select(Docente)
            .options(selectinload(Docente.provincia), selectinload(Docente.distrito))
            .where(Docente.dni == dni)
        )
        return result.scalars().first()

    async def get_all(self, db: AsyncSession) -> List[Docente]:
        """Get all docentes ordered by id."""
        result = await db.execute(
            select(Docente)
            .options(selectinload(Docente.provincia), selectinload(Docente.distrito))
            .order_by(Docente.id)
        )
        return result.scalars().all()

    async def get_paginated_with_search(
        self, db: AsyncSession, skip: int = 0, limit: int = 10, search_query: Optional[str] = None
    ) -> tuple[List[Docente], int]:
        from sqlalchemy import or_, func

        stmt = select(Docente)

        if search_query:
            search_term = f"%{search_query}%"
            stmt = stmt.where(
                or_(
                    Docente.dni.ilike(search_term),
                    Docente.nombres.ilike(search_term),
                    Docente.apellidos.ilike(search_term)
                )
            )

        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await db.execute(count_stmt)).scalar() or 0

        # Get items with eager loading
        items_stmt = (
            stmt
            .options(selectinload(Docente.provincia), selectinload(Docente.distrito))
            .order_by(Docente.id.desc())
            .offset(skip)
            .limit(limit)
        )
        items = (await db.execute(items_stmt)).scalars().all()

        return items, total


docente_repository = DocenteRepository()
