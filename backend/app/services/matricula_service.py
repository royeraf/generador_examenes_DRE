from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.db_models import Matricula, Grado


async def get_matricula_activa(db: AsyncSession, estudiante_id: int) -> Optional[Matricula]:
    result = await db.execute(
        select(Matricula)
        .options(selectinload(Matricula.grado))
        .where(Matricula.estudiante_id == estudiante_id, Matricula.is_active == True)
        .order_by(Matricula.año_escolar.desc())
    )
    return result.scalars().first()


async def crear_matricula(
    db: AsyncSession,
    estudiante_id: int,
    grado_id: int,
    seccion: str,
    año_escolar: int,
    institucion_educativa_id: int,
    ugel_id: Optional[int] = None,
) -> Matricula:
    matricula = Matricula(
        estudiante_id=estudiante_id,
        año_escolar=año_escolar,
        grado_id=grado_id,
        seccion=seccion,
        institucion_educativa_id=institucion_educativa_id,
        ugel_id=ugel_id,
        is_active=True,
    )
    db.add(matricula)
    await db.flush()
    await db.refresh(matricula)
    # Cargar grado para tener grado_nombre disponible
    grado_r = await db.execute(select(Grado).where(Grado.id == grado_id))
    matricula.grado = grado_r.scalars().first()
    return matricula
