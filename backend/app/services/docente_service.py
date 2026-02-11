from typing import Optional
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
        docente_in: DocenteCreate
    ) -> Docente:
        """Create new docente with hashed password."""
        # Check if DNI exists
        existing = await self.repository.get_by_dni(db, docente_in.dni)
        if existing:
            raise ValueError("DNI already registered")

        # Hash password
        obj_in_data = docente_in.model_dump()
        password = obj_in_data.pop("password")
        hashed_password = get_password_hash(password)
        obj_in_data["password_hash"] = hashed_password

        # Create docente
        # We need to adapt because BaseRepository.create expects a Pydantic model
        # But we modified the data. So we might need to manually call repository.model(**obj_in_data)
        # Or construct a new Pydantic model.
        # However, BaseRepository.create takes `obj_in: CreateSchemaType`.
        # So providing a dict won't work perfectly with type hints, but at runtime it just calls `.dict()`.
        
        # Actually, let's just use the repository to create the object manually if needed, 
        # but better yet, let's subclass the CreateSchema to handle hashed_password if we were strict. 
        # Here I will just override the create method logic slightly by modifying the input dictionary and passing it to model constructor directly via repository if available, 
        # or just instantiate the model here and add it via session.
        
        # But to stick to repository pattern:
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

docente_service = DocenteService()
