"""
Rutas de gestión de estudiantes para administradores (DRE, UGEL y Director).

Permite:
- Listar estudiantes dentro del scope del usuario (con filtros).
- Reasignar el docente creador, la IE, el grado y/o la sección de la matrícula.
- Eliminar nóminas cargadas por error (con protección si hay intentos de examen).

Este módulo NO modifica el schema; opera sobre `estudiantes` y `matriculas`.
"""
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_, delete
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field
import math
from datetime import datetime

from app.core.database import get_db
from app.models.db_models import (
    Matricula,
    InstitucionEducativa,
    Grado,
    IntentoExamen,
    RespuestaIntento,
    ProgresoEstudiante,
)
from app.models.estudiante import Estudiante
from app.models.usuario import Usuario
from app.models.enums import RolCodigo
from app.api.dependencies import require_role
from app.schemas.pagination import PaginatedResponse
from app.services.matricula_service import crear_matricula

router = APIRouter()

DRE_ROLES = (RolCodigo.ESPECIALISTA_DRE_COMUNICACION, RolCodigo.ESPECIALISTA_DRE_MATEMATICA)
GESTOR_ROLES = (*DRE_ROLES, RolCodigo.RESPONSABLE_UGEL, RolCodigo.DIRECTOR)
get_gestor = require_role(*GESTOR_ROLES)


# ─── Schemas ─────────────────────────────────────────────────────────────────

class EstudianteGestionItem(BaseModel):
    id: int
    dni: Optional[str] = None
    codigo_estudiante: Optional[str] = None
    nombres: Optional[str] = None
    apellidos: Optional[str] = None
    is_active: bool
    creado_por_id: Optional[int] = None
    creado_por_nombre: Optional[str] = None
    institucion_educativa_id: Optional[int] = None
    institucion_nombre: Optional[str] = None
    ugel_id: Optional[int] = None
    grado_id: Optional[int] = None
    grado_nombre: Optional[str] = None
    seccion: Optional[str] = None
    año_escolar: Optional[int] = None
    intentos: int = 0


class TransferirEstudiantesRequest(BaseModel):
    estudiante_ids: List[int] = Field(..., min_length=1, max_length=1000)
    nuevo_creador_id: Optional[int] = None
    nueva_institucion_educativa_id: Optional[int] = None
    nuevo_grado_id: Optional[int] = None
    nueva_seccion: Optional[str] = Field(None, min_length=1, max_length=10)
    año_escolar: Optional[int] = None


class TransferirEstudiantesResponse(BaseModel):
    actualizados: int


class EliminarEstudiantesRequest(BaseModel):
    estudiante_ids: List[int] = Field(..., min_length=1, max_length=1000)
    forzar: bool = False


class EliminarEstudiantesResponse(BaseModel):
    eliminados: int
    intentos_eliminados: int


# ─── Helpers de scope ────────────────────────────────────────────────────────

def _rol(user: Usuario) -> RolCodigo:
    return RolCodigo(user.rol_codigo)


def _estudiante_en_scope(user: Usuario, est: Estudiante) -> bool:
    rol = _rol(user)
    if rol in DRE_ROLES:
        return True
    ie = est.institucion_educativa
    if rol == RolCodigo.RESPONSABLE_UGEL:
        return bool(ie and ie.ugel_id == user.ugel_id)
    return est.institucion_educativa_id == user.institucion_educativa_id


def _validar_ie(user: Usuario, ie: InstitucionEducativa) -> None:
    rol = _rol(user)
    if rol in DRE_ROLES:
        return
    if rol == RolCodigo.RESPONSABLE_UGEL:
        if ie.ugel_id != user.ugel_id:
            raise HTTPException(403, "La institución no pertenece a tu UGEL")
        return
    if ie.id != user.institucion_educativa_id:
        raise HTTPException(403, "La institución no es la tuya")


def _validar_usuario(user: Usuario, objetivo: Usuario) -> None:
    rol = _rol(user)
    if rol in DRE_ROLES:
        return
    if rol == RolCodigo.RESPONSABLE_UGEL:
        if objetivo.ugel_id != user.ugel_id:
            raise HTTPException(403, "El usuario destino no pertenece a tu UGEL")
        return
    if objetivo.institucion_educativa_id != user.institucion_educativa_id:
        raise HTTPException(403, "El usuario destino no pertenece a tu institución")


def _nombre_usuario(u: Optional[Usuario]) -> Optional[str]:
    if not u:
        return None
    nombre = " ".join(filter(None, [u.apellidos, u.nombres])).strip()
    return nombre or u.dni or None


# ─── Listado ─────────────────────────────────────────────────────────────────

