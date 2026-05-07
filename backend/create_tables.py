"""Script de inicialización: crea todas las tablas en la DB y marca alembic como aplicado."""
import asyncio
import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from app.core.database import engine, Base
from app.models.db_models import *  # noqa: F401, F403
from app.models.usuario import Usuario  # noqa: F401
from app.models.ubigeo import Provincia, Distrito  # noqa: F401


async def main():
    print(f"Conectando a: {os.getenv('DATABASE_URL', '(no DATABASE_URL)')}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tablas creadas OK")


if __name__ == "__main__":
    asyncio.run(main())
