"""
Rutas de gestión organizacional: UGELes e Instituciones Educativas.
"""
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, delete
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.models.db_models import Ugel, InstitucionEducativa, InstitucionNivel, Grado, ExamenLectura, ExamenMatematica, AsignacionExamen, IntentoExamen
from app.models.usuario import Usuario
from app.models.enums import RolCodigo
from app.api.dependencies import get_current_active_user, require_role

router = APIRouter()

DRE_ROLES = (RolCodigo.ESPECIALISTA_DRE_COMUNICACION, RolCodigo.ESPECIALISTA_DRE_MATEMATICA)
DRE_UGEL_ROLES = (*DRE_ROLES, RolCodigo.RESPONSABLE_UGEL)


# ─── Schemas ─────────────────────────────────────────────────────────────────

class UgelCreate(BaseModel):
    codigo: str
    nombre: str
    provincia_id: Optional[int] = None
    is_active: bool = True


class UgelUpdate(BaseModel):
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    provincia_id: Optional[int] = None
    is_active: Optional[bool] = None


class UgelResponse(BaseModel):
    id: int
    codigo: str
    nombre: str
    provincia_id: Optional[int] = None
    provincia_nombre: Optional[str] = None
    is_active: bool
    fecha_creacion: Optional[datetime] = None

    class Config:
        from_attributes = True


NIVELES_VALIDOS = {"inicial", "primaria", "secundaria"}


class IECreate(BaseModel):
    codigo_modular: str
    nombre: str
    nivel_educativo: List[str]  # ["inicial"], ["primaria","secundaria"], etc.
    direccion: Optional[str] = None
    ugel_id: int
    distrito_id: Optional[int] = None
    is_active: bool = True


class IEUpdate(BaseModel):
    codigo_modular: Optional[str] = None
    nombre: Optional[str] = None
    nivel_educativo: Optional[List[str]] = None
    direccion: Optional[str] = None
    ugel_id: Optional[int] = None
    distrito_id: Optional[int] = None
    is_active: Optional[bool] = None


class IEResponse(BaseModel):
    id: int
    codigo_modular: str
    nombre: str
    nivel_educativo: List[str]
    direccion: Optional[str] = None
    ugel_id: int
    ugel_nombre: Optional[str] = None
    distrito_id: Optional[int] = None
    distrito_nombre: Optional[str] = None
    is_active: bool
    fecha_creacion: Optional[datetime] = None

    class Config:
        from_attributes = True


class GradoResponse(BaseModel):
    id: int
    nombre: str
    numero: int
    nivel: str
    orden: int

    class Config:
        from_attributes = True


# ─── UGEL endpoints ───────────────────────────────────────────────────────────

@router.get("/ugeles", response_model=List[UgelResponse])
async def listar_ugeles(
    search: Optional[str] = Query(None),
    solo_activas: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    q = select(Ugel)
    if solo_activas:
        q = q.where(Ugel.is_active == True)
    if search:
        q = q.where(Ugel.nombre.ilike(f"%{search}%"))
    result = await db.execute(q.order_by(Ugel.nombre))
    ugeles = result.scalars().all()
    return [
        UgelResponse(
            id=u.id, codigo=u.codigo, nombre=u.nombre,
            provincia_id=u.provincia_id,
            provincia_nombre=u.provincia.nombre if u.provincia else None,
            is_active=u.is_active, fecha_creacion=u.fecha_creacion,
        )
        for u in ugeles
    ]


@router.post("/ugeles", response_model=UgelResponse)
async def crear_ugel(
    data: UgelCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_role(*DRE_ROLES)),
):
    existing = await db.execute(select(Ugel).where(Ugel.codigo == data.codigo))
    if existing.scalars().first():
        raise HTTPException(400, "Ya existe una UGEL con ese código")
    ugel = Ugel(**data.model_dump())
    db.add(ugel)
    await db.flush()
    await db.refresh(ugel)
    return UgelResponse(
        id=ugel.id, codigo=ugel.codigo, nombre=ugel.nombre,
        provincia_id=ugel.provincia_id, provincia_nombre=None,
        is_active=ugel.is_active, fecha_creacion=ugel.fecha_creacion,
    )


