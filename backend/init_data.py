#!/usr/bin/env python
"""
Script para inicializar la base de datos con datos de competencias, capacidades y desempeños,
y crear el primer superusuario administrador.
Se ejecuta como parte del proceso de build/deploy.
"""

import os
import sys
import asyncio
import subprocess
from dotenv import load_dotenv

# Agregar el directorio backend al path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

# Cargar .env ANTES de cualquier import de app (database.py lee DATABASE_URL al importarse)
load_dotenv(os.path.join(backend_dir, ".env"))


def run_script(script_name: str) -> bool:
    """Ejecuta un script de carga de datos."""
    print(f"\n{'='*60}")
    print(f"Ejecutando: {script_name}")
    print(f"{'='*60}")

    try:
        result = subprocess.run(
            [sys.executable, "-m", f"scripts.{script_name}"],
            cwd=backend_dir,
            timeout=300
        )

        if result.returncode == 0:
            print(f"OK: {script_name} completado exitosamente\n")
            return True
        else:
            print(f"ERROR: {script_name} fallo\n")
            return False
    except subprocess.TimeoutExpired:
        print(f"TIMEOUT ejecutando {script_name}\n")
        return False
    except Exception as e:
        print(f"ERROR ejecutando {script_name}: {e}\n")
        return False


async def seed_roles(db):
    """Inserta los roles base si la tabla está vacía."""
    from sqlalchemy import text
    result = await db.execute(text("SELECT COUNT(*) FROM roles"))
    count = result.scalar()
    if count > 0:
        return
    roles = [
        (1, 'especialista_dre_comunicacion', 'Especialista DRE Comunicación', 'Mantiene desempeños de comunicación a nivel DRE', 1, 1),
        (2, 'especialista_dre_matematica',   'Especialista DRE Matemática',   'Mantiene desempeños de matemática a nivel DRE', 1, 2),
        (3, 'responsable_ugel',              'Responsable UGEL',              'Gestiona su UGEL y sus instituciones educativas', 2, 3),
        (4, 'director',                      'Director',                      'Director de institución educativa',               3, 4),
        (5, 'auxiliar',                      'Auxiliar',                      'Auxiliar de institución educativa',               4, 5),
        (6, 'docente',                       'Docente',                       'Docente que genera y asigna exámenes',            5, 6),
        (7, 'estudiante',                    'Estudiante',                    'Estudiante que rinde exámenes',                   6, 7),
    ]
    for r in roles:
        await db.execute(text(
            "INSERT IGNORE INTO roles (id, codigo, nombre, descripcion, nivel, orden) "
            "VALUES (:id, :codigo, :nombre, :descripcion, :nivel, :orden)"
        ), {"id": r[0], "codigo": r[1], "nombre": r[2], "descripcion": r[3], "nivel": r[4], "orden": r[5]})
    await db.commit()
    print("Roles base sembrados.")


async def create_first_admin():
    """Crea el primer superusuario si no existe ninguno."""
    from app.core.database import AsyncSessionLocal
    from app.models import db_models  # noqa: F401 — registra Rol y demás modelos
    from app.models.usuario import Usuario
    from app.core.security import get_password_hash
    from sqlalchemy import select, text

    print(f"\n{'='*60}")
    print("Verificando superusuario admin...")
    print(f"{'='*60}")

    async with AsyncSessionLocal() as db:
        # Sembrar roles si la tabla está vacía
        await seed_roles(db)

        # Verificar si ya existe un admin (rol especialista_dre_comunicacion = id 1)
        result = await db.execute(
            select(Usuario).where(Usuario.rol_id == 1)
        )
        existing_admin = result.scalars().first()

        if existing_admin:
            print(f"Ya existe un superusuario: DNI {existing_admin.dni}")
            return

        admin_dni = os.getenv("ADMIN_DNI", "00000000")
        admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
        admin_nombres = os.getenv("ADMIN_NOMBRES", "Administrador")
        admin_apellidos = os.getenv("ADMIN_APELLIDOS", "Sistema")

        admin = Usuario(
            dni=admin_dni,
            nombres=admin_nombres,
            apellidos=admin_apellidos,
            profesion="Administrador del Sistema",
            is_active=True,
            rol_id=1,  # especialista_dre_comunicacion = superusuario
            password_hash=get_password_hash(admin_password),
        )
        db.add(admin)
        await db.commit()
        print(f"Superusuario creado exitosamente:")
        print(f"  DNI: {admin_dni}")
        print(f"  Contrasena: {admin_password}")
        print(f"  Nombres: {admin_nombres} {admin_apellidos}")
        print("  IMPORTANTE: Cambia la contrasena despues del primer login.")


def main():
    """Script principal."""
    print("\nIniciando carga de datos de LectoSistem y MatSistem...\n")

    success_count = 0

    # Ejecutar scripts de carga de curriculum
    scripts = ["load_desempenos", "load_matematica"]

    for script in scripts:
        if run_script(script):
            success_count += 1

    print(f"\n{'='*60}")
    print(f"Resumen curriculum: {success_count}/{len(scripts)} scripts completados")
    print(f"{'='*60}\n")

    # Crear primer admin
    asyncio.run(create_first_admin())

    return 0 if success_count == len(scripts) else 1


if __name__ == "__main__":
    sys.exit(main())
