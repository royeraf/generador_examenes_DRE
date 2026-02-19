#!/usr/bin/env python3
"""
Script para migrar datos de SQLite (desempenos.db) a PostgreSQL.

Primero crea todas las tablas en PostgreSQL (usando SQLAlchemy),
luego migra los datos del SQLite existente con reconexión automática.

Uso:
    cd /home/royer/Desktop/lectosistem_dre/backend
    source venv/bin/activate
    python scripts/migrate_sqlite_to_postgres.py
"""

import os
import sys
import sqlite3
import asyncio
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

import psycopg2
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/lectosistem_dre"
)
PG_URL_SYNC = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
SQLITE_PATH = os.path.join(os.path.dirname(__file__), "../desempenos.db")


# =====================================================
# PASO 1: CREAR TABLAS
# =====================================================

async def create_tables():
    print("🔧 Creando tablas en PostgreSQL...")
    from app.models.db_models import (
        Grado, Capacidad, Desempeno,
        CompetenciaMatematica, CapacidadMatematica,
        EstandarMatematica, DesempenoMatematica,
        ExamenLectura, ExamenMatematica
    )
    from app.models.docente import Docente
    from app.core.database import Base

    engine = create_async_engine(DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print("  ✅ Tablas creadas correctamente.\n")


# =====================================================
# PASO 2: MIGRAR DATOS (con reconexión automática)
# =====================================================

def new_pg_conn():
    """Crea una nueva conexión a PostgreSQL."""
    conn = psycopg2.connect(PG_URL_SYNC, connect_timeout=30)
    conn.autocommit = False
    return conn


def execute_with_retry(pg_conn, sql, params, max_retries=3):
    """Ejecuta una query con reconexión automática si la conexión se cae."""
    for attempt in range(max_retries):
        try:
            cur = pg_conn.cursor()
            cur.execute(sql, params)
            pg_conn.commit()
            cur.close()
            return pg_conn, True
        except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
            print(f"\n  🔄 Conexión perdida, reconectando... (intento {attempt + 1}/{max_retries})")
            try:
                pg_conn.close()
            except Exception:
                pass
            time.sleep(2)
            try:
                pg_conn = new_pg_conn()
            except Exception as e2:
                print(f"  ❌ No se pudo reconectar: {e2}")
                if attempt == max_retries - 1:
                    raise
        except psycopg2.errors.UniqueViolation:
            try:
                pg_conn.rollback()
            except Exception:
                pass
            return pg_conn, False
        except Exception as e:
            try:
                pg_conn.rollback()
            except Exception:
                pass
            print(f"  ⚠️  Error: {e}")
            return pg_conn, False
    return pg_conn, False


def migrate_table(sqlite_cur, pg_conn, table_name, columns, insert_sql):
    """Migra una tabla completa con reconexión automática."""
    try:
        sqlite_cur.execute(f"SELECT {', '.join(columns)} FROM {table_name}")
    except sqlite3.OperationalError:
        print(f"  ⚠️  Tabla '{table_name}' no existe en SQLite, omitiendo.")
        return pg_conn, 0

    rows = sqlite_cur.fetchall()
    if not rows:
        print(f"  ⚠️  Tabla '{table_name}': vacía.")
        return pg_conn, 0

    inserted = 0
    for i, row in enumerate(rows):
        pg_conn, ok = execute_with_retry(pg_conn, insert_sql, row)
        if ok:
            inserted += 1
        # Pequeña pausa cada 50 filas para no saturar la conexión
        if (i + 1) % 50 == 0:
            time.sleep(0.1)

    print(f"  ✅ Tabla '{table_name}': {inserted}/{len(rows)} filas migradas.")
    return pg_conn, inserted


def migrate_data():
    print("📦 Iniciando migración de datos...\n")

    if not os.path.exists(SQLITE_PATH):
        print(f"❌ No se encontró: {SQLITE_PATH}")
        sys.exit(1)

    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    sqlite_cur = sqlite_conn.cursor()

    try:
        pg_conn = new_pg_conn()
        print("✅ Conexión a PostgreSQL establecida.\n")
    except Exception as e:
        print(f"❌ No se pudo conectar: {e}")
        sys.exit(1)

    try:
        print("📦 Migrando: grados")
        pg_conn, _ = migrate_table(sqlite_cur, pg_conn, "grados",
            ["id", "nombre", "numero", "nivel", "orden"],
            "INSERT INTO grados (id, nombre, numero, nivel, orden) VALUES (%s,%s,%s,%s,%s) ON CONFLICT (id) DO NOTHING"
        )

        print("📦 Migrando: capacidades")
        pg_conn, _ = migrate_table(sqlite_cur, pg_conn, "capacidades",
            ["id", "nombre", "tipo", "descripcion"],
            "INSERT INTO capacidades (id, nombre, tipo, descripcion) VALUES (%s,%s,%s,%s) ON CONFLICT (id) DO NOTHING"
        )

        print("📦 Migrando: desempenos")
        pg_conn, _ = migrate_table(sqlite_cur, pg_conn, "desempenos",
            ["id", "codigo", "descripcion", "grado_id", "capacidad_id"],
            "INSERT INTO desempenos (id, codigo, descripcion, grado_id, capacidad_id) VALUES (%s,%s,%s,%s,%s) ON CONFLICT (id) DO NOTHING"
        )

        print("📦 Migrando: competencias_matematica")
        pg_conn, _ = migrate_table(sqlite_cur, pg_conn, "competencias_matematica",
            ["id", "codigo", "nombre", "descripcion"],
            "INSERT INTO competencias_matematica (id, codigo, nombre, descripcion) VALUES (%s,%s,%s,%s) ON CONFLICT (id) DO NOTHING"
        )

        print("📦 Migrando: capacidades_matematica")
        pg_conn, _ = migrate_table(sqlite_cur, pg_conn, "capacidades_matematica",
            ["id", "orden", "nombre", "descripcion", "competencia_id"],
            "INSERT INTO capacidades_matematica (id, orden, nombre, descripcion, competencia_id) VALUES (%s,%s,%s,%s,%s) ON CONFLICT (id) DO NOTHING"
        )

        print("📦 Migrando: estandares_matematica")
        pg_conn, _ = migrate_table(sqlite_cur, pg_conn, "estandares_matematica",
            ["id", "descripcion", "ciclo", "grado_id", "competencia_id"],
            "INSERT INTO estandares_matematica (id, descripcion, ciclo, grado_id, competencia_id) VALUES (%s,%s,%s,%s,%s) ON CONFLICT (id) DO NOTHING"
        )

        print("📦 Migrando: desempenos_matematica")
        pg_conn, _ = migrate_table(sqlite_cur, pg_conn, "desempenos_matematica",
            ["id", "codigo", "descripcion", "grado_id", "capacidad_id"],
            "INSERT INTO desempenos_matematica (id, codigo, descripcion, grado_id, capacidad_id) VALUES (%s,%s,%s,%s,%s) ON CONFLICT (id) DO NOTHING"
        )

        # DOCENTES
        print("📦 Migrando: docentes")
        sqlite_cur.execute("PRAGMA table_info(docentes)")
        col_names = [c[1] for c in sqlite_cur.fetchall()]
        all_cols = ["id", "dni", "nombres", "apellidos", "profesion",
                    "institucion_educativa", "nivel_educativo",
                    "password_hash", "is_active", "is_superuser"]
        available = [c for c in all_cols if c in col_names]
        sqlite_cur.execute(f"SELECT {', '.join(available)} FROM docentes")
        rows = sqlite_cur.fetchall()
        inserted = 0
        for row in rows:
            row_dict = dict(zip(available, row))
            # SQLite guarda booleanos como 0/1 — convertir a bool para PostgreSQL
            row_dict["is_active"] = bool(row_dict.get("is_active", True))
            row_dict["is_superuser"] = bool(row_dict.get("is_superuser", False))
            vals = tuple(row_dict.get(c) for c in all_cols)
            pg_conn, ok = execute_with_retry(pg_conn, """
                INSERT INTO docentes
                    (id, dni, nombres, apellidos, profesion,
                     institucion_educativa, nivel_educativo,
                     password_hash, is_active, is_superuser)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (id) DO NOTHING
            """, vals)
            if ok:
                inserted += 1
        print(f"  ✅ Tabla 'docentes': {inserted}/{len(rows)} filas migradas.")


        # Actualizar secuencias
        print("\n🔧 Actualizando secuencias...")
        for table in ["grados", "capacidades", "desempenos",
                      "competencias_matematica", "capacidades_matematica",
                      "estandares_matematica", "desempenos_matematica", "docentes"]:
            pg_conn, _ = execute_with_retry(pg_conn, f"""
                SELECT setval(
                    pg_get_serial_sequence('{table}', 'id'),
                    COALESCE((SELECT MAX(id) FROM {table}), 1)
                )
            """, None if False else ())
            print(f"  ✅ Secuencia '{table}' actualizada.")

        print("\n" + "=" * 60)
        print("  ✅ Migración completada exitosamente.")
        print("=" * 60)

    finally:
        sqlite_conn.close()
        try:
            pg_conn.close()
        except Exception:
            pass


async def main():
    print("=" * 60)
    print("  Migración SQLite → PostgreSQL (Render)")
    print("=" * 60)
    print(f"  Origen:  {SQLITE_PATH}")
    print(f"  Destino: {PG_URL_SYNC}\n")
    await create_tables()
    migrate_data()


if __name__ == "__main__":
    asyncio.run(main())
