from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Database URL — SQLite por defecto para desarrollo local
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///./desempenos.db"
)

# Configurar connect_args según el motor
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    engine_kwargs = {}
elif "render.com" in DATABASE_URL:
    connect_args = {"ssl": "require"}
    engine_kwargs = {"pool_pre_ping": True, "pool_size": 10, "max_overflow": 20}
else:
    connect_args = {}
    engine_kwargs = {"pool_pre_ping": True, "pool_size": 10, "max_overflow": 20}

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args=connect_args,
    **engine_kwargs
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
    """Aplica migraciones de Alembic al iniciar la aplicación."""
    import os
    from alembic.config import Config
    from alembic import command

    alembic_cfg = Config(
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "../alembic.ini")
    )
    # Ejecutar en un thread para no bloquear el event loop
    import asyncio
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, lambda: command.upgrade(alembic_cfg, "head"))
