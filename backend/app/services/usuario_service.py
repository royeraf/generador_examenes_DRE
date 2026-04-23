from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.repositories.usuario_repository import usuario_repository
from app.schemas.usuario import UsuarioAdminCreate, UsuarioUpdate
from app.models.usuario import Usuario
from app.models.db_models import Rol
from app.models.enums import RolCodigo
from app.core.security import get_password_hash, verify_password
from app.core.permissions import puede_crear_rol


class UsuarioService:
    """Lógica de negocio para usuarios."""

    def __init__(self):
        self.repository = usuario_repository

    async def _generar_codigo_estudiante(self, db: AsyncSession) -> str:
        """Genera el siguiente código de estudiante (EST0001, EST0002, ...)."""
        ultimo = await self.repository.get_ultimo_codigo_estudiante(db)
        if ultimo:
            try:
                numero = int(ultimo[3:]) + 1
            except ValueError:
                numero = 1
        else:
            numero = 1
        return f"EST{numero:04d}"

    async def _get_rol_id(self, db: AsyncSession, rol_codigo: str) -> int:
        """Obtiene el ID del rol por su código."""
        result = await db.execute(select(Rol).where(Rol.codigo == rol_codigo))
        rol = result.scalars().first()
        if not rol:
            raise ValueError(f"Rol '{rol_codigo}' no encontrado")
        return rol.id

    async def create_usuario(
        self,
        db: AsyncSession,
        usuario_in: UsuarioAdminCreate,
        creado_por_id: Optional[int] = None,
        creado_por_rol: Optional[str] = None,
    ) -> Usuario:
        """Crea un nuevo usuario. Valida jerarquía de roles si se pasa creado_por_rol."""
        if creado_por_rol and not puede_crear_rol(creado_por_rol, usuario_in.rol_codigo):
            raise ValueError(f"No tienes permiso para crear usuarios con rol '{usuario_in.rol_codigo}'")

        # Verificar DNI duplicado si se provee
        if usuario_in.dni:
            existing = await self.repository.get_by_dni(db, usuario_in.dni)
            if existing:
                raise ValueError("DNI ya registrado")

        obj_data = usuario_in.model_dump()
        password = obj_data.pop("password")
        rol_codigo = obj_data.pop("rol_codigo")

        obj_data["password_hash"] = get_password_hash(password)
        obj_data["rol_id"] = await self._get_rol_id(db, rol_codigo)
        obj_data["creado_por_id"] = creado_por_id

        # Generar código de estudiante si es necesario
        if rol_codigo == RolCodigo.ESTUDIANTE and not obj_data.get("dni"):
            obj_data["codigo_estudiante"] = await self._generar_codigo_estudiante(db)

        db_obj = Usuario(**obj_data)
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def authenticate(
        self,
        db: AsyncSession,
        identifier: str,
        password: str,
    ) -> Optional[Usuario]:
        """Autentica por DNI o código de estudiante."""
        usuario = await self.repository.get_by_login(db, identifier)
        if not usuario:
            return None
        if not verify_password(password, usuario.password_hash):
            return None
        return usuario

    async def update_usuario(
        self,
        db: AsyncSession,
        usuario_id: int,
        usuario_in: UsuarioUpdate,
    ) -> Optional[Usuario]:
        usuario = await self.repository.get(db, usuario_id)
        if not usuario:
            return None

        update_data = usuario_in.model_dump(exclude_unset=True)
        if "password" in update_data:
            update_data["password_hash"] = get_password_hash(update_data.pop("password"))
        if "rol_codigo" in update_data:
            update_data["rol_id"] = await self._get_rol_id(db, update_data.pop("rol_codigo"))

        return await self.repository.update(db, usuario, update_data)

    async def delete_usuario(self, db: AsyncSession, usuario_id: int) -> bool:
        usuario = await self.repository.get(db, usuario_id)
        if not usuario:
            return False
        await db.delete(usuario)
        await db.flush()
        return True

    async def get_paginated_usuarios(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 10,
        search_query: Optional[str] = None,
        ugel_id: Optional[int] = None,
        institucion_educativa_id: Optional[int] = None,
    ) -> tuple[List[Usuario], int]:
        return await self.repository.get_paginated_with_search(
            db,
            skip=skip,
            limit=limit,
            search_query=search_query,
            ugel_id=ugel_id,
            institucion_educativa_id=institucion_educativa_id,
        )


usuario_service = UsuarioService()

# Alias de compatibilidad
docente_service = usuario_service
