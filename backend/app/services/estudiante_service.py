from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.estudiante import Estudiante
from app.repositories.estudiante_repository import estudiante_repository
from app.services.matricula_service import crear_matricula
from app.core.security import get_password_hash, verify_password


class EstudianteService:

    async def _generar_codigo(self, db: AsyncSession) -> str:
        ultimo = await estudiante_repository.get_ultimo_codigo(db)
        if ultimo:
            try:
                numero = int(ultimo[3:]) + 1
            except ValueError:
                numero = 1
        else:
            numero = 1
        return f"EST{numero:04d}"

    async def crear_estudiante(
        self,
        db: AsyncSession,
        *,
        dni: Optional[str],
        nombres: Optional[str],
        apellidos: Optional[str],
        password: str,
        institucion_educativa_id: Optional[int],
        distrito_id: Optional[int] = None,
        creado_por_id: Optional[int] = None,
        is_active: bool = True,
        codigo_estudiante: Optional[str] = None,
        grado_id: Optional[int] = None,
        seccion: Optional[str] = None,
        año_escolar: Optional[int] = None,
        ugel_id: Optional[int] = None,
    ) -> Estudiante:
        if dni:
            existing = await estudiante_repository.get_by_dni(db, dni)
            if existing:
                raise ValueError("DNI ya registrado")

        if not codigo_estudiante:
            codigo_estudiante = await self._generar_codigo(db)

        est = Estudiante(
            dni=dni,
            codigo_estudiante=codigo_estudiante,
            nombres=nombres,
            apellidos=apellidos,
            password_hash=get_password_hash(password),
            is_active=is_active,
            institucion_educativa_id=institucion_educativa_id,
            distrito_id=distrito_id,
            creado_por_id=creado_por_id,
        )
        db.add(est)
        await db.flush()
        await db.refresh(est)

        if grado_id and seccion and institucion_educativa_id:
            await crear_matricula(
                db,
                estudiante_id=est.id,
                grado_id=grado_id,
                seccion=seccion,
                año_escolar=año_escolar or datetime.now().year,
                institucion_educativa_id=institucion_educativa_id,
                ugel_id=ugel_id,
            )

        return est

    async def authenticate(
        self, db: AsyncSession, identifier: str, password: str
    ) -> Optional[Estudiante]:
        est = await estudiante_repository.get_by_login(db, identifier)
        if not est:
            return None
        if not verify_password(password, est.password_hash):
            return None
        return est


estudiante_service = EstudianteService()
