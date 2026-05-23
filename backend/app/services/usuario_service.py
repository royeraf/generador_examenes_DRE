from datetime import datetime
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.repositories.usuario_repository import usuario_repository
from app.schemas.usuario import UsuarioAdminCreate, UsuarioUpdate
from app.models.usuario import Usuario
from app.models.db_models import Rol, InstitucionEducativa
from app.models.enums import RolCodigo
from app.core.security import get_password_hash, verify_password
from app.core.permissions import puede_crear_rol
from app.services.matricula_service import get_matricula_activa


class UsuarioService:
    """Lógica de negocio para usuarios."""

    def __init__(self):
        self.repository = usuario_repository

    async def _get_rol_id(self, db: AsyncSession, rol_codigo: str) -> int:
        result = await db.execute(select(Rol).where(Rol.codigo == rol_codigo))
        rol = result.scalars().first()
        if not rol:
            raise ValueError(f"Rol '{rol_codigo}' no encontrado")
        return rol.id

    async def _resolve_ugel_id(self, db: AsyncSession, institucion_educativa_id: int) -> Optional[int]:
        result = await db.execute(
            select(InstitucionEducativa.ugel_id).where(InstitucionEducativa.id == institucion_educativa_id)
        )
        return result.scalar()

    async def create_usuario(
        self,
        db: AsyncSession,
        usuario_in: UsuarioAdminCreate,
        creado_por_id: Optional[int] = None,
        creado_por_rol: Optional[str] = None,
    ) -> Usuario:
        if creado_por_rol and not puede_crear_rol(creado_por_rol, usuario_in.rol_codigo):
            raise ValueError(f"No tienes permiso para crear usuarios con rol '{usuario_in.rol_codigo}'")

        if usuario_in.dni:
            existing = await self.repository.get_by_dni(db, usuario_in.dni)
            if existing:
                raise ValueError("DNI ya registrado")

        obj_data = usuario_in.model_dump()
        password = obj_data.pop("password")
        rol_codigo = obj_data.pop("rol_codigo")
        # Extraer campos de matricula antes de crear el usuario
        grado_id = obj_data.pop("grado_id", None)
        seccion = obj_data.pop("seccion", None)
        año_escolar = obj_data.pop("año_escolar", None)

        if rol_codigo == RolCodigo.ESTUDIANTE:
            raise ValueError("Los estudiantes deben crearse usando estudiante_service.crear_estudiante()")

        obj_data["password_hash"] = get_password_hash(password)
        obj_data["rol_id"] = await self._get_rol_id(db, rol_codigo)
        obj_data["creado_por_id"] = creado_por_id

        if obj_data.get("institucion_educativa_id") and not obj_data.get("ugel_id"):
            obj_data["ugel_id"] = await self._resolve_ugel_id(db, obj_data["institucion_educativa_id"])

        db_obj = Usuario(**obj_data)
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)

        return db_obj

    async def authenticate(self, db: AsyncSession, identifier: str, password: str) -> Optional[Usuario]:
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

        # Extraer campos de matrícula antes de actualizar el usuario
        grado_id = update_data.pop("grado_id", None)
        seccion = update_data.pop("seccion", None)
        año_escolar = update_data.pop("año_escolar", None)

        if "password" in update_data:
            update_data["password_hash"] = get_password_hash(update_data.pop("password"))
        if "rol_codigo" in update_data:
            nuevo_rol = update_data.pop("rol_codigo")
            if nuevo_rol == RolCodigo.ESTUDIANTE:
                raise ValueError("No se puede cambiar un usuario a rol estudiante; use la tabla estudiantes")
            update_data["rol_id"] = await self._get_rol_id(db, nuevo_rol)

        if update_data.get("institucion_educativa_id") and not update_data.get("ugel_id"):
            update_data["ugel_id"] = await self._resolve_ugel_id(db, update_data["institucion_educativa_id"])

        usuario = await self.repository.update(db, usuario, update_data)
        return usuario

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
