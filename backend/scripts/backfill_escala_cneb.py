"""
Backfill de la escala CNEB en intentos de examen existentes.

Rellena `nota_vigesimal` (0-20) y `nivel_cneb` (AD/A/B/C) para los
`intentos_examen` que ya tienen `puntaje_total` (0-100) pero no fueron
clasificados aún.

Uso:  cd backend && ./venv/bin/python -m scripts.backfill_escala_cneb
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

# Cargar .env ANTES de importar app.core.database, para usar el mismo
# DATABASE_URL que la aplicación (MySQL en dev/prod, no el default SQLite).
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal

# Registrar todos los modelos para que SQLAlchemy resuelva las relaciones
# (p. ej. Ugel -> Provincia, definida en app.models.ubigeo).
import app.models.ubigeo  # noqa: F401
import app.models.usuario  # noqa: F401
import app.models.estudiante  # noqa: F401
import app.models.sesion  # noqa: F401
from app.models.db_models import IntentoExamen
from app.core.escala_cneb import clasificar


async def main() -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(IntentoExamen).where(
                IntentoExamen.puntaje_total.isnot(None),
                IntentoExamen.nota_vigesimal.is_(None),
            )
        )
        intentos = result.scalars().all()

        actualizados = 0
        for intento in intentos:
            clasificacion = clasificar(intento.puntaje_total)
            intento.nota_vigesimal = clasificacion["nota_vigesimal"]
            intento.nivel_cneb = clasificacion["nivel_cneb"]
            actualizados += 1

        await db.commit()
        print(f"Backfill completado: {actualizados} intentos clasificados.")


if __name__ == "__main__":
    asyncio.run(main())
