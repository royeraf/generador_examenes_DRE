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

# Agregar el directorio backend al path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)


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


async def create_first_admin():
    """Crea el primer superusuario si no existe ninguno."""
    from app.core.database import init_db, AsyncSessionLocal
    from app.models.docente import Docente
    from app.core.security import get_password_hash
    from sqlalchemy import select

    print(f"\n{'='*60}")
    print("Verificando superusuario admin...")
    print(f"{'='*60}")

    await init_db()

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Docente).where(Docente.is_superuser == True)
        )
        existing_admin = result.scalars().first()

        if existing_admin:
            print(f"Ya existe un superusuario: DNI {existing_admin.dni}")
            return

        # Leer credenciales del entorno o usar valores por defecto
        admin_dni = os.getenv("ADMIN_DNI", "00000000")
        admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
        admin_nombres = os.getenv("ADMIN_NOMBRES", "Administrador")
        admin_apellidos = os.getenv("ADMIN_APELLIDOS", "Sistema")

        admin = Docente(
            dni=admin_dni,
            nombres=admin_nombres,
            apellidos=admin_apellidos,
            profesion="Administrador del Sistema",
            is_active=True,
            is_superuser=True,
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
