"""
Monitoreo de sesiones activas y estadísticas de acceso.

Acceso exclusivo de los especialistas DRE (superusuarios) con el módulo
`monitoreo` habilitado.
"""
from datetime import date, datetime, time, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_superuser
from app.core.database import get_db
from app.models.db_models import InstitucionEducativa, Ugel
from app.models.sesion import SesionAcceso
from app.models.usuario import Usuario
from app.schemas.monitoreo import (
    EstadisticasMonitoreo,
    ConteoItem,
    PuntoSerie,
    ResumenMonitoreo,
    SesionAccesoOut,
)
from app.schemas.pagination import PaginatedResponse

router = APIRouter()

# Minutos sin actividad tras los cuales una sesión deja de considerarse activa.
VENTANA_ACTIVA_MINUTOS = 15


async def get_monitoreo_user(current_user: Usuario = Depends(get_current_superuser)) -> Usuario:
    """Solo especialistas DRE con el módulo 'monitoreo' habilitado."""
    if not current_user.tiene_modulo("monitoreo"):
        raise HTTPException(status_code=403, detail="Sin acceso al módulo 'monitoreo'")
    return current_user


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: Optional[datetime]) -> Optional[datetime]:
    """Normaliza datetimes naive (SQLite) a UTC aware."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _filtro_activo(ahora: datetime):
    return and_(
        SesionAcceso.exito.is_(True),
        SesionAcceso.is_active.is_(True),
        SesionAcceso.logout_at.is_(None),
        SesionAcceso.last_activity.is_not(None),
        SesionAcceso.last_activity >= ahora - timedelta(minutes=VENTANA_ACTIVA_MINUTOS),
    )


async def _resolver_nombres(db: AsyncSession, sesiones: List[SesionAcceso]):
    ie_ids = {s.institucion_educativa_id for s in sesiones if s.institucion_educativa_id}
    ugel_ids = {s.ugel_id for s in sesiones if s.ugel_id}
    ie_map: dict = {}
    ugel_map: dict = {}

    if ie_ids:
        rows = await db.execute(
            select(InstitucionEducativa.id, InstitucionEducativa.nombre).where(
                InstitucionEducativa.id.in_(ie_ids)
            )
        )
        ie_map = {r[0]: r[1] for r in rows.all()}
    if ugel_ids:
        rows = await db.execute(
            select(Ugel.id, Ugel.nombre).where(Ugel.id.in_(ugel_ids))
        )
        ugel_map = {r[0]: r[1] for r in rows.all()}

    return ie_map, ugel_map


def _to_out(
    s: SesionAcceso,
    ie_map: dict,
    ugel_map: dict,
    ahora: datetime,
) -> SesionAccesoOut:
    last = _aware(s.last_activity)
    login = _aware(s.login_at)
    logout = _aware(s.logout_at)

    en_linea = bool(
        s.exito
        and s.logout_at is None
        and s.is_active
        and last is not None
        and last >= ahora - timedelta(minutes=VENTANA_ACTIVA_MINUTOS)
    )

    duracion = None
    referencia = logout or last
    if login and referencia:
        duracion = max(0, int((referencia - login).total_seconds() // 60))

    return SesionAccesoOut(
        id=s.id,
        exito=bool(s.exito),
        motivo=s.motivo,
        tipo_usuario=s.tipo_usuario,
        usuario_id=s.usuario_id,
        identificador=s.identificador,
        nombres=s.nombres,
        apellidos=s.apellidos,
        rol_codigo=s.rol_codigo,
        institucion_educativa_id=s.institucion_educativa_id,
        institucion_nombre=ie_map.get(s.institucion_educativa_id),
        ugel_id=s.ugel_id,
        ugel_nombre=ugel_map.get(s.ugel_id),
        ip=s.ip,
        dispositivo=s.dispositivo,
        sistema_operativo=s.sistema_operativo,
        navegador=s.navegador,
        es_movil=bool(s.es_movil),
        login_at=s.login_at,
        last_activity=s.last_activity,
        logout_at=s.logout_at,
        is_active=bool(s.is_active),
        en_linea=en_linea,
        duracion_minutos=duracion,
    )


async def _serializar(db: AsyncSession, sesiones: List[SesionAcceso]) -> List[SesionAccesoOut]:
    ie_map, ugel_map = await _resolver_nombres(db, sesiones)
    ahora = _utcnow()
    return [_to_out(s, ie_map, ugel_map, ahora) for s in sesiones]


async def _conteo_por(db: AsyncSession, columna, base_filtro) -> List[tuple]:
    rows = await db.execute(
        select(columna, func.count(SesionAcceso.id))
        .where(base_filtro)
        .group_by(columna)
        .order_by(func.count(SesionAcceso.id).desc())
    )
    return rows.all()


@router.get("/resumen", response_model=ResumenMonitoreo)
async def resumen_monitoreo(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_monitoreo_user),
):
    """KPIs de sesiones activas, accesos de hoy y distribución por rol/UGEL/IE."""
    ahora = _utcnow()
    activo = _filtro_activo(ahora)
    inicio_hoy = ahora.replace(hour=0, minute=0, second=0, microsecond=0)

    activas = (
        await db.execute(select(SesionAcceso).where(activo))
    ).scalars().all()

    sesiones_activas = len(activas)
    estudiantes_activos = sum(1 for s in activas if s.rol_codigo == "estudiante")
    staff_activos = sesiones_activas - estudiantes_activos

    logins_hoy = (
        await db.execute(
            select(func.count(SesionAcceso.id)).where(
                SesionAcceso.exito.is_(True), SesionAcceso.login_at >= inicio_hoy
            )
        )
    ).scalar() or 0
    fallidos_hoy = (
        await db.execute(
            select(func.count(SesionAcceso.id)).where(
                SesionAcceso.exito.is_(False), SesionAcceso.login_at >= inicio_hoy
            )
        )
    ).scalar() or 0
    sesiones_hoy = (
        await db.execute(
            select(func.count(SesionAcceso.id)).where(SesionAcceso.login_at >= inicio_hoy)
        )
    ).scalar() or 0

    # Activos por rol
    rol_rows = await _conteo_por(db, SesionAcceso.rol_codigo, activo)
    activos_por_rol = [
        ConteoItem(clave=r[0] or "sin_rol", total=r[1]) for r in rol_rows
    ]

    # Activos por UGEL (con nombre)
    ugel_rows = await _conteo_por(db, SesionAcceso.ugel_id, activo)
    ugel_ids = [r[0] for r in ugel_rows if r[0] is not None]
    ugel_map: dict = {}
    if ugel_ids:
        rows = await db.execute(select(Ugel.id, Ugel.nombre).where(Ugel.id.in_(ugel_ids)))
        ugel_map = {r[0]: r[1] for r in rows.all()}
    activos_por_ugel = [
        ConteoItem(clave=ugel_map.get(r[0], "Sin UGEL") if r[0] else "Sin UGEL", total=r[1])
        for r in ugel_rows
    ]

    # Top instituciones activas
    ie_rows = await _conteo_por(db, SesionAcceso.institucion_educativa_id, activo)
    ie_ids = [r[0] for r in ie_rows if r[0] is not None]
    ie_map: dict = {}
    if ie_ids:
        rows = await db.execute(
            select(InstitucionEducativa.id, InstitucionEducativa.nombre).where(
                InstitucionEducativa.id.in_(ie_ids)
            )
        )
        ie_map = {r[0]: r[1] for r in rows.all()}
    top_instituciones = [
        ConteoItem(clave=ie_map.get(r[0], "Sin IE") if r[0] else "Sin IE", total=r[1])
        for r in ie_rows[:8]
    ]

    return ResumenMonitoreo(
        sesiones_activas=sesiones_activas,
        estudiantes_activos=estudiantes_activos,
        staff_activos=staff_activos,
        logins_hoy=logins_hoy,
        fallidos_hoy=fallidos_hoy,
        sesiones_hoy=sesiones_hoy,
        activos_por_rol=activos_por_rol,
        activos_por_ugel=activos_por_ugel,
        top_instituciones=top_instituciones,
        ultima_actualizacion=ahora,
    )


@router.get("/sesiones-activas", response_model=List[SesionAccesoOut])
async def sesiones_activas(
    q: Optional[str] = Query(None, description="Buscar por nombre, DNI o código"),
    rol: Optional[str] = Query(None, description="Filtrar por rol"),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_monitoreo_user),
):
    """Listado de usuarios con sesión activa y su metadata de conexión."""
    ahora = _utcnow()
    stmt = select(SesionAcceso).where(_filtro_activo(ahora))

    if rol:
        stmt = stmt.where(SesionAcceso.rol_codigo == rol)
    if q:
        term = f"%{q}%"
        stmt = stmt.where(
            (SesionAcceso.identificador.ilike(term))
            | (SesionAcceso.nombres.ilike(term))
            | (SesionAcceso.apellidos.ilike(term))
        )

    stmt = stmt.order_by(SesionAcceso.last_activity.desc())
    sesiones = (await db.execute(stmt)).scalars().all()
    return await _serializar(db, list(sesiones))


@router.get("/sesiones", response_model=PaginatedResponse[SesionAccesoOut])
async def listar_sesiones(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    q: Optional[str] = Query(None, description="Buscar por nombre, DNI o código"),
    rol: Optional[str] = Query(None),
    ie_id: Optional[int] = Query(None),
    ugel_id: Optional[int] = Query(None),
    fecha_desde: Optional[date] = Query(None),
    fecha_hasta: Optional[date] = Query(None),
    solo_fallidos: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_monitoreo_user),
):
    """Histórico paginado de accesos (exitosos y fallidos) con filtros."""
    filtros = []
    if rol:
        filtros.append(SesionAcceso.rol_codigo == rol)
    if ie_id:
        filtros.append(SesionAcceso.institucion_educativa_id == ie_id)
    if ugel_id:
        filtros.append(SesionAcceso.ugel_id == ugel_id)
    if solo_fallidos:
        filtros.append(SesionAcceso.exito.is_(False))
    if fecha_desde:
        filtros.append(
            SesionAcceso.login_at >= datetime.combine(fecha_desde, time.min, tzinfo=timezone.utc)
        )
    if fecha_hasta:
        filtros.append(
            SesionAcceso.login_at <= datetime.combine(fecha_hasta, time.max, tzinfo=timezone.utc)
        )
    if q:
        term = f"%{q}%"
        filtros.append(
            (SesionAcceso.identificador.ilike(term))
            | (SesionAcceso.nombres.ilike(term))
            | (SesionAcceso.apellidos.ilike(term))
        )

    where = and_(*filtros) if filtros else None

    count_stmt = select(func.count(SesionAcceso.id))
    data_stmt = select(SesionAcceso)
    if where is not None:
        count_stmt = count_stmt.where(where)
        data_stmt = data_stmt.where(where)

    total = (await db.execute(count_stmt)).scalar() or 0
    data_stmt = data_stmt.order_by(SesionAcceso.login_at.desc()).offset((page - 1) * size).limit(size)
    sesiones = (await db.execute(data_stmt)).scalars().all()

    return PaginatedResponse[SesionAccesoOut](
        items=await _serializar(db, list(sesiones)),
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size if size else 0,
    )


@router.get("/estadisticas", response_model=EstadisticasMonitoreo)
async def estadisticas_monitoreo(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_monitoreo_user),
):
    """Series temporales y distribuciones de dispositivos/SO/navegadores/IE."""
    ahora = _utcnow()

    # ── Accesos por hora (últimas 24h) ───────────────────────────────────────
    desde_24h = ahora - timedelta(hours=24)
    rows = (
        await db.execute(
            select(SesionAcceso.login_at, SesionAcceso.exito).where(
                SesionAcceso.login_at >= desde_24h
            )
        )
    ).all()
    horas: dict = {}
    for login_at, exito in rows:
        dt = _aware(login_at)
        if not dt:
            continue
        key = dt.strftime("%Y-%m-%d %H:00")
        bucket = horas.setdefault(key, {"total": 0, "exitos": 0, "fallidos": 0})
        bucket["total"] += 1
        if exito:
            bucket["exitos"] += 1
        else:
            bucket["fallidos"] += 1
    accesos_por_hora = [
        PuntoSerie(periodo=k[-5:], total=v["total"], exitos=v["exitos"], fallidos=v["fallidos"])
        for k, v in sorted(horas.items())
    ]

    # ── Accesos por día (últimos 14 días) ────────────────────────────────────
    desde_14d = (ahora - timedelta(days=14)).replace(hour=0, minute=0, second=0, microsecond=0)
    rows = (
        await db.execute(
            select(SesionAcceso.login_at, SesionAcceso.exito).where(
                SesionAcceso.login_at >= desde_14d
            )
        )
    ).all()
    dias: dict = {}
    for login_at, exito in rows:
        dt = _aware(login_at)
        if not dt:
            continue
        key = dt.strftime("%Y-%m-%d")
        bucket = dias.setdefault(key, {"total": 0, "exitos": 0, "fallidos": 0})
        bucket["total"] += 1
        if exito:
            bucket["exitos"] += 1
        else:
            bucket["fallidos"] += 1
    accesos_por_dia = [
        PuntoSerie(periodo=k, total=v["total"], exitos=v["exitos"], fallidos=v["fallidos"])
        for k, v in sorted(dias.items())
    ]

    # ── Distribuciones (sesiones exitosas de los últimos 30 días) ────────────
    desde_30d = ahora - timedelta(days=30)
    base = and_(SesionAcceso.exito.is_(True), SesionAcceso.login_at >= desde_30d)

    dispositivos = [ConteoItem(clave=r[0] or "Desconocido", total=r[1]) for r in await _conteo_por(db, SesionAcceso.dispositivo, base)]
    sistemas = [ConteoItem(clave=r[0] or "Desconocido", total=r[1]) for r in await _conteo_por(db, SesionAcceso.sistema_operativo, base)]
    navegadores = [ConteoItem(clave=r[0] or "Desconocido", total=r[1]) for r in await _conteo_por(db, SesionAcceso.navegador, base)]

    ie_rows = await _conteo_por(db, SesionAcceso.institucion_educativa_id, base)
    ie_ids = [r[0] for r in ie_rows if r[0] is not None]
    ie_map: dict = {}
    if ie_ids:
        rows = await db.execute(
            select(InstitucionEducativa.id, InstitucionEducativa.nombre).where(
                InstitucionEducativa.id.in_(ie_ids)
            )
        )
        ie_map = {r[0]: r[1] for r in rows.all()}
    top_instituciones = [
        ConteoItem(clave=ie_map.get(r[0], "Sin IE") if r[0] else "Sin IE", total=r[1])
        for r in ie_rows[:8]
    ]

    return EstadisticasMonitoreo(
        accesos_por_hora=accesos_por_hora,
        accesos_por_dia=accesos_por_dia,
        dispositivos=dispositivos,
        sistemas_operativos=sistemas,
        navegadores=navegadores,
        top_instituciones=top_instituciones,
        ultima_actualizacion=ahora,
    )


@router.post("/sesiones/{sesion_id}/cerrar")
async def cerrar_sesion(
    sesion_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_monitoreo_user),
):
    """Fuerza el cierre de una sesión activa."""
    result = await db.execute(
        update(SesionAcceso)
        .where(SesionAcceso.id == sesion_id, SesionAcceso.logout_at.is_(None))
        .values(logout_at=_utcnow(), is_active=False)
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Sesión no encontrada o ya cerrada")
    return {"message": "Sesión cerrada"}
