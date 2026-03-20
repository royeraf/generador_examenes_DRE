from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Database URL - PostgreSQL
# Usa asyncpg como driver asíncrono para PostgreSQL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/lectosistem_dre"
)

# Create async engine
connect_args = {}
if "render.com" in DATABASE_URL:
    connect_args["ssl"] = "require"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL debugging
    pool_pre_ping=True,  # Verifica conexiones antes de usarlas
    pool_size=10,
    max_overflow=20,
    connect_args=connect_args
)

# Async Session factory
AsyncSessionLocal = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False,
    autoflush=False
)

# Base class for models
Base = declarative_base()


async def get_db():
    """Dependency to get async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database tables asynchronously."""
    # Importar modelos aquí para asegurar que se registren en Base.metadata
    from app.models.db_models import (
        Grado, Capacidad, Desempeno,
        CompetenciaMatematica, CapacidadMatematica,
        EstandarMatematica, DesempenoMatematica,
        ExamenLectura, ExamenMatematica
    )
    from app.models.docente import Docente
    from app.models.ubigeo import Provincia, Distrito

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # Migración inline: agregar columnas provincia_id y distrito_id si no existen
        from sqlalchemy import text, inspect as sa_inspect

        def _add_columns_if_missing(sync_conn):
            inspector = sa_inspect(sync_conn)
            columns = [col["name"] for col in inspector.get_columns("docentes")]
            if "provincia_id" not in columns:
                sync_conn.execute(text(
                    "ALTER TABLE docentes ADD COLUMN provincia_id INTEGER REFERENCES provincias(id) ON DELETE SET NULL"
                ))
            if "distrito_id" not in columns:
                sync_conn.execute(text(
                    "ALTER TABLE docentes ADD COLUMN distrito_id INTEGER REFERENCES distritos(id) ON DELETE SET NULL"
                ))

        await conn.run_sync(_add_columns_if_missing)