@router.put("/ugeles/{ugel_id}", response_model=UgelResponse)
async def actualizar_ugel(
    ugel_id: int,
    data: UgelUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_role(*DRE_ROLES)),
):
    result = await db.execute(select(Ugel).where(Ugel.id == ugel_id))
    ugel = result.scalars().first()
    if not ugel:
        raise HTTPException(404, "UGEL no encontrada")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(ugel, field, value)
    await db.flush()
    await db.refresh(ugel)
    return UgelResponse(
        id=ugel.id, codigo=ugel.codigo, nombre=ugel.nombre,
        provincia_id=ugel.provincia_id,
        provincia_nombre=ugel.provincia.nombre if ugel.provincia else None,
        is_active=ugel.is_active, fecha_creacion=ugel.fecha_creacion,
    )


@router.delete("/ugeles/{ugel_id}")
async def eliminar_ugel(
    ugel_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_role(*DRE_ROLES)),
):
    result = await db.execute(select(Ugel).where(Ugel.id == ugel_id))
    ugel = result.scalars().first()
    if not ugel:
        raise HTTPException(404, "UGEL no encontrada")
    await db.delete(ugel)
    await db.flush()
    return {"ok": True}


# ─── Institución Educativa endpoints ─────────────────────────────────────────

@router.get("/instituciones", response_model=List[IEResponse])
async def listar_instituciones(
    ugel_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    solo_activas: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    q = select(InstitucionEducativa).options(selectinload(InstitucionEducativa.niveles))
    if solo_activas:
        q = q.where(InstitucionEducativa.is_active == True)
    if ugel_id:
        q = q.where(InstitucionEducativa.ugel_id == ugel_id)
    elif current_user.rol_codigo == RolCodigo.RESPONSABLE_UGEL and current_user.ugel_id:
        q = q.where(InstitucionEducativa.ugel_id == current_user.ugel_id)
    if search:
        q = q.where(
            or_(
                InstitucionEducativa.nombre.ilike(f"%{search}%"),
                InstitucionEducativa.codigo_modular.ilike(f"%{search}%"),
            )
        )
    result = await db.execute(q.order_by(InstitucionEducativa.nombre))
    ies = result.scalars().all()

    # Cargar ugeles para los nombres
    ugel_ids = list({ie.ugel_id for ie in ies})
    ugel_map: dict = {}
    if ugel_ids:
        ugel_result = await db.execute(select(Ugel).where(Ugel.id.in_(ugel_ids)))
        ugel_map = {u.id: u.nombre for u in ugel_result.scalars().all()}

    return [
        IEResponse(
            id=ie.id, codigo_modular=ie.codigo_modular, nombre=ie.nombre,
            nivel_educativo=ie.nivel_educativo, direccion=ie.direccion,
            ugel_id=ie.ugel_id, ugel_nombre=ugel_map.get(ie.ugel_id),
            distrito_id=ie.distrito_id,
            distrito_nombre=ie.distrito.nombre if ie.distrito else None,
            is_active=ie.is_active, fecha_creacion=ie.fecha_creacion,
        )
        for ie in ies
    ]


@router.get("/instituciones/{ie_id}", response_model=IEResponse)
async def obtener_institucion(
    ie_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    result = await db.execute(
        select(InstitucionEducativa)
        .options(selectinload(InstitucionEducativa.niveles))
        .where(InstitucionEducativa.id == ie_id)
    )
    ie = result.scalars().first()
    if not ie:
        raise HTTPException(404, "Institución no encontrada")
    return IEResponse(
        id=ie.id, codigo_modular=ie.codigo_modular, nombre=ie.nombre,
        nivel_educativo=ie.nivel_educativo, direccion=ie.direccion,
        ugel_id=ie.ugel_id,
        ugel_nombre=ie.ugel.nombre if ie.ugel else None,
        distrito_id=ie.distrito_id,
        distrito_nombre=ie.distrito.nombre if ie.distrito else None,
        is_active=ie.is_active, fecha_creacion=ie.fecha_creacion,
    )


@router.post("/instituciones", response_model=IEResponse)
async def crear_institucion(
    data: IECreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_role(*DRE_UGEL_ROLES)),
):
    existing = await db.execute(
        select(InstitucionEducativa).where(InstitucionEducativa.codigo_modular == data.codigo_modular)
    )
    if existing.scalars().first():
        raise HTTPException(400, "Ya existe una IE con ese código modular")

    # Responsable UGEL solo puede crear IEs en su UGEL
    if current_user.rol_codigo == RolCodigo.RESPONSABLE_UGEL:
        if data.ugel_id != current_user.ugel_id:
            raise HTTPException(403, "Solo puedes crear instituciones en tu UGEL")

    data_dict = data.model_dump()
    niveles_data: List[str] = data_dict.pop("nivel_educativo", [])
    ie = InstitucionEducativa(**data_dict)
    db.add(ie)
    await db.flush()
    for nivel in niveles_data:
        db.add(InstitucionNivel(institucion_id=ie.id, nivel=nivel))
    await db.flush()
    return IEResponse(
        id=ie.id, codigo_modular=ie.codigo_modular, nombre=ie.nombre,
        nivel_educativo=niveles_data, direccion=ie.direccion,
        ugel_id=ie.ugel_id, ugel_nombre=None,
        distrito_id=ie.distrito_id, distrito_nombre=None,
        is_active=ie.is_active, fecha_creacion=ie.fecha_creacion,
    )


@router.put("/instituciones/{ie_id}", response_model=IEResponse)
async def actualizar_institucion(
    ie_id: int,
    data: IEUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_role(*DRE_UGEL_ROLES)),
):
    result = await db.execute(select(InstitucionEducativa).where(InstitucionEducativa.id == ie_id))
    ie = result.scalars().first()
    if not ie:
        raise HTTPException(404, "Institución no encontrada")

    if current_user.rol_codigo == RolCodigo.RESPONSABLE_UGEL:
        if ie.ugel_id != current_user.ugel_id:
            raise HTTPException(403, "No tienes acceso a esta institución")

    data_dict = data.model_dump(exclude_unset=True)
    niveles_data: List[str] | None = data_dict.pop("nivel_educativo", None)
    for field, value in data_dict.items():
        setattr(ie, field, value)
    if niveles_data is not None:
        await db.execute(delete(InstitucionNivel).where(InstitucionNivel.institucion_id == ie.id))
        for nivel in niveles_data:
            db.add(InstitucionNivel(institucion_id=ie.id, nivel=nivel))
    await db.flush()
    result2 = await db.execute(
        select(InstitucionEducativa)
        .options(selectinload(InstitucionEducativa.niveles))
        .where(InstitucionEducativa.id == ie.id)
    )
    ie = result2.scalars().first()
    return IEResponse(
        id=ie.id, codigo_modular=ie.codigo_modular, nombre=ie.nombre,
        nivel_educativo=ie.nivel_educativo, direccion=ie.direccion,
        ugel_id=ie.ugel_id,
        ugel_nombre=ie.ugel.nombre if ie.ugel else None,
        distrito_id=ie.distrito_id,
        distrito_nombre=ie.distrito.nombre if ie.distrito else None,
        is_active=ie.is_active, fecha_creacion=ie.fecha_creacion,
    )