@router.get("", response_model=PaginatedResponse[EstudianteGestionItem])
async def listar_estudiantes(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=1000),
    q: Optional[str] = None,
    institucion_educativa_id: Optional[int] = None,
    grado_id: Optional[int] = None,
    seccion: Optional[str] = None,
    creado_por_id: Optional[int] = None,
    año_escolar: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_gestor),
):
    rol = _rol(current_user)

    joins = (
        select(Estudiante, Matricula, InstitucionEducativa, Usuario)
        .select_from(Estudiante)
        .outerjoin(
            Matricula,
            and_(Matricula.estudiante_id == Estudiante.id, Matricula.is_active == True),
        )
        .outerjoin(InstitucionEducativa, InstitucionEducativa.id == Estudiante.institucion_educativa_id)
        .outerjoin(Usuario, Usuario.id == Estudiante.creado_por_id)
        .options(selectinload(Matricula.grado))
    )

    condiciones = []
    if rol == RolCodigo.RESPONSABLE_UGEL:
        condiciones.append(InstitucionEducativa.ugel_id == current_user.ugel_id)
    elif rol not in DRE_ROLES:
        condiciones.append(Estudiante.institucion_educativa_id == current_user.institucion_educativa_id)

    if institucion_educativa_id:
        condiciones.append(Estudiante.institucion_educativa_id == institucion_educativa_id)
    if grado_id:
        condiciones.append(Matricula.grado_id == grado_id)
    if seccion:
        condiciones.append(Matricula.seccion == seccion)
    if creado_por_id:
        condiciones.append(Estudiante.creado_por_id == creado_por_id)
    if año_escolar:
        condiciones.append(Matricula.año_escolar == año_escolar)
    if q:
        like = f"%{q}%"
        condiciones.append(
            or_(
                Estudiante.nombres.ilike(like),
                Estudiante.apellidos.ilike(like),
                Estudiante.dni.ilike(like),
                Estudiante.codigo_estudiante.ilike(like),
            )
        )

    if condiciones:
        joins = joins.where(*condiciones)

    count_stmt = select(func.count()).select_from(joins.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = (
        joins.order_by(Estudiante.apellidos, Estudiante.nombres)
        .offset((page - 1) * size)
        .limit(size)
    )
    rows = (await db.execute(stmt)).all()

    ids = [e.id for e, _, _, _ in rows]
    intentos_map: dict[int, int] = {}
    if ids:
        r = await db.execute(
            select(IntentoExamen.estudiante_id, func.count(IntentoExamen.id))
            .where(IntentoExamen.estudiante_id.in_(ids))
            .group_by(IntentoExamen.estudiante_id)
        )
        intentos_map = {est_id: cnt for est_id, cnt in r.all()}

    items = [
        EstudianteGestionItem(
            id=e.id,
            dni=e.dni,
            codigo_estudiante=e.codigo_estudiante,
            nombres=e.nombres,
            apellidos=e.apellidos,
            is_active=e.is_active,
            creado_por_id=e.creado_por_id,
            creado_por_nombre=_nombre_usuario(creador),
            institucion_educativa_id=e.institucion_educativa_id,
            institucion_nombre=ie.nombre if ie else None,
            ugel_id=ie.ugel_id if ie else None,
            grado_id=m.grado_id if m else None,
            grado_nombre=m.grado.nombre if m and m.grado else None,
            seccion=m.seccion if m else None,
            año_escolar=m.año_escolar if m else None,
            intentos=intentos_map.get(e.id, 0),
        )
        for e, m, ie, creador in rows
    ]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size) if total > 0 else 0,
    )


# ─── Transferencia ───────────────────────────────────────────────────────────

