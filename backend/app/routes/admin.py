from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional

from app.core.database import get_db
from app.core.db_utils import get_or_404
from app.models.db_models import Grado, Capacidad, Desempeno, Rol
from app.models.usuario import Usuario as DocenteModel
from app.schemas.usuario import Usuario as Docente, UsuarioAdminCreate as DocenteAdminCreate, UsuarioUpdate as DocenteUpdate
from app.services.usuario_service import usuario_service as docente_service
from app.api.dependencies import get_current_superuser, get_current_active_user, require_role
from app.models.enums import RolCodigo

# Dependencia para gestión de usuarios: DRE + UGEL + Director
_GESTORES_ROLES = (
    RolCodigo.ESPECIALISTA_DRE_COMUNICACION,
    RolCodigo.ESPECIALISTA_DRE_MATEMATICA,
    RolCodigo.RESPONSABLE_UGEL,
    RolCodigo.DIRECTOR,
)
get_gestor = require_role(*_GESTORES_ROLES)


def _scope(current_user: DocenteModel) -> dict:
    """Retorna filtros de scope según el rol del usuario."""
    rol = RolCodigo(current_user.rol_codigo)
    if rol in {RolCodigo.ESPECIALISTA_DRE_COMUNICACION, RolCodigo.ESPECIALISTA_DRE_MATEMATICA}:
        return {}
    if rol == RolCodigo.RESPONSABLE_UGEL:
        return {"ugel_id": current_user.ugel_id}
    # Director
    return {"institucion_educativa_id": current_user.institucion_educativa_id}

router = APIRouter()


# --- Schemas ---

class GradoSchema(BaseModel):
    nombre: str
    numero: int
    nivel: str
    orden: int

    class Config:
        from_attributes = True


class GradoCreate(GradoSchema):
    pass


class GradoUpdate(GradoSchema):
    pass


class GradoResponse(GradoSchema):
    id: int


class CapacidadSchema(BaseModel):
    nombre: str
    tipo: str
    descripcion: Optional[str] = None

    class Config:
        from_attributes = True


class CapacidadCreate(CapacidadSchema):
    pass


class CapacidadUpdate(CapacidadSchema):
    pass


class CapacidadResponse(CapacidadSchema):
    id: int


class DesempenoSchema(BaseModel):
    codigo: str
    descripcion: str
    grado_id: int
    capacidad_id: int

    class Config:
        from_attributes = True


class DesempenoCreate(DesempenoSchema):
    pass


class DesempenoUpdate(DesempenoSchema):
    pass


class DesempenoResponse(DesempenoSchema):
    id: int


# --- Grado Endpoints ---

@router.post("/grados", response_model=GradoResponse)
async def create_grado(
    grado: GradoCreate,
    db: AsyncSession = Depends(get_db),
    _: DocenteModel = Depends(get_current_superuser)
):
    db_grado = Grado(**grado.dict())
    db.add(db_grado)
    await db.commit()
    await db.refresh(db_grado)
    return db_grado


@router.get("/grados", response_model=List[GradoResponse])
async def get_grados(
    db: AsyncSession = Depends(get_db),
    _: DocenteModel = Depends(get_current_superuser)
):
    result = await db.execute(select(Grado).order_by(Grado.orden))
    return result.scalars().all()


@router.put("/grados/{grado_id}", response_model=GradoResponse)
async def update_grado(
    grado_id: int,
    grado: GradoUpdate,
    db: AsyncSession = Depends(get_db),
    _: DocenteModel = Depends(get_current_superuser)
):
    db_grado = await get_or_404(db, Grado, grado_id, "Grado not found")

    for key, value in grado.dict().items():
        setattr(db_grado, key, value)

    await db.commit()
    await db.refresh(db_grado)
    return db_grado


@router.delete("/grados/{grado_id}")
async def delete_grado(
    grado_id: int,
    db: AsyncSession = Depends(get_db),
    _: DocenteModel = Depends(get_current_superuser)
):
    db_grado = await get_or_404(db, Grado, grado_id, "Grado not found")

    await db.delete(db_grado)
    await db.commit()
    return {"message": "Grado deleted successfully"}