@router.delete("/instituciones/{ie_id}")
async def eliminar_institucion(
    ie_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_role(*DRE_UGEL_ROLES)),
):
    result = await db.execute(select(InstitucionEducativa).where(InstitucionEducativa.id == ie_id))
    ie = result.scalars().first()
    if not ie:
        raise HTTPException(404, "Institución no encontrada")
    if current_user.rol_codigo == RolCodigo.RESPONSABLE_UGEL and ie.ugel_id != current_user.ugel_id:
        raise HTTPException(403, "No tienes acceso a esta institución")
    await db.delete(ie)
    await db.flush()
    return {"ok": True}


# ─── Mi UGEL / Mi Institución ────────────────────────────────────────────────

@router.get("/mi-ugel", response_model=UgelResponse)
async def mi_ugel(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_role(RolCodigo.RESPONSABLE_UGEL)),
):
    if not current_user.ugel_id:
        raise HTTPException(400, "No tienes una UGEL asignada")
    result = await db.execute(select(Ugel).where(Ugel.id == current_user.ugel_id))
    ugel = result.scalars().first()
    if not ugel:
        raise HTTPException(404, "UGEL no encontrada")
    return UgelResponse(
        id=ugel.id, codigo=ugel.codigo, nombre=ugel.nombre,
        provincia_id=ugel.provincia_id,
        provincia_nombre=ugel.provincia.nombre if ugel.provincia else None,
        is_active=ugel.is_active, fecha_creacion=ugel.fecha_creacion,
    )