@router.post("/transferir", response_model=TransferirEstudiantesResponse)
async def transferir_estudiantes(
    data: TransferirEstudiantesRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_gestor),
):
    ids = list(dict.fromkeys(data.estudiante_ids))

    estudiantes = (
        await db.execute(select(Estudiante).where(Estudiante.id.in_(ids)))
    ).scalars().all()
    if len(estudiantes) != len(ids):
        encontrados = {e.id for e in estudiantes}
        faltantes = [str(i) for i in ids if i not in encontrados]
        raise HTTPException(404, f"Estudiantes no encontrados: {', '.join(faltantes[:10])}")

    for est in estudiantes:
        if not _estudiante_en_scope(current_user, est):
            raise HTTPException(403, "Uno o más estudiantes están fuera de tu alcance")

    creador = None
    if data.nuevo_creador_id:
        creador = (
            await db.execute(select(Usuario).where(Usuario.id == data.nuevo_creador_id))
        ).scalars().first()
        if not creador:
            raise HTTPException(404, "El usuario destino no existe")
        _validar_usuario(current_user, creador)

    ie = None
    if data.nueva_institucion_educativa_id:
        ie = (
            await db.execute(
                select(InstitucionEducativa).where(
                    InstitucionEducativa.id == data.nueva_institucion_educativa_id
                )
            )
        ).scalars().first()
        if not ie:
            raise HTTPException(404, "La institución destino no existe")
        _validar_ie(current_user, ie)

    grado = None
    if data.nuevo_grado_id:
        grado = (
            await db.execute(select(Grado).where(Grado.id == data.nuevo_grado_id))
        ).scalars().first()
        if not grado:
            raise HTTPException(404, "El grado destino no existe")

    if not any([
        data.nuevo_creador_id,
        data.nueva_institucion_educativa_id,
        data.nuevo_grado_id,
        data.nueva_seccion,
    ]):
        raise HTTPException(400, "Indica al menos un cambio a aplicar")

    año = data.año_escolar or datetime.now().year

    # Matrículas activas de los estudiantes seleccionados
    mats = (
        await db.execute(
            select(Matricula).where(
                Matricula.estudiante_id.in_(ids),
                Matricula.is_active == True,
            )
        )
    ).scalars().all()
    mats_por_estudiante: dict[int, list[Matricula]] = {}
    for m in mats:
        mats_por_estudiante.setdefault(m.estudiante_id, []).append(m)

    for est in estudiantes:
        if data.nuevo_creador_id:
            est.creado_por_id = data.nuevo_creador_id
        if ie:
            est.institucion_educativa_id = ie.id

        mats_est = mats_por_estudiante.get(est.id, [])
        for m in mats_est:
            if ie:
                m.institucion_educativa_id = ie.id
                m.ugel_id = ie.ugel_id
            if data.nuevo_grado_id:
                m.grado_id = data.nuevo_grado_id
            if data.nueva_seccion:
                m.seccion = data.nueva_seccion.strip()

        # Crear matrícula si el estudiante no tenía una activa y hay datos suficientes
        if not mats_est:
            ie_destino_id = ie.id if ie else est.institucion_educativa_id
            ie_destino = ie
            if not ie_destino and ie_destino_id:
                ie_destino = (
                    await db.execute(
                        select(InstitucionEducativa).where(InstitucionEducativa.id == ie_destino_id)
                    )
                ).scalars().first()
            grado_destino_id = data.nuevo_grado_id or (grado.id if grado else None)
            seccion_destino = data.nueva_seccion.strip() if data.nueva_seccion else None
            if ie_destino and grado_destino_id and seccion_destino:
                await crear_matricula(
                    db,
                    estudiante_id=est.id,
                    grado_id=grado_destino_id,
                    seccion=seccion_destino,
                    año_escolar=año,
                    institucion_educativa_id=ie_destino.id,
                    ugel_id=ie_destino.ugel_id,
                )

    await db.flush()
    return TransferirEstudiantesResponse(actualizados=len(estudiantes))


# ─── Eliminación ─────────────────────────────────────────────────────────────

@router.post("/eliminar", response_model=EliminarEstudiantesResponse)
async def eliminar_estudiantes(
    data: EliminarEstudiantesRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_gestor),
):
    ids = list(dict.fromkeys(data.estudiante_ids))

    estudiantes = (
        await db.execute(select(Estudiante).where(Estudiante.id.in_(ids)))
    ).scalars().all()
    if len(estudiantes) != len(ids):
        encontrados = {e.id for e in estudiantes}
        faltantes = [str(i) for i in ids if i not in encontrados]
        raise HTTPException(404, f"Estudiantes no encontrados: {', '.join(faltantes[:10])}")

    for est in estudiantes:
        if not _estudiante_en_scope(current_user, est):
            raise HTTPException(403, "Uno o más estudiantes están fuera de tu alcance")

    intento_ids = (
        await db.execute(
            select(IntentoExamen.id).where(IntentoExamen.estudiante_id.in_(ids))
        )
    ).scalars().all()

    if intento_ids and not data.forzar:
        raise HTTPException(
            400,
            f"{len(estudiantes)} estudiante(s) tienen {len(intento_ids)} intento(s) de examen registrados. "
            "Confirma la eliminación forzada para borrar también sus resultados.",
        )

    if intento_ids:
        await db.execute(
            delete(RespuestaIntento).where(RespuestaIntento.intento_id.in_(intento_ids))
        )
        await db.execute(
            delete(IntentoExamen).where(IntentoExamen.id.in_(intento_ids))
        )

    matricula_ids = (
        await db.execute(
            select(Matricula.id).where(Matricula.estudiante_id.in_(ids))
        )
    ).scalars().all()

    if matricula_ids:
        await db.execute(
            delete(ProgresoEstudiante).where(ProgresoEstudiante.matricula_id.in_(matricula_ids))
        )
        await db.execute(
            delete(Matricula).where(Matricula.id.in_(matricula_ids))
        )

    await db.execute(delete(Estudiante).where(Estudiante.id.in_(ids)))
    await db.flush()

    return EliminarEstudiantesResponse(
        eliminados=len(estudiantes),
        intentos_eliminados=len(intento_ids),
    )
