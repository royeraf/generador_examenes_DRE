"""
Métricas scoped por rol del usuario autenticado.
"""
import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case

from app.core.database import get_db
from app.core.tz import iso_peru
from app.core.escala_cneb import clasificar, nota_a_nivel
from app.models.db_models import (
    ExamenLectura, ExamenMatematica,
    InstitucionEducativa, Ugel, AsignacionExamen,
    IntentoExamen, ProgresoEstudiante,
    PreguntaExamen, RespuestaIntento,
)
from app.models.estudiante import Estudiante
from app.models.ubigeo import Provincia
from app.models.usuario import Usuario
from app.models.enums import RolCodigo
from app.api.dependencies import get_current_active_user, require_modulo

router = APIRouter()

logger = logging.getLogger(__name__)

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
            "fecha": iso_peru(e.fecha_creacion),
        }
        for e in recientes_lec
    ] + [
        {
            "id": e.id,
            "titulo": e.titulo or f"Examen {e.grado_nombre}",
            "grado": e.grado_nombre or "—",
            "area": "matematica",
            "fecha": iso_peru(e.fecha_creacion),
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


def _item_avance(id_, nombre, asignaciones, completados, ugel=None, provincia=None):
    """Normaliza una fila de avance (asignaciones vs. asignaciones con intento completado)."""
    asignaciones = int(asignaciones or 0)
    completados = int(completados or 0)
    pct = round((completados / asignaciones) * 100) if asignaciones else 0
    return {
        "id": id_,
        "nombre": nombre or "Sin nombre",
        "ugel": ugel,
        "provincia": provincia,
        "asignaciones": asignaciones,
        "completados": completados,
        "avance_pct": min(100, pct),
    }


@router.get("/distribucion")
async def distribucion_metricas(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_modulo("metricas")),
):
    """
    Distribuciones para los gráficos del dashboard, scoped por rol:
    - `avance_por_ugel`: avance de asignaciones por UGEL.
    - `avance_por_institucion`: avance de asignaciones por IE.
    - `estudiantes_por_institucion`: estudiantes activos por IE.

    El avance se calcula como asignaciones con al menos un intento
    completado sobre el total de asignaciones.
    """
    rol = RolCodigo(current_user.rol_codigo)
    ugel_id = current_user.ugel_id
    ie_id = current_user.institucion_educativa_id

    ugel_ids: list[int] | None = None
    ie_ids: list[int] | None = None
    docente_id: int | None = None

    if rol in DRE_ROLES:
        pass
    elif rol == RolCodigo.RESPONSABLE_UGEL and ugel_id:
        ugel_ids = [ugel_id]
    elif rol in {RolCodigo.DIRECTOR, RolCodigo.AUXILIAR} and ie_id:
        ie_ids = [ie_id]
    elif rol == RolCodigo.DOCENTE:
        docente_id = current_user.id
        if ie_id:
            ie_ids = [ie_id]
    else:
        return {
            "rol": rol.value,
            "avance_por_ugel": [],
            "avance_por_institucion": [],
            "estudiantes_por_institucion": [],
            "totales": {
                "asignaciones": 0,
                "completados": 0,
                "estudiantes": 0,
                "instituciones": 0,
            },
        }

    avance_por_ugel: list[dict] = []
    avance_por_institucion: list[dict] = []
    estudiantes_por_institucion: list[dict] = []

    # ── Scope de asignaciones ─────────────────────────────────────────────────
    filtros_asig = [AsignacionExamen.institucion_educativa_id.isnot(None)]
    if ie_ids is not None:
        filtros_asig.append(AsignacionExamen.institucion_educativa_id.in_(ie_ids))
    if ugel_ids is not None:
        filtros_asig.append(InstitucionEducativa.ugel_id.in_(ugel_ids))
    if docente_id is not None:
        filtros_asig.append(AsignacionExamen.asignado_por_id == docente_id)

    try:
        # ── Avance por UGEL ───────────────────────────────────────────────────
        # La DRE ve todas las UGELes activas, incluidas las que aún no tienen
        # asignaciones (0 %), para evidenciar brechas de cobertura.
        if rol in DRE_ROLES:
            stmt_ugel = (
                select(
                    Ugel.id,
                    Ugel.nombre,
                    Provincia.nombre.label("provincia"),
                    func.count(func.distinct(AsignacionExamen.id)).label("asignaciones"),
                    func.count(func.distinct(IntentoExamen.asignacion_id)).label("completados"),
                )
                .select_from(Ugel)
                .outerjoin(Provincia, Ugel.provincia_id == Provincia.id)
                .outerjoin(InstitucionEducativa, InstitucionEducativa.ugel_id == Ugel.id)
                .outerjoin(
                    AsignacionExamen,
                    AsignacionExamen.institucion_educativa_id == InstitucionEducativa.id,
                )
                .outerjoin(
                    IntentoExamen,
                    (IntentoExamen.asignacion_id == AsignacionExamen.id)
                    & (IntentoExamen.estado == "completado"),
                )
                .where(Ugel.is_active == True)
                .group_by(Ugel.id, Ugel.nombre, Provincia.nombre)
                .order_by(Ugel.nombre)
            )
        else:
            stmt_ugel = (
                select(
                    Ugel.id,
                    Ugel.nombre,
                    Provincia.nombre.label("provincia"),
                    func.count(func.distinct(AsignacionExamen.id)).label("asignaciones"),
                    func.count(func.distinct(IntentoExamen.asignacion_id)).label("completados"),
                )
                .select_from(AsignacionExamen)
                .join(InstitucionEducativa, AsignacionExamen.institucion_educativa_id == InstitucionEducativa.id)
                .join(Ugel, InstitucionEducativa.ugel_id == Ugel.id)
                .outerjoin(Provincia, Ugel.provincia_id == Provincia.id)
                .outerjoin(
                    IntentoExamen,
                    (IntentoExamen.asignacion_id == AsignacionExamen.id)
                    & (IntentoExamen.estado == "completado"),
                )
                .where(*filtros_asig)
                .group_by(Ugel.id, Ugel.nombre, Provincia.nombre)
                .order_by(Ugel.nombre)
            )
        filas_ugel = (await db.execute(stmt_ugel)).all()
        avance_por_ugel = [
            _item_avance(f[0], f[1], f[3], f[4], provincia=f[2]) for f in filas_ugel
        ]

        # ── Avance por institución ────────────────────────────────────────────
        stmt_ie = (
            select(
                InstitucionEducativa.id,
                InstitucionEducativa.nombre,
                Ugel.nombre.label("ugel"),
                Provincia.nombre.label("provincia"),
                func.count(func.distinct(AsignacionExamen.id)).label("asignaciones"),
                func.count(func.distinct(IntentoExamen.asignacion_id)).label("completados"),
            )
            .select_from(AsignacionExamen)
            .join(InstitucionEducativa, AsignacionExamen.institucion_educativa_id == InstitucionEducativa.id)
            .join(Ugel, InstitucionEducativa.ugel_id == Ugel.id)
            .outerjoin(Provincia, Ugel.provincia_id == Provincia.id)
            .outerjoin(
                IntentoExamen,
                (IntentoExamen.asignacion_id == AsignacionExamen.id)
                & (IntentoExamen.estado == "completado"),
            )
            .where(*filtros_asig)
            .group_by(InstitucionEducativa.id, InstitucionEducativa.nombre, Ugel.nombre, Provincia.nombre)
            .order_by(func.count(func.distinct(AsignacionExamen.id)).desc(), InstitucionEducativa.nombre)
        )
        filas_ie = (await db.execute(stmt_ie)).all()
        avance_por_institucion = [
            _item_avance(f[0], f[1], f[4], f[5], ugel=f[2], provincia=f[3]) for f in filas_ie
        ]
    except Exception:
        # Tablas de la fase 3 pueden no existir en instalaciones antiguas.
        logger.exception("No se pudo calcular el avance por UGEL/institución")
        avance_por_ugel = []
        avance_por_institucion = []

    # ── Estudiantes por institución ───────────────────────────────────────────
    # Un docente sin IE asignada no puede ver estudiantes.
    if not (rol == RolCodigo.DOCENTE and ie_id is None):
        try:
            filtros_est = [
                Estudiante.is_active == True,
                Estudiante.institucion_educativa_id.isnot(None),
            ]
            if ie_ids is not None:
                filtros_est.append(Estudiante.institucion_educativa_id.in_(ie_ids))
            if ugel_ids is not None:
                filtros_est.append(InstitucionEducativa.ugel_id.in_(ugel_ids))

            stmt_est = (
                select(
                    InstitucionEducativa.id,
                    InstitucionEducativa.nombre,
                    Ugel.nombre.label("ugel"),
                    Provincia.nombre.label("provincia"),
                    func.count(Estudiante.id).label("estudiantes"),
                )
                .select_from(Estudiante)
                .join(InstitucionEducativa, Estudiante.institucion_educativa_id == InstitucionEducativa.id)
                .join(Ugel, InstitucionEducativa.ugel_id == Ugel.id)
                .outerjoin(Provincia, Ugel.provincia_id == Provincia.id)
                .where(*filtros_est)
                .group_by(InstitucionEducativa.id, InstitucionEducativa.nombre, Ugel.nombre, Provincia.nombre)
                .order_by(func.count(Estudiante.id).desc(), InstitucionEducativa.nombre)
            )
            filas_est = (await db.execute(stmt_est)).all()
            estudiantes_por_institucion = [
                {
                    "id": f[0],
                    "nombre": f[1] or "Sin nombre",
                    "ugel": f[2],
                    "provincia": f[3],
                    "estudiantes": int(f[4] or 0),
                }
                for f in filas_est
            ]
        except Exception:
            logger.exception("No se pudo calcular los estudiantes por institución")
            estudiantes_por_institucion = []

    return {
        "rol": rol.value,
        "avance_por_ugel": avance_por_ugel,
        "avance_por_institucion": avance_por_institucion,
        "estudiantes_por_institucion": estudiantes_por_institucion,
        "totales": {
            "asignaciones": sum(a["asignaciones"] for a in avance_por_ugel),
            "completados": sum(a["completados"] for a in avance_por_ugel),
            "estudiantes": sum(e["estudiantes"] for e in estudiantes_por_institucion),
            "instituciones": len(estudiantes_por_institucion),
        },
    }


# ─── Métricas académicas: promedios, niveles de logro y dominio de desempeños ──

_NIVELES_4 = ["pre_inicio", "inicio", "proceso", "satisfactorio"]
_CNEB_A_4NIVELES = {"AD": "satisfactorio", "A": "proceso", "B": "inicio", "C": "pre_inicio"}
_AREA_METRICA = {"lectura": "comunicacion", "matematica": "matematica"}


def _promedio_academico(filas: list[dict]) -> dict:
    """Promedio de puntaje/nota y nivel CNEB para un conjunto de intentos."""
    puntajes = [f["puntaje"] for f in filas if f["puntaje"] is not None]
    notas = [f["nota"] for f in filas if f["nota"] is not None]
    if not puntajes:
        return {
            "evaluados": len(filas),
            "puntaje_promedio": None,
            "nota_promedio": None,
            "nivel_cneb": None,
        }
    puntaje_promedio = round(sum(puntajes) / len(puntajes), 2)
    nota_promedio = round(sum(notas) / len(notas), 2) if notas else None
    return {
        "evaluados": len(filas),
        "puntaje_promedio": puntaje_promedio,
        "nota_promedio": nota_promedio,
        "nivel_cneb": clasificar(puntaje_promedio)["nivel_cneb"],
    }


@router.get("/academico")
async def metricas_academicas(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_modulo("metricas")),
):
    """Rendimiento académico consolidado y scoped por rol.

    Devuelve, para el ámbito del usuario autenticado:
    - Promedios de puntaje y nota vigesimal por área (Comunicación / Matemática).
    - Distribución de estudiantes por nivel de logro CNEB (último intento por
      asignación y estudiante).
    - Dominio acumulado por desempeño CNEB, calculado sobre todas las respuestas
      calificadas de los intentos completados.

    El scope replica el de las demás métricas: DRE ve todo el sistema, UGEL sus
    instituciones, director/auxiliar su IE y docente únicamente sus asignaciones.
    """
    rol = RolCodigo(current_user.rol_codigo)
    ugel_id = current_user.ugel_id
    ie_id = current_user.institucion_educativa_id
    DRE_ROLES = {RolCodigo.ESPECIALISTA_DRE_COMUNICACION, RolCodigo.ESPECIALISTA_DRE_MATEMATICA}
    GESTORES_IE = {RolCodigo.DIRECTOR, RolCodigo.AUXILIAR}

    condiciones = []
    if rol in DRE_ROLES:
        pass
    elif rol == RolCodigo.RESPONSABLE_UGEL and ugel_id:
        ie_ids_r = await db.execute(
            select(InstitucionEducativa.id).where(InstitucionEducativa.ugel_id == ugel_id)
        )
        condiciones.append(
            AsignacionExamen.institucion_educativa_id.in_([r[0] for r in ie_ids_r.all()])
        )
    elif rol in GESTORES_IE and ie_id:
        condiciones.append(AsignacionExamen.institucion_educativa_id == ie_id)
    else:
        condiciones.append(AsignacionExamen.asignado_por_id == current_user.id)

    asig_q = select(AsignacionExamen.id, AsignacionExamen.tipo_examen)
    if condiciones:
        asig_q = asig_q.where(*condiciones)
    asignaciones = (await db.execute(asig_q)).all()
    asig_area = {f[0]: _AREA_METRICA.get(f[1], f[1]) for f in asignaciones}
    asig_ids = list(asig_area)

    vacio = {
        "rol": rol.value,
        "total_evaluados": 0,
        "promedios": {
            "general": _promedio_academico([]),
            "comunicacion": _promedio_academico([]),
            "matematica": _promedio_academico([]),
        },
        "distribucion_niveles": {**{n: 0 for n in _NIVELES_4}, "total": 0},
        "dominio_desempenos": {"comunicacion": [], "matematica": []},
    }
    if not asig_ids:
        return vacio

    # Último intento completado por (asignación, estudiante): base de promedios
    # y de la distribución de niveles, para no sobrerrepresentar a quien repite.
    intentos_r = await db.execute(
        select(
            IntentoExamen.asignacion_id,
            IntentoExamen.estudiante_id,
            IntentoExamen.numero_intento,
            IntentoExamen.puntaje_total,
            IntentoExamen.nota_vigesimal,
            IntentoExamen.nivel_cneb,
        )
        .where(
            IntentoExamen.asignacion_id.in_(asig_ids),
            IntentoExamen.estado == "completado",
        )
        .order_by(
            IntentoExamen.asignacion_id,
            IntentoExamen.estudiante_id,
            IntentoExamen.numero_intento.desc(),
        )
    )
    ultimos: dict = {}
    for asig_id, est_id, _num, puntaje, nota, nivel_cneb in intentos_r.all():
        clave = (asig_id, est_id)
        if clave in ultimos:
            continue
        ultimos[clave] = {
            "area": asig_area.get(asig_id),
            "puntaje": puntaje,
            "nota": nota,
            "nivel_cneb": nivel_cneb,
        }

    filas = list(ultimos.values())
    distribucion = {n: 0 for n in _NIVELES_4}
    for fila in filas:
        cneb = fila["nivel_cneb"] or (
            nota_a_nivel(fila["nota"]) if fila["nota"] is not None else None
        )
        nivel = _CNEB_A_4NIVELES.get(cneb)
        if nivel:
            distribucion[nivel] += 1

    # Dominio acumulado por desempeño: todas las respuestas calificadas.
    area_expr = case(
        (PreguntaExamen.examen_lectura_id.isnot(None), "comunicacion"),
        else_="matematica",
    )
    dominio_r = await db.execute(
        select(
            area_expr.label("area"),
            PreguntaExamen.desempeno_codigo,
            func.max(PreguntaExamen.desempeno_descripcion),
            func.count(RespuestaIntento.id),
            func.sum(case((RespuestaIntento.es_correcta == True, 1), else_=0)),
        )
        .select_from(RespuestaIntento)
        .join(PreguntaExamen, PreguntaExamen.id == RespuestaIntento.pregunta_id)
        .join(IntentoExamen, IntentoExamen.id == RespuestaIntento.intento_id)
        .where(
            IntentoExamen.asignacion_id.in_(asig_ids),
            IntentoExamen.estado == "completado",
            PreguntaExamen.desempeno_codigo.isnot(None),
            PreguntaExamen.desempeno_codigo != "",
        )
        .group_by(area_expr, PreguntaExamen.desempeno_codigo)
        .order_by(area_expr, PreguntaExamen.desempeno_codigo)
    )
    dominio = {"comunicacion": [], "matematica": []}
    for area, codigo, descripcion, total, correctas in dominio_r.all():
        total = int(total or 0)
        correctas = int(correctas or 0)
        porcentaje = round((correctas / total * 100) if total else 0, 2)
        dominio.setdefault(area, []).append({
            "desempeno_codigo": codigo,
            "desempeno_descripcion": descripcion,
            "total_preguntas": total,
            "correctas": correctas,
            "porcentaje": porcentaje,
            "nivel_cneb": nota_a_nivel(clasificar(porcentaje)["nota_vigesimal"])
            if total else None,
        })

    return {
        "rol": rol.value,
        "total_evaluados": len(filas),
        "promedios": {
            "general": _promedio_academico(filas),
            "comunicacion": _promedio_academico(
                [f for f in filas if f["area"] == "comunicacion"]
            ),
            "matematica": _promedio_academico(
                [f for f in filas if f["area"] == "matematica"]
            ),
        },
        "distribucion_niveles": {**distribucion, "total": sum(distribucion.values())},
        "dominio_desempenos": dominio,
    }
