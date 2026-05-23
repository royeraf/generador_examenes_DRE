from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, desc
from sqlalchemy.orm import selectinload

from app.models.estudiante import Estudiante


class EstudianteRepository:

    def _base_query(self):
        return (
            select(Estudiante)
            .options(
                selectinload(Estudiante.institucion_educativa),
                selectinload(Estudiante.distrito),
            )
        )

    async def get(self, db: AsyncSession, id: int) -> Optional[Estudiante]:
        result = await db.execute(self._base_query().where(Estudiante.id == id))
        return result.scalars().first()

    async def get_by_dni(self, db: AsyncSession, dni: str) -> Optional[Estudiante]:
        result = await db.execute(self._base_query().where(Estudiante.dni == dni))
        return result.scalars().first()

    async def get_by_codigo(self, db: AsyncSession, codigo: str) -> Optional[Estudiante]:
        result = await db.execute(
            self._base_query().where(Estudiante.codigo_estudiante == codigo)
        )
        return result.scalars().first()

    async def get_by_login(self, db: AsyncSession, identifier: str) -> Optional[Estudiante]:
        """Busca por DNI o código de estudiante."""
        result = await db.execute(
            self._base_query().where(
                or_(Estudiante.dni == identifier, Estudiante.codigo_estudiante == identifier)
            )
        )
        return result.scalars().first()

    async def get_ultimo_codigo(self, db: AsyncSession) -> Optional[str]:
        result = await db.execute(
            select(Estudiante.codigo_estudiante)
            .where(Estudiante.codigo_estudiante.like("EST%"))
            .order_by(desc(Estudiante.codigo_estudiante))
            .limit(1)
        )
        return result.scalar()


estudiante_repository = EstudianteRepository()
