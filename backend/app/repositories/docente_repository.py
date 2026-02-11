from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.docente import Docente
from app.schemas.docente import DocenteCreate, DocenteUpdate
from app.repositories.base_repository import BaseRepository

class DocenteRepository(BaseRepository[Docente, DocenteCreate, DocenteUpdate]):
    """Docente-specific repository."""

    def __init__(self):
        super().__init__(Docente)
    
    async def get_by_dni(self, db: AsyncSession, dni: str) -> Optional[Docente]:
        """Get docente by DNI."""
        result = await db.execute(
            select(Docente).where(Docente.dni == dni)
        )
        return result.scalars().first()

docente_repository = DocenteRepository()