# --- Capacidad Endpoints ---

@router.post("/capacidades", response_model=CapacidadResponse)
async def create_capacidad(
    capacidad: CapacidadCreate,
    db: AsyncSession = Depends(get_db),
    _: DocenteModel = Depends(get_current_superuser)
):
    db_capacidad = Capacidad(**capacidad.dict())
    db.add(db_capacidad)
    await db.commit()
    await db.refresh(db_capacidad)
    return db_capacidad


@router.get("/capacidades", response_model=List[CapacidadResponse])
async def get_capacidades(
    db: AsyncSession = Depends(get_db),
    _: DocenteModel = Depends(get_current_superuser)
):
    result = await db.execute(select(Capacidad))
    return result.scalars().all()


@router.put("/capacidades/{capacidad_id}", response_model=CapacidadResponse)
async def update_capacidad(
    capacidad_id: int,
    capacidad: CapacidadUpdate,
    db: AsyncSession = Depends(get_db),
    _: DocenteModel = Depends(get_current_superuser)
):
    db_capacidad = await get_or_404(db, Capacidad, capacidad_id, "Capacidad not found")

    for key, value in capacidad.dict().items():
        setattr(db_capacidad, key, value)

    await db.commit()
    await db.refresh(db_capacidad)
    return db_capacidad


@router.delete("/capacidades/{capacidad_id}")
async def delete_capacidad(
    capacidad_id: int,
    db: AsyncSession = Depends(get_db),
    _: DocenteModel = Depends(get_current_superuser)
):
    db_capacidad = await get_or_404(db, Capacidad, capacidad_id, "Capacidad not found")

    await db.delete(db_capacidad)
    await db.commit()
    return {"message": "Capacidad deleted successfully"}


# --- Desempeno Endpoints ---

@router.post("/desempenos", response_model=DesempenoResponse)
async def create_desempeno(
    desempeno: DesempenoCreate,
    db: AsyncSession = Depends(get_db),
    _: DocenteModel = Depends(get_current_superuser)
):
    db_desempeno = Desempeno(**desempeno.dict())
    db.add(db_desempeno)
    await db.commit()
    await db.refresh(db_desempeno)
    return db_desempeno


@router.put("/desempenos/{desempeno_id}", response_model=DesempenoResponse)
async def update_desempeno(
    desempeno_id: int,
    desempeno: DesempenoUpdate,
    db: AsyncSession = Depends(get_db),
    _: DocenteModel = Depends(get_current_superuser)
):
    db_desempeno = await get_or_404(db, Desempeno, desempeno_id, "Desempeno not found")

    for key, value in desempeno.dict().items():
        setattr(db_desempeno, key, value)

    await db.commit()
    await db.refresh(db_desempeno)
    return db_desempeno


@router.delete("/desempenos/{desempeno_id}")
async def delete_desempeno(
    desempeno_id: int,
    db: AsyncSession = Depends(get_db),
    _: DocenteModel = Depends(get_current_superuser)
):
    db_desempeno = await get_or_404(db, Desempeno, desempeno_id, "Desempeno not found")

    await db.delete(db_desempeno)
    await db.commit()
    return {"message": "Desempeno deleted successfully"}


# --- Docentes (Usuarios) Endpoints ---

from app.schemas.pagination import PaginatedResponse
import math

@router.get("/docentes", response_model=PaginatedResponse[Docente])
async def list_docentes(
    page: int = 1,
    size: int = 10,
    q: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: DocenteModel = Depends(get_gestor)
):
    """Listar usuarios con paginación y búsqueda opcional. Scoped por rol."""
    skip = (page - 1) * size
    scope = _scope(current_user)
    items, total = await docente_service.get_paginated_usuarios(
        db, skip=skip, limit=size, search_query=q, **scope
    )
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size) if total > 0 else 0
    )