@router.get("/mi-institucion", response_model=IEResponse)
async def mi_institucion(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    allowed = {
        RolCodigo.DIRECTOR, RolCodigo.AUXILIAR,
        RolCodigo.ESPECIALISTA_DRE_COMUNICACION, RolCodigo.ESPECIALISTA_DRE_MATEMATICA,
        RolCodigo.RESPONSABLE_UGEL,
    }
    if RolCodigo(current_user.rol_codigo) not in allowed:
        raise HTTPException(403, "No tienes acceso")
    if not current_user.institucion_educativa_id:
        raise HTTPException(400, "No tienes una institución asignada")
    result = await db.execute(
        select(InstitucionEducativa)
        .options(selectinload(InstitucionEducativa.niveles))
        .where(InstitucionEducativa.id == current_user.institucion_educativa_id)
    )
    ie = result.scalars().first()
    if not ie:
        raise HTTPException(404, "Institución no encontrada")
    return IEResponse(
        id=ie.id, codigo_modular=ie.codigo_modular, nombre=ie.nombre,
        nivel_educativo=ie.nivel_educativo, direccion=ie.direccion,
        ugel_id=ie.ugel_id,
        ugel_nombre=ie.ugel.nombre if ie.ugel else None,
        distrito_id=ie.distrito_id,
        distrito_nombre=ie.distrito.nombre if ie.distrito else None,
        is_active=ie.is_active, fecha_creacion=ie.fecha_creacion,
    )


# ─── Analytics de IE ─────────────────────────────────────────────────────────

@router.get("/instituciones/{ie_id}/analytics")
async def ie_analytics(
    ie_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    """Estadísticas operacionales de una IE: exámenes, asignaciones, completados."""
    rol = RolCodigo(current_user.rol_codigo)
    GESTORES_IE = {RolCodigo.DIRECTOR, RolCodigo.AUXILIAR}

    # Verificar acceso según rol
    if rol in GESTORES_IE:
        if current_user.institucion_educativa_id != ie_id:
            raise HTTPException(403, "Solo puedes consultar tu propia institución")
    elif rol == RolCodigo.RESPONSABLE_UGEL:
        ie_r = await db.execute(
            select(InstitucionEducativa.ugel_id).where(InstitucionEducativa.id == ie_id)
        )
        ugel_id_ie = ie_r.scalar()
        if ugel_id_ie != current_user.ugel_id:
            raise HTTPException(403, "Esta IE no pertenece a tu UGEL")
    elif rol not in {RolCodigo.ESPECIALISTA_DRE_COMUNICACION, RolCodigo.ESPECIALISTA_DRE_MATEMATICA}:
        raise HTTPException(403, "No tienes acceso")

    # IDs de usuarios de esta IE
    user_ids_r = await db.execute(
        select(Usuario.id).where(Usuario.institucion_educativa_id == ie_id)
    )
    user_ids = [r[0] for r in user_ids_r.all()]

    # Conteo de usuarios por tipo
    from app.models.db_models import Rol as RolModel
    est_r = await db.execute(
        select(func.count()).select_from(Usuario)
        .join(RolModel, RolModel.id == Usuario.rol_id)
        .where(Usuario.institucion_educativa_id == ie_id, RolModel.codigo == "estudiante")
    )
    total_estudiantes = est_r.scalar() or 0

    doc_r = await db.execute(
        select(func.count()).select_from(Usuario)
        .join(RolModel, RolModel.id == Usuario.rol_id)
        .where(
            Usuario.institucion_educativa_id == ie_id,
            RolModel.codigo.in_(["docente", "auxiliar", "director"]),
        )
    )
    total_docentes = doc_r.scalar() or 0

    # Exámenes generados por usuarios de esta IE
    lec_r = await db.execute(
        select(func.count()).select_from(ExamenLectura)
        .where(ExamenLectura.docente_id.in_(user_ids))
    )
    total_lectura = lec_r.scalar() or 0

    mat_r = await db.execute(
        select(func.count()).select_from(ExamenMatematica)
        .where(ExamenMatematica.docente_id.in_(user_ids))
    )
    total_matematica = mat_r.scalar() or 0

    # Asignaciones y completados en esta IE
    asig_r = await db.execute(
        select(func.count()).select_from(AsignacionExamen)
        .where(AsignacionExamen.institucion_educativa_id == ie_id)
    )
    total_asignaciones = asig_r.scalar() or 0

    comp_r = await db.execute(
        select(func.count()).select_from(IntentoExamen)
        .where(
            IntentoExamen.estado == "completado",
            IntentoExamen.asignacion_id.in_(
                select(AsignacionExamen.id).where(AsignacionExamen.institucion_educativa_id == ie_id)
            ),
        )
    )
    total_completados = comp_r.scalar() or 0

    # Exámenes recientes de esta IE (últimos 6, lectura + matemática)
    rec_lec_r = await db.execute(
        select(ExamenLectura, Usuario)
        .join(Usuario, Usuario.id == ExamenLectura.docente_id)
        .where(ExamenLectura.docente_id.in_(user_ids))
        .order_by(ExamenLectura.fecha_creacion.desc())
        .limit(6)
    )
    recientes = []
    for ex, doc in rec_lec_r:
        recientes.append({
            "id": ex.id,
            "titulo": ex.titulo or f"Examen {ex.grado_nombre}",
            "grado": ex.grado_nombre or "—",
            "area": "lectura",
            "fecha": ex.fecha_creacion.isoformat() if ex.fecha_creacion else None,
            "docente": f"{doc.nombres or ''} {doc.apellidos or ''}".strip() or doc.dni,
        })

    rec_mat_r = await db.execute(
        select(ExamenMatematica, Usuario)
        .join(Usuario, Usuario.id == ExamenMatematica.docente_id)
        .where(ExamenMatematica.docente_id.in_(user_ids))
        .order_by(ExamenMatematica.fecha_creacion.desc())
        .limit(6)
    )
    for ex, doc in rec_mat_r:
        recientes.append({
            "id": ex.id,
            "titulo": ex.titulo or f"Examen {ex.grado_nombre}",
            "grado": ex.grado_nombre or "—",
            "area": "matematica",
            "fecha": ex.fecha_creacion.isoformat() if ex.fecha_creacion else None,
            "docente": f"{doc.nombres or ''} {doc.apellidos or ''}".strip() or doc.dni,
        })

    recientes.sort(key=lambda x: x["fecha"] or "", reverse=True)
    recientes = recientes[:6]

    return {
        "total_estudiantes": total_estudiantes,
        "total_docentes": total_docentes,
        "total_examenes_lectura": total_lectura,
        "total_examenes_matematica": total_matematica,
        "total_examenes": total_lectura + total_matematica,
        "total_asignaciones": total_asignaciones,
        "total_completados": total_completados,
        "recientes": recientes,
    }


# ─── Grados ──────────────────────────────────────────────────────────────────

@router.get("/grados", response_model=List[GradoResponse])
async def listar_grados(
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_active_user),
):
    result = await db.execute(select(Grado).order_by(Grado.orden))
    return result.scalars().all()
