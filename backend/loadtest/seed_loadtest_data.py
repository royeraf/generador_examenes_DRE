"""
Crea datos dedicados para pruebas de carga LOCALES del flujo "estudiante rinde examen".

Genera:
  - N estudiantes de prueba (codigo_estudiante = LOADT0001, LOADT0002, ...)
    con matrícula activa en institución 5755, grado "PRIMER GRADO DE PRIMARIA" (id 1), sección A.
  - 1 asignación de examen de lectura (examen_id=14) y 1 de matemática (examen_id=28)
    con ventana horaria amplia (año actual, sin vencer) e intentos_permitidos alto,
    para poder correr el load test repetidas veces sin toparse con "intentos agotados".

Es idempotente: si ya existen estudiantes/asignaciones LOADT los reutiliza en vez de duplicar.

Uso:
    cd backend
    ./venv/bin/python -m loadtest.seed_loadtest_data --n-estudiantes 50

Requiere estar apuntando a la BD de DESARROLLO LOCAL (revisa DATABASE_URL en .env).
NUNCA correr esto contra la base de datos del VPS de producción.
"""
import argparse
import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, func

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal, engine, init_db
from app.core.security import get_password_hash
from app.models.estudiante import Estudiante
from app.models.usuario import Usuario
from app.models.db_models import Matricula, AsignacionExamen

PASSWORD = "LoadTest2026!"
CODIGO_PREFIX = "LOADT"
INSTITUCION_ID = 5755
GRADO_ID = 1
SECCION = "A"
AÑO_ESCOLAR = datetime.now().year

EXAMEN_LECTURA_ID = 14
EXAMEN_MATEMATICA_ID = 28


def _confirmar_bd_local():
    settings = get_settings()
    url = settings.database_url
    if "drehua5" in url or "sieva" in url.lower():
        print(f"ABORTADO: la DATABASE_URL actual parece ser de PRODUCCIÓN:\n  {url}")
        print("Este script solo debe correr contra la BD de desarrollo local.")
        sys.exit(1)
    print(f"BD destino: {url.split('@')[-1] if '@' in url else url}")


async def crear_estudiantes(db, n: int) -> list[str]:
    existentes_r = await db.execute(
        select(Estudiante.codigo_estudiante).where(
            Estudiante.codigo_estudiante.like(f"{CODIGO_PREFIX}%")
        )
    )
    existentes = {c for c in existentes_r.scalars().all()}
    codigos = [f"{CODIGO_PREFIX}{i:04d}" for i in range(1, n + 1)]
    faltantes = [c for c in codigos if c not in existentes]

    for codigo in faltantes:
        est = Estudiante(
            codigo_estudiante=codigo,
            nombres="Carga",
            apellidos=codigo,
            password_hash=get_password_hash(PASSWORD),
            is_active=True,
            institucion_educativa_id=INSTITUCION_ID,
        )
        db.add(est)
        await db.flush()
        await db.refresh(est)

        mat_r = await db.execute(
            select(Matricula).where(
                Matricula.estudiante_id == est.id,
                Matricula.año_escolar == AÑO_ESCOLAR,
            )
        )
        if not mat_r.scalars().first():
            db.add(Matricula(
                estudiante_id=est.id,
                año_escolar=AÑO_ESCOLAR,
                grado_id=GRADO_ID,
                seccion=SECCION,
                institucion_educativa_id=INSTITUCION_ID,
                is_active=True,
            ))

    if faltantes:
        await db.flush()
        print(f"Estudiantes creados: {len(faltantes)}")
    else:
        print("Estudiantes de carga ya existían, no se creó ninguno nuevo.")

    print(f"Total estudiantes LOADT disponibles: {len(codigos)}")
    return codigos


async def _get_asignado_por_id(db) -> int:
    r = await db.execute(select(Usuario.id).order_by(Usuario.id).limit(1))
    usuario_id = r.scalar()
    if not usuario_id:
        raise RuntimeError("No hay ningún usuario en la BD para usar como asignado_por_id")
    return usuario_id


async def crear_asignacion(db, tipo_examen: str, examen_id: int, asignado_por_id: int) -> int:
    existente_r = await db.execute(
        select(AsignacionExamen).where(
            AsignacionExamen.tipo_examen == tipo_examen,
            AsignacionExamen.examen_id == examen_id,
            AsignacionExamen.institucion_educativa_id == INSTITUCION_ID,
            AsignacionExamen.grado_id == GRADO_ID,
            AsignacionExamen.seccion == SECCION,
            AsignacionExamen.año_escolar == AÑO_ESCOLAR,
        )
    )
    asig = existente_r.scalars().first()
    ahora = datetime.now(timezone.utc)
    if asig:
        # Asegurar que siga vigente y con intentos altos aunque ya existiera de una corrida previa
        asig.fecha_inicio = ahora - timedelta(days=1)
        asig.fecha_fin = ahora + timedelta(days=365)
        asig.intentos_permitidos = 999999
        asig.is_active = True
        await db.flush()
        print(f"Asignación {tipo_examen} reutilizada: id={asig.id}")
        return asig.id

    asig = AsignacionExamen(
        tipo_examen=tipo_examen,
        examen_id=examen_id,
        asignado_por_id=asignado_por_id,
        institucion_educativa_id=INSTITUCION_ID,
        grado_id=GRADO_ID,
        seccion=SECCION,
        año_escolar=AÑO_ESCOLAR,
        fecha_inicio=ahora - timedelta(days=1),
        fecha_fin=ahora + timedelta(days=365),
        duracion_minutos=None,
        intentos_permitidos=999999,
        mostrar_resultados=True,
        mezclar_preguntas=True,
        mezclar_alternativas=True,
        is_active=True,
    )
    db.add(asig)
    await db.flush()
    await db.refresh(asig)
    print(f"Asignación {tipo_examen} creada: id={asig.id}")
    return asig.id


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-estudiantes", type=int, default=50)
    args = parser.parse_args()

    _confirmar_bd_local()
    await init_db()

    async with AsyncSessionLocal() as db:
        codigos = await crear_estudiantes(db, args.n_estudiantes)
        asignado_por_id = await _get_asignado_por_id(db)
        asig_lectura_id = await crear_asignacion(db, "lectura", EXAMEN_LECTURA_ID, asignado_por_id)
        asig_matematica_id = await crear_asignacion(db, "matematica", EXAMEN_MATEMATICA_ID, asignado_por_id)
        await db.commit()

    print("\n" + "=" * 60)
    print("  LISTO PARA LOAD TEST")
    print("=" * 60)
    print(f"Password (todos los LOADT####): {PASSWORD}")
    print(f"Estudiantes: {codigos[0]} .. {codigos[-1]} ({len(codigos)} total)")
    print(f"Asignación lectura:    id={asig_lectura_id}")
    print(f"Asignación matemática: id={asig_matematica_id}")
    print()
    print("Correr locust con, por ejemplo:")
    print(f"  LOADTEST_ASIGNACION_LECTURA={asig_lectura_id} \\")
    print(f"  LOADTEST_ASIGNACION_MATEMATICA={asig_matematica_id} \\")
    print(f"  LOADTEST_N_ESTUDIANTES={len(codigos)} \\")
    print("  ./venv/bin/locust -f loadtest/locustfile.py --host http://localhost:8000")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
