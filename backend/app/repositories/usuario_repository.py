from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload

from app.models.usuario import Usuario
from app.repositories.base_repository import BaseRepository


class UsuarioRepository(BaseRepository[Usuario, None, None]):
    """Repositorio para el modelo Usuario."""

    def __init__(self):
        super().__init__(Usuario)

    def _base_query(self):
        return (
            select(Usuario)
            .options(
                selectinload(Usuario.rol),
                selectinload(Usuario.provincia),
                selectinload(Usuario.distrito),
                selectinload(Usuario.ugel),
                selectinload(Usuario.institucion_educativa),
            )
        )

    async def get(self, db: AsyncSession, id: int) -> Optional[Usuario]:
        result = await db.execute(self._base_query().where(Usuario.id == id))
        return result.scalars().first()

    async def get_by_dni(self, db: AsyncSession, dni: str) -> Optional[Usuario]:
        result = await db.execute(
            self._base_query().where(Usuario.dni == dni)
        )
        return result.scalars().first()

    async def get_by_login(self, db: AsyncSession, identifier: str) -> Optional[Usuario]:
        """Busca por DNI (solo staff)."""
        result = await db.execute(
            self._base_query().where(Usuario.dni == identifier)
        )
        return result.scalars().first()

    async def get_all(self, db: AsyncSession) -> List[Usuario]:
        result = await db.execute(self._base_query().order_by(Usuario.id))
        return result.scalars().all()

    async def get_paginated_with_search(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 10,
        search_query: Optional[str] = None,
        ugel_id: Optional[int] = None,
        institucion_educativa_id: Optional[int] = None,
    ) -> tuple[List[Usuario], int]:
        from sqlalchemy import func

        stmt = select(Usuario)

        if search_query:
            term = f"%{search_query}%"
            stmt = stmt.where(
                or_(
                    Usuario.dni.ilike(term),
                    Usuario.nombres.ilike(term),
                    Usuario.apellidos.ilike(term),
                )
            )

        if ugel_id is not None:
            stmt = stmt.where(Usuario.ugel_id == ugel_id)

        if institucion_educativa_id is not None:
            stmt = stmt.where(Usuario.institucion_educativa_id == institucion_educativa_id)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await db.execute(count_stmt)).scalar() or 0

        items_stmt = (
            stmt
            .options(
                selectinload(Usuario.rol),
                selectinload(Usuario.provincia),
                selectinload(Usuario.distrito),
                selectinload(Usuario.ugel),
                selectinload(Usuario.institucion_educativa),
            )
            .order_by(Usuario.id.desc())
            .offset(skip)
            .limit(limit)
        )
        items = (await db.execute(items_stmt)).scalars().all()

        return items, total

usuario_repository = UsuarioRepository()

# Alias de compatibilidad
docente_repository = usuario_repository
