import asyncio
import os
import sys
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
from dotenv import load_dotenv

# Agregar el directorio backend al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Cargar .env antes de importar los modelos
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

# Importar Base y todos los modelos para que estén registrados
from app.core.database import Base  # noqa: E402
from app.models.db_models import (  # noqa: E402, F401
    Grado, Capacidad, Desempeno,
    CompetenciaMatematica, CapacidadMatematica,
    EstandarMatematica, DesempenoMatematica,
    ExamenLectura, ExamenMatematica,
)
from app.models.docente import Docente  # noqa: E402, F401
from app.models.ubigeo import Provincia, Distrito  # noqa: E402, F401

config = context.config

# Sobreescribir la URL desde la variable de entorno
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./desempenos.db")
config.set_main_option("sqlalchemy.url", DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Genera SQL sin conexión activa (útil para revisar SQL antes de aplicar)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