@router.post("/docentes", response_model=Docente, status_code=201)
async def create_docente(
    docente_in: DocenteAdminCreate,
    db: AsyncSession = Depends(get_db),
    current_user: DocenteModel = Depends(get_gestor)
):
    """Crear un nuevo usuario. Valida jerarquía de roles."""
    rol = RolCodigo(current_user.rol_codigo)
    if rol == RolCodigo.DIRECTOR:
        docente_in.institucion_educativa_id = current_user.institucion_educativa_id
        docente_in.ugel_id = current_user.ugel_id
    try:
        return await docente_service.create_usuario(
            db, docente_in,
            creado_por_id=current_user.id,
            creado_por_rol=current_user.rol_codigo,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/docentes/{docente_id}", response_model=Docente)
async def get_docente(
    docente_id: int,
    db: AsyncSession = Depends(get_db),
    _: DocenteModel = Depends(get_gestor)
):
    """Obtener un usuario por ID."""
    from app.repositories.docente_repository import docente_repository
    docente = await docente_repository.get(db, docente_id)
    if not docente:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return docente


@router.put("/docentes/{docente_id}", response_model=Docente)
async def update_docente(
    docente_id: int,
    docente_in: DocenteUpdate,
    db: AsyncSession = Depends(get_db),
    _: DocenteModel = Depends(get_gestor)
):
    """Actualizar un usuario."""
    docente = await docente_service.update_usuario(db, docente_id, docente_in)
    if not docente:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return docente


@router.delete("/docentes/{docente_id}")
async def delete_docente(
    docente_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: DocenteModel = Depends(get_gestor)
):
    """Eliminar un usuario. No se puede eliminar a sí mismo."""
    if current_user.id == docente_id:
        raise HTTPException(status_code=400, detail="No puedes eliminar tu propio usuario")
    deleted = await docente_service.delete_usuario(db, docente_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"message": "Usuario eliminado correctamente"}


# --- Métricas del Sistema ---

from app.models.db_models import ExamenLectura, ExamenMatematica
from sqlalchemy import func, case

@router.get("/metricas")
async def get_metricas(
    db: AsyncSession = Depends(get_db),
    _: DocenteModel = Depends(get_current_superuser)
):
    """Métricas de uso del sistema para el administrador."""
    from datetime import datetime, timedelta, timezone

    # ── Totales de docentes ──────────────────────────────────────────────
    r = await db.execute(select(func.count()).select_from(DocenteModel))
    total_docentes = r.scalar() or 0

    r = await db.execute(select(func.count()).select_from(DocenteModel).where(DocenteModel.is_active == True))
    docentes_activos = r.scalar() or 0

    # ── Totales de exámenes ──────────────────────────────────────────────
    r = await db.execute(select(func.count()).select_from(ExamenLectura))
    total_lectura = r.scalar() or 0

    r = await db.execute(select(func.count()).select_from(ExamenMatematica))
    total_matematica = r.scalar() or 0

    # ── Exámenes por mes (últimos 6 meses) ───────────────────────────────
    hace_6_meses = datetime.now(timezone.utc) - timedelta(days=180)

    r_lec = await db.execute(
        select(
            func.to_char(ExamenLectura.fecha_creacion, 'YYYY-MM').label('mes'),
            func.count().label('total')
        )
        .where(ExamenLectura.fecha_creacion >= hace_6_meses)
        .group_by('mes')
        .order_by('mes')
    )
    lec_por_mes = {row.mes: row.total for row in r_lec}

    r_mat = await db.execute(
        select(
            func.to_char(ExamenMatematica.fecha_creacion, 'YYYY-MM').label('mes'),
            func.count().label('total')
        )
        .where(ExamenMatematica.fecha_creacion >= hace_6_meses)
        .group_by('mes')
        .order_by('mes')
    )
    mat_por_mes = {row.mes: row.total for row in r_mat}

    # Construir los últimos 6 meses
    meses = []
    for i in range(5, -1, -1):
        d = datetime.now(timezone.utc).replace(day=1) - timedelta(days=i * 30)
        key = d.strftime('%Y-%m')
        meses.append({
            'mes': key,
            'label': d.strftime('%b %Y'),
            'lectura': lec_por_mes.get(key, 0),
            'matematica': mat_por_mes.get(key, 0),
        })

    # ── Top 10 docentes más activos ──────────────────────────────────────
    r = await db.execute(
        select(
            DocenteModel.id,
            DocenteModel.nombres,
            DocenteModel.apellidos,
            DocenteModel.dni,
            func.count(ExamenLectura.id).label('examenes_lectura')
        )
        .outerjoin(ExamenLectura, ExamenLectura.docente_id == DocenteModel.id)
        .group_by(DocenteModel.id)
        .order_by(func.count(ExamenLectura.id).desc())
        .limit(10)
    )
    top_lec = {row.id: row.examenes_lectura for row in r}

    r = await db.execute(
        select(
            DocenteModel.id,
            func.count(ExamenMatematica.id).label('examenes_mat')
        )
        .outerjoin(ExamenMatematica, ExamenMatematica.docente_id == DocenteModel.id)
        .group_by(DocenteModel.id)
    )
    top_mat = {row.id: row.examenes_mat for row in r}

    r = await db.execute(
        select(DocenteModel).options()
        .order_by(DocenteModel.id)
    )
    docentes_list = r.scalars().all()

    top_docentes = sorted([
        {
            'id': d.id,
            'nombre': f"{d.nombres or ''} {d.apellidos or ''}".strip() or d.dni,
            'dni': d.dni,
            'institucion': d.institucion_nombre or '—',
            'lectura': top_lec.get(d.id, 0),
            'matematica': top_mat.get(d.id, 0),
            'total': top_lec.get(d.id, 0) + top_mat.get(d.id, 0),
        }
        for d in docentes_list
    ], key=lambda x: x['total'], reverse=True)[:10]

    # ── Distribución por grado ───────────────────────────────────────────
    r = await db.execute(
        select(ExamenLectura.grado_nombre, func.count().label('total'))
        .where(ExamenLectura.grado_nombre != None)
        .group_by(ExamenLectura.grado_nombre)
        .order_by(func.count().desc())
        .limit(8)
    )
    por_grado_lec = [{'grado': row.grado_nombre, 'total': row.total, 'area': 'lectura'} for row in r]

    r = await db.execute(
        select(ExamenMatematica.grado_nombre, func.count().label('total'))
        .where(ExamenMatematica.grado_nombre != None)
        .group_by(ExamenMatematica.grado_nombre)
        .order_by(func.count().desc())
        .limit(8)
    )
    por_grado_mat = [{'grado': row.grado_nombre, 'total': row.total, 'area': 'matematica'} for row in r]

    # ── Exámenes recientes ────────────────────────────────────────────────
    r = await db.execute(
        select(ExamenLectura, DocenteModel)
        .join(DocenteModel, DocenteModel.id == ExamenLectura.docente_id)
        .order_by(ExamenLectura.fecha_creacion.desc())
        .limit(8)
    )
    recientes_lec = [
        {
            'id': ex.id,
            'titulo': ex.titulo or 'Sin título',
            'grado': ex.grado_nombre or '—',
            'docente': f"{doc.nombres or ''} {doc.apellidos or ''}".strip() or doc.dni,
            'fecha': ex.fecha_creacion.isoformat() if ex.fecha_creacion else None,
            'area': 'lectura',
        }
        for ex, doc in r
    ]

    r = await db.execute(
        select(ExamenMatematica, DocenteModel)
        .join(DocenteModel, DocenteModel.id == ExamenMatematica.docente_id)
        .order_by(ExamenMatematica.fecha_creacion.desc())
        .limit(8)
    )
    recientes_mat = [
        {
            'id': ex.id,
            'titulo': ex.titulo or 'Sin título',
            'grado': ex.grado_nombre or '—',
            'docente': f"{doc.nombres or ''} {doc.apellidos or ''}".strip() or doc.dni,
            'fecha': ex.fecha_creacion.isoformat() if ex.fecha_creacion else None,
            'area': 'matematica',
        }
        for ex, doc in r
    ]

    recientes = sorted(recientes_lec + recientes_mat, key=lambda x: x['fecha'] or '', reverse=True)[:10]

    return {
        'resumen': {
            'total_docentes': total_docentes,
            'docentes_activos': docentes_activos,
            'docentes_inactivos': total_docentes - docentes_activos,
            'total_examenes': total_lectura + total_matematica,
            'examenes_lectura': total_lectura,
            'examenes_matematica': total_matematica,
        },
        'por_mes': meses,
        'top_docentes': top_docentes,
        'por_grado_lectura': por_grado_lec,
        'por_grado_matematica': por_grado_mat,
        'recientes': recientes,
    }



# --- Roles Config Endpoints ---

class RolConfigResponse(BaseModel):
    id: int
    codigo: str
    nombre: str
    descripcion: Optional[str] = None
    nivel: int
    orden: int
    modulos_default: Optional[List[str]] = None
    modulos_efectivos: List[str]

    class Config:
        from_attributes = True


class RolConfigUpdate(BaseModel):
    modulos_default: Optional[List[str]] = None


@router.get("/roles-config", response_model=List[RolConfigResponse])
async def get_roles_config(
    db: AsyncSession = Depends(get_db),
    _: DocenteModel = Depends(get_current_superuser),
):
    """Obtener configuración de módulos de todos los roles."""
    from app.models.enums import ROLE_MODULOS_DEFAULT
    result = await db.execute(select(Rol).order_by(Rol.orden))
    roles = result.scalars().all()
    out = []
    for rol in roles:
        efectivos = rol.modulos_default if rol.modulos_default else ROLE_MODULOS_DEFAULT.get(rol.codigo, [])
        out.append(RolConfigResponse(
            id=rol.id,
            codigo=rol.codigo,
            nombre=rol.nombre,
            descripcion=rol.descripcion,
            nivel=rol.nivel,
            orden=rol.orden,
            modulos_default=rol.modulos_default,
            modulos_efectivos=efectivos,
        ))
    return out


@router.put("/roles-config/{rol_codigo}", response_model=RolConfigResponse)
async def update_rol_config(
    rol_codigo: str,
    data: RolConfigUpdate,
    db: AsyncSession = Depends(get_db),
    _: DocenteModel = Depends(get_current_superuser),
):
    """Actualizar los módulos por defecto de un rol."""
    from app.models.enums import ROLE_MODULOS_DEFAULT, MODULOS_DISPONIBLES
    result = await db.execute(select(Rol).where(Rol.codigo == rol_codigo))
    rol = result.scalars().first()
    if not rol:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    if data.modulos_default is not None:
        invalidos = [m for m in data.modulos_default if m not in MODULOS_DISPONIBLES]
        if invalidos:
            raise HTTPException(status_code=400, detail=f"Módulos inválidos: {invalidos}")
    rol.modulos_default = data.modulos_default
    await db.commit()
    await db.refresh(rol)
    efectivos = rol.modulos_default if rol.modulos_default else ROLE_MODULOS_DEFAULT.get(rol.codigo, [])
    return RolConfigResponse(
        id=rol.id,
        codigo=rol.codigo,
        nombre=rol.nombre,
        descripcion=rol.descripcion,
        nivel=rol.nivel,
        orden=rol.orden,
        modulos_default=rol.modulos_default,
        modulos_efectivos=efectivos,
    )


@router.patch("/docentes/{docente_id}/toggle-active", response_model=Docente)
async def toggle_active(
    docente_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: DocenteModel = Depends(get_gestor)
):
    """Activar o desactivar un usuario."""
    if current_user.id == docente_id:
        raise HTTPException(status_code=400, detail="No puedes desactivar tu propio usuario")
    from app.repositories.docente_repository import docente_repository
    docente = await docente_repository.get(db, docente_id)
    if not docente:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    update_data = {"is_active": not docente.is_active}
    return await docente_repository.update(db, docente, update_data)
