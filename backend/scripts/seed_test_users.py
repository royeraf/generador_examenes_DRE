"""
Script para crear usuarios de prueba para cada rol del sistema.
Uso:  cd backend && ./venv/bin/python -m scripts.seed_test_users
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, text
from app.core.database import AsyncSessionLocal, init_db
from app.models.usuario import Usuario
from app.models.db_models import Rol
from app.core.security import get_password_hash

# ─── Parámetros comunes ───────────────────────────────────────────────────────
PASSWORD = "Test2024!"

# IDs que deben existir en la BD (creados por init_data / alembic seeds)
UGEL_ID   = 2   # UGEL DOS DE MAYO
IE_ID     = 2   # I.E. Pública Yarowilca
GRADO1_ID = 1   # Primer grado de primaria

# ─── Definición de usuarios de prueba ────────────────────────────────────────
USERS = [
    # Rol: especialista_dre_matematica
    {
        "dni": "11111111",
        "nombres": "María",
        "apellidos": "López Díaz",
        "profesion": "Especialista en Matemática",
        "rol_codigo": "especialista_dre_matematica",
        "ugel_id": None,
        "institucion_educativa_id": None,
        "grado_id": None,
        "seccion": None,
    },
    # Rol: responsable_ugel
    {
        "dni": "22222222",
        "nombres": "Carlos",
        "apellidos": "Mendoza Ruiz",
        "profesion": "Responsable UGEL",
        "rol_codigo": "responsable_ugel",
        "ugel_id": UGEL_ID,
        "institucion_educativa_id": None,
        "grado_id": None,
        "seccion": None,
    },
    # Rol: director
    {
        "dni": "99999999",
        "nombres": "Manuel",
        "apellidos": "Rosas Test",
        "profesion": "Director de IE",
        "rol_codigo": "director",
        "ugel_id": UGEL_ID,
        "institucion_educativa_id": IE_ID,
        "grado_id": None,
        "seccion": None,
    },
    # Rol: auxiliar
    {
        "dni": "33333333",
        "nombres": "Ana",
        "apellidos": "Torres Vásquez",
        "profesion": "Auxiliar de Educación",
        "rol_codigo": "auxiliar",
        "ugel_id": UGEL_ID,
        "institucion_educativa_id": IE_ID,
        "grado_id": None,
        "seccion": None,
    },
    # Rol: docente
    {
        "dni": "44444444",
        "nombres": "Pedro",
        "apellidos": "Quispe Alvarado",
        "profesion": "Docente de Primaria",
        "rol_codigo": "docente",
        "ugel_id": UGEL_ID,
        "institucion_educativa_id": IE_ID,
        "grado_id": None,
        "seccion": None,
    },
    # Rol: docente (segundo docente para la IE)
    {
        "dni": "55555555",
        "nombres": "Lucía",
        "apellidos": "Fernández Poma",
        "profesion": "Docente de Comunicación",
        "rol_codigo": "docente",
        "ugel_id": UGEL_ID,
        "institucion_educativa_id": IE_ID,
        "grado_id": None,
        "seccion": None,
    },
    # Rol: estudiante (con DNI)
    {
        "dni": "66666666",
        "nombres": "Sofía",
        "apellidos": "Campos Reyes",
        "rol_codigo": "estudiante",
        "ugel_id": UGEL_ID,
        "institucion_educativa_id": IE_ID,
        "grado_id": GRADO1_ID,
        "seccion": "A",
    },
    # Rol: estudiante (sin DNI físico — usa DNI placeholder)
    {
        "dni": "77777777",
        "nombres": "Diego",
        "apellidos": "Ramos Flores",
        "rol_codigo": "estudiante",
        "ugel_id": UGEL_ID,
        "institucion_educativa_id": IE_ID,
        "grado_id": GRADO1_ID,
        "seccion": "A",
    },
]


async def get_rol_id(db, codigo: str) -> int:
    r = await db.execute(select(Rol).where(Rol.codigo == codigo))
    rol = r.scalars().first()
    if not rol:
        raise ValueError(f"Rol '{codigo}' no encontrado en la BD")
    return rol.id


async def get_ultimo_codigo_estudiante(db) -> str:
    r = await db.execute(
        select(Usuario.codigo_estudiante)
        .where(Usuario.codigo_estudiante.isnot(None))
        .order_by(text("codigo_estudiante DESC"))
        .limit(1)
    )
    ultimo = r.scalar()
    if ultimo:
        try:
            numero = int(ultimo[3:]) + 1
        except ValueError:
            numero = 1
    else:
        numero = 1
    return f"EST{numero:04d}"


async def seed():
    await init_db()
    creados = []
    omitidos = []

    async with AsyncSessionLocal() as db:
        for u in USERS:
            dni = u.get("dni")

            # Verificar si ya existe por DNI
            if dni:
                r = await db.execute(select(Usuario).where(Usuario.dni == dni))
                if r.scalars().first():
                    omitidos.append(f"{dni} ({u['rol_codigo']}) — ya existe")
                    continue

            rol_id = await get_rol_id(db, u["rol_codigo"])

            codigo_estudiante = None
            if u["rol_codigo"] == "estudiante" and not dni:
                codigo_estudiante = await get_ultimo_codigo_estudiante(db)

            nuevo = Usuario(
                dni=dni,
                nombres=u.get("nombres"),
                apellidos=u.get("apellidos"),
                profesion=u.get("profesion"),
                rol_id=rol_id,
                ugel_id=u.get("ugel_id"),
                institucion_educativa_id=u.get("institucion_educativa_id"),
                grado_id=u.get("grado_id"),
                seccion=u.get("seccion"),
                codigo_estudiante=codigo_estudiante,
                password_hash=get_password_hash(PASSWORD),
                is_active=True,
            )
            db.add(nuevo)
            await db.flush()
            await db.refresh(nuevo)

            label = dni or nuevo.codigo_estudiante
            creados.append(f"{label} — {u['nombres']} {u.get('apellidos','')} ({u['rol_codigo']})")

        await db.commit()

    print("\n" + "="*60)
    print(f"  SEED COMPLETADO — contraseña: {PASSWORD}")
    print("="*60)
    if creados:
        print(f"\nUsuarios creados ({len(creados)}):")
        for c in creados:
            print(f"  ✓ {c}")
    if omitidos:
        print(f"\nOmitidos — ya existían ({len(omitidos)}):")
        for o in omitidos:
            print(f"  · {o}")
    print()


if __name__ == "__main__":
    asyncio.run(seed())
