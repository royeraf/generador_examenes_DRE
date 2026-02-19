from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.docente_repository import docente_repository
from app.schemas.docente import DocenteCreate, DocenteUpdate
from app.models.docente import Docente
from app.core.security import get_password_hash, verify_password


class DocenteService:
    """Business logic for docentes."""

    def __init__(self):
        self.repository = docente_repository

    async def create_docente(
        self,
        db: AsyncSession,
        docente_in: DocenteCreate,
        creado_por_id: Optional[int] = None
    ) -> Docente:
        """Create new docente with hashed password."""
        existing = await self.repository.get_by_dni(db, docente_in.dni)
        if existing:
            raise ValueError("DNI ya registrado")

        obj_in_data = docente_in.model_dump()
        password = obj_in_data.pop("password")
        hashed_password = get_password_hash(password)
        obj_in_data["password_hash"] = hashed_password
        obj_in_data["creado_por_id"] = creado_por_id

        db_obj = Docente(**obj_in_data)
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def authenticate(
        self,
        db: AsyncSession,
        dni: str,
        password: str
    ) -> Optional[Docente]:
        """Authenticate docente."""
        docente = await self.repository.get_by_dni(db, dni)
        if not docente:
            return None
        if not verify_password(password, docente.password_hash):
            return None
        return docente

    async def update_docente(
        self,
        db: AsyncSession,
        docente_id: int,
        docente_in: DocenteUpdate
    ) -> Optional[Docente]:
        """Update docente."""
        docente = await self.repository.get(db, docente_id)
        if not docente:
            return None

        update_data = docente_in.model_dump(exclude_unset=True)
        if "password" in update_data:
            hashed_password = get_password_hash(update_data.pop("password"))
            update_data["password_hash"] = hashed_password

        return await self.repository.update(db, docente, update_data)

    async def delete_docente(
        self,
        db: AsyncSession,
        docente_id: int
    ) -> bool:
        """Delete docente by ID. Returns True if deleted, False if not found."""
        docente = await self.repository.get(db, docente_id)
        if not docente:
            return False
        await db.delete(docente)
        await db.flush()
        return True

    async def get_paginated_docentes(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 10
    ) -> tuple[List[Docente], int]:
        """Get paginated docentes and total count."""
        items = await self.repository.get_multi(db, skip=skip, limit=limit)
        total = await self.repository.count(db)
        return items, total


docente_service = DocenteService()
