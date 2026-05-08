"""
Métricas scoped por rol del usuario autenticado.
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.models.db_models import (
    ExamenLectura, ExamenMatematica,
    InstitucionEducativa, Ugel, AsignacionExamen,
    IntentoExamen, ProgresoEstudiante,
)
from app.models.usuario import Usuario
from app.models.enums import RolCodigo
from app.api.dependencies import get_current_active_user, require_modulo

router = APIRouter()

DRE_ROLES = {RolCodigo.ESPECIALISTA_DRE_COMUNICACION, RolCodigo.ESPECIALISTA_DRE_MATEMATICA}


@router.get("/resumen")
async def resumen_metricas(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_modulo("metricas")),
):
    """
    Métricas resumidas adaptadas al rol:
    - DRE: todo el sistema
    - UGEL: su UGEL
    - Director/Auxiliar: su IE
    - Docente: sus exámenes
    """
    rol = RolCodigo(current_user.rol_codigo)
    ugel_id = current_user.ugel_id
    ie_id = current_user.institucion_educativa_id
    docente_id = current_user.id

    # ── Base filters por rol ──────────────────────────────────────────────────
    if rol in DRE_ROLES:
        # DRE ve todo
        lec_filter = True
        mat_filter = True
        user_filter = True
    elif rol == RolCodigo.RESPONSABLE_UGEL and ugel_id:
        # UGEL ve sus IEs
        ie_ids_r = await db.execute(
            select(InstitucionEducativa.id).where(InstitucionEducativa.ugel_id == ugel_id)
        )
        ie_ids = [r[0] for r in ie_ids_r.all()]
        lec_filter = ExamenLectura.docente_id.in_(
            select(Usuario.id).where(Usuario.institucion_educativa_id.in_(ie_ids))
        )
        mat_filter = ExamenMatematica.docente_id.in_(
            select(Usuario.id).where(Usuario.institucion_educativa_id.in_(ie_ids))
        )
        user_filter = Usuario.institucion_educativa_id.in_(ie_ids)
    elif rol in {RolCodigo.DIRECTOR, RolCodigo.AUXILIAR} and ie_id:
        # IE ve sus docentes
        lec_filter = ExamenLectura.docente_id.in_(
            select(Usuario.id).where(Usuario.institucion_educativa_id == ie_id)
        )
        mat_filter = ExamenMatematica.docente_id.in_(
            select(Usuario.id).where(Usuario.institucion_educativa_id == ie_id)
        )
        user_filter = Usuario.institucion_educativa_id == ie_id
    else:
        # Docente: solo sus propios exámenes
        lec_filter = ExamenLectura.docente_id == docente_id
        mat_filter = ExamenMatematica.docente_id == docente_id
        user_filter = Usuario.id == docente_id

    # ── Conteos ───────────────────────────────────────────────────────────────
    async def count(model, filt):
        if filt is True:
            r = await db.execute(select(func.count()).select_from(model))
        else:
            r = await db.execute(select(func.count()).select_from(model).where(filt))
        return r.scalar() or 0

    total_lectura = await count(ExamenLectura, lec_filter)
    total_matematica = await count(ExamenMatematica, mat_filter)

    # Usuarios en scope
    if user_filter is True:
        r = await db.execute(select(func.count()).select_from(Usuario))
    else:
        r = await db.execute(select(func.count()).select_from(Usuario).where(user_filter))
    total_usuarios = r.scalar() or 0

    # UGELes e IEs (solo para DRE)
    total_ugeles = 0
    total_instituciones = 0
    if rol in DRE_ROLES:
        r = await db.execute(select(func.count()).select_from(Ugel).where(Ugel.is_active == True))
        total_ugeles = r.scalar() or 0
        r = await db.execute(select(func.count()).select_from(InstitucionEducativa).where(InstitucionEducativa.is_active == True))
        total_instituciones = r.scalar() or 0
    elif rol == RolCodigo.RESPONSABLE_UGEL and ugel_id:
        r = await db.execute(
            select(func.count()).select_from(InstitucionEducativa).where(
                InstitucionEducativa.ugel_id == ugel_id,
                InstitucionEducativa.is_active == True,
            )
        )
        total_instituciones = r.scalar() or 0

    # Asignaciones y completados (Fase 3)
    total_asignaciones = 0
    total_completados = 0
    try:
        if rol in {RolCodigo.DIRECTOR, RolCodigo.AUXILIAR} and ie_id:
            r = await db.execute(
                select(func.count()).select_from(AsignacionExamen).where(
                    AsignacionExamen.institucion_educativa_id == ie_id
                )
            )
            total_asignaciones = r.scalar() or 0
            r = await db.execute(
                select(func.count()).select_from(IntentoExamen).where(
                    IntentoExamen.estado == "completado",
                    IntentoExamen.asignacion_id.in_(
                        select(AsignacionExamen.id).where(
                            AsignacionExamen.institucion_educativa_id == ie_id
                        )
                    ),
                )
            )
            total_completados = r.scalar() or 0
        elif rol in DRE_ROLES:
            r = await db.execute(select(func.count()).select_from(AsignacionExamen))
            total_asignaciones = r.scalar() or 0
            r = await db.execute(
                select(func.count()).select_from(IntentoExamen).where(IntentoExamen.estado == "completado")
            )
            total_completados = r.scalar() or 0
        elif rol not in {RolCodigo.ESTUDIANTE, RolCodigo.RESPONSABLE_UGEL}:
            r = await db.execute(
                select(func.count()).select_from(AsignacionExamen).where(
                    AsignacionExamen.asignado_por_id == docente_id
                )
            )
            total_asignaciones = r.scalar() or 0
            r = await db.execute(
                select(func.count()).select_from(IntentoExamen).where(
                    IntentoExamen.estado == "completado",
                    IntentoExamen.asignacion_id.in_(
                        select(AsignacionExamen.id).where(
                            AsignacionExamen.asignado_por_id == docente_id
                        )
                    ),
                )
            )
            total_completados = r.scalar() or 0
    except Exception:
        pass  # tablas pueden no existir en migraciones anteriores

    # Exámenes recientes (últimos 5 de cada área, luego ordenar en Python)
    if lec_filter is True:
        r_lec = await db.execute(
            select(ExamenLectura).order_by(ExamenLectura.fecha_creacion.desc()).limit(5)
        )
    else:
        r_lec = await db.execute(
            select(ExamenLectura).where(lec_filter).order_by(ExamenLectura.fecha_creacion.desc()).limit(5)
        )
    recientes_lec = r_lec.scalars().all()

    if mat_filter is True:
        r_mat = await db.execute(
            select(ExamenMatematica).order_by(ExamenMatematica.fecha_creacion.desc()).limit(5)
        )
    else:
        r_mat = await db.execute(
            select(ExamenMatematica).where(mat_filter).order_by(ExamenMatematica.fecha_creacion.desc()).limit(5)
        )
    recientes_mat = r_mat.scalars().all()

    recientes_combinados = [
        {
            "id": e.id,
            "titulo": e.titulo or f"Examen {e.grado_nombre}",
            "grado": e.grado_nombre or "—",
            "area": "lectura",
            "fecha": e.fecha_creacion.isoformat() if e.fecha_creacion else None,
        }
        for e in recientes_lec
    ] + [
        {
            "id": e.id,
            "titulo": e.titulo or f"Examen {e.grado_nombre}",
            "grado": e.grado_nombre or "—",
            "area": "matematica",
            "fecha": e.fecha_creacion.isoformat() if e.fecha_creacion else None,
        }
        for e in recientes_mat
    ]
    
    recientes_combinados.sort(key=lambda x: x["fecha"] or "", reverse=True)
    recientes = recientes_combinados[:5]

    return {
        "total_examenes_lectura": total_lectura,
        "total_examenes_matematica": total_matematica,
        "total_examenes": total_lectura + total_matematica,
        "total_usuarios": total_usuarios,
        "total_ugeles": total_ugeles,
        "total_instituciones": total_instituciones,
        "total_asignaciones": total_asignaciones,
        "total_completados": total_completados,
        "recientes": recientes,
        "rol": rol.value,
    }
