"""
Rutas para auto-registro de estudiantes y gestión de códigos de clase.
"""
import random
import string
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.db_models import CodigoClase, Grado, InstitucionEducativa
from app.models.usuario import Usuario
from app.models.db_models import Rol
from app.models.enums import RolCodigo
from app.api.dependencies import get_current_active_user, require_role, require_modulo
from app.core.security import get_password_hash

router = APIRouter()

CREADORES_ROLES = (
    RolCodigo.DOCENTE, RolCodigo.AUXILIAR, RolCodigo.DIRECTOR,
    RolCodigo.ESPECIALISTA_DRE_COMUNICACION, RolCodigo.ESPECIALISTA_DRE_MATEMATICA,
)


# ─── Schemas ─────────────────────────────────────────────────────────────────

class CodigoClaseCreate(BaseModel):
    grado_id: int
    seccion: str = Field(..., min_length=1, max_length=10)
    max_estudiantes: int = Field(40, ge=1, le=200)
    fecha_expiracion: Optional[datetime] = None


class CodigoClaseResponse(BaseModel):
    id: int
    codigo: str
    grado_id: int
    grado_nombre: Optional[str] = None
    seccion: str
    max_estudiantes: int
    is_active: bool
    fecha_creacion: Optional[datetime] = None
    fecha_expiracion: Optional[datetime] = None
    institucion_nombre: Optional[str] = None
    total_estudiantes: int = 0

    class Config:
        from_attributes = True


class RegistroEstudianteRequest(BaseModel):
    codigo_clase: str = Field(..., min_length=4, max_length=20)
    nombres: str = Field(..., min_length=2, max_length=100)
    apellidos: str = Field(..., min_length=2, max_length=100)
    dni: Optional[str] = Field(None, min_length=8, max_length=8, pattern=r"^\d{8}$")
    password: str = Field(..., min_length=4, max_length=72)


class RegistroEstudianteResponse(BaseModel):
    id: int
    codigo_estudiante: str
    nombres: Optional[str] = None
    apellidos: Optional[str] = None
    grado: Optional[str] = None
    seccion: Optional[str] = None
    institucion: Optional[str] = None


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _generar_codigo_clase() -> str:
    """Genera un código de clase alfanumérico de 8 caracteres."""
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choices(chars, k=8))


async def _siguiente_codigo_estudiante(db: AsyncSession) -> str:
    result = await db.execute(
        select(func.max(Usuario.codigo_estudiante)).where(
            Usuario.codigo_estudiante.isnot(None)
        )
    )
    ultimo = result.scalar()
    if ultimo:
        try:
            numero = int(ultimo[3:]) + 1
        except ValueError:
            numero = 1
    else:
        numero = 1
    return f"EST{numero:04d}"


# ─── Endpoints de Códigos de Clase ───────────────────────────────────────────

@router.get("/codigos-clase", response_model=List[CodigoClaseResponse])
async def listar_codigos_clase(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_modulo("codigos_clase")),
):
    q = select(CodigoClase).where(CodigoClase.creado_por_id == current_user.id)
    # Director ve todos los de su institución
    if current_user.rol_codigo == RolCodigo.DIRECTOR and current_user.institucion_educativa_id:
        q = select(CodigoClase).where(
            CodigoClase.institucion_educativa_id == current_user.institucion_educativa_id
        )
    result = await db.execute(q.order_by(CodigoClase.fecha_creacion.desc()))
    codigos = result.scalars().all()

    grado_ids = list({c.grado_id for c in codigos})
    grado_map: dict = {}
    if grado_ids:
        gr = await db.execute(select(Grado).where(Grado.id.in_(grado_ids)))
        grado_map = {g.id: g.nombre for g in gr.scalars().all()}

    ie_ids = list({c.institucion_educativa_id for c in codigos})
    ie_map: dict = {}
    if ie_ids:
        ie = await db.execute(select(InstitucionEducativa).where(InstitucionEducativa.id.in_(ie_ids)))
        ie_map = {i.id: i.nombre for i in ie.scalars().all()}

    return [
        CodigoClaseResponse(
            id=c.id, codigo=c.codigo,
            grado_id=c.grado_id, grado_nombre=grado_map.get(c.grado_id),
            seccion=c.seccion, max_estudiantes=c.max_estudiantes,
            is_active=c.is_active, fecha_creacion=c.fecha_creacion,
            fecha_expiracion=c.fecha_expiracion,
            institucion_nombre=ie_map.get(c.institucion_educativa_id),
            total_estudiantes=0,
        )
        for c in codigos
    ]


@router.post("/codigos-clase", response_model=CodigoClaseResponse)
async def crear_codigo_clase(
    data: CodigoClaseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_modulo("codigos_clase")),
):
    if not current_user.institucion_educativa_id:
        raise HTTPException(400, "No tienes una institución educativa asignada")

    # Generar código único
    for _ in range(10):
        codigo = _generar_codigo_clase()
        existing = await db.execute(select(CodigoClase).where(CodigoClase.codigo == codigo))
        if not existing.scalars().first():
            break

    cc = CodigoClase(
        codigo=codigo,
        creado_por_id=current_user.id,
        institucion_educativa_id=current_user.institucion_educativa_id,
        grado_id=data.grado_id,
        seccion=data.seccion,
        max_estudiantes=data.max_estudiantes,
        fecha_expiracion=data.fecha_expiracion,
    )
    db.add(cc)
    await db.flush()
    await db.refresh(cc)

    grado_result = await db.execute(select(Grado).where(Grado.id == data.grado_id))
    grado = grado_result.scalars().first()

    return CodigoClaseResponse(
        id=cc.id, codigo=cc.codigo,
        grado_id=cc.grado_id, grado_nombre=grado.nombre if grado else None,
        seccion=cc.seccion, max_estudiantes=cc.max_estudiantes,
        is_active=cc.is_active, fecha_creacion=cc.fecha_creacion,
        fecha_expiracion=cc.fecha_expiracion,
        institucion_nombre=None, total_estudiantes=0,
    )


@router.put("/codigos-clase/{codigo_id}/toggle")
async def toggle_codigo_clase(
    codigo_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_modulo("codigos_clase")),
):
    result = await db.execute(select(CodigoClase).where(CodigoClase.id == codigo_id))
    cc = result.scalars().first()
    if not cc:
        raise HTTPException(404, "Código no encontrado")
    if cc.creado_por_id != current_user.id and current_user.rol_codigo != RolCodigo.DIRECTOR:
        raise HTTPException(403, "No tienes permiso para modificar este código")
    cc.is_active = not cc.is_active
    await db.flush()
    return {"id": cc.id, "is_active": cc.is_active}


@router.delete("/codigos-clase/{codigo_id}")
async def eliminar_codigo_clase(
    codigo_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_modulo("codigos_clase")),
):
    result = await db.execute(select(CodigoClase).where(CodigoClase.id == codigo_id))
    cc = result.scalars().first()
    if not cc:
        raise HTTPException(404, "Código no encontrado")
    if cc.creado_por_id != current_user.id and current_user.rol_codigo != RolCodigo.DIRECTOR:
        raise HTTPException(403, "No tienes permiso")
    await db.delete(cc)
    await db.flush()
    return {"ok": True}


# ─── Auto-registro de estudiantes (público) ───────────────────────────────────

@router.post("/registro/estudiante", response_model=RegistroEstudianteResponse)
async def registrar_estudiante(
    data: RegistroEstudianteRequest,
    db: AsyncSession = Depends(get_db),
):
    # Buscar y validar código de clase
    result = await db.execute(
        select(CodigoClase).where(CodigoClase.codigo == data.codigo_clase.upper())
    )
    cc = result.scalars().first()
    if not cc or not cc.is_active:
        raise HTTPException(400, "Código de clase inválido o inactivo")

    if cc.fecha_expiracion and cc.fecha_expiracion < datetime.utcnow():
        raise HTTPException(400, "El código de clase ha expirado")

    # Verificar DNI duplicado si se proveyó
    if data.dni:
        existing = await db.execute(select(Usuario).where(Usuario.dni == data.dni))
        if existing.scalars().first():
            raise HTTPException(400, "DNI ya registrado")

    # Obtener rol de estudiante
    rol_result = await db.execute(select(Rol).where(Rol.codigo == RolCodigo.ESTUDIANTE.value))
    rol = rol_result.scalars().first()
    if not rol:
        raise HTTPException(500, "Rol estudiante no configurado")

    # Contar estudiantes ya registrados con este código
    count_result = await db.execute(
        select(func.count(Usuario.id)).where(
            Usuario.rol_id == rol.id,
            Usuario.institucion_educativa_id == cc.institucion_educativa_id,
            Usuario.grado_id == cc.grado_id,
            Usuario.seccion == cc.seccion,
        )
    )
    count = count_result.scalar() or 0
    if count >= cc.max_estudiantes:
        raise HTTPException(400, "El código de clase ha alcanzado el máximo de estudiantes")

    codigo_estudiante = await _siguiente_codigo_estudiante(db)

    estudiante = Usuario(
        dni=data.dni,
        codigo_estudiante=codigo_estudiante,
        nombres=data.nombres,
        apellidos=data.apellidos,
        password_hash=get_password_hash(data.password),
        rol_id=rol.id,
        ugel_id=None,
        institucion_educativa_id=cc.institucion_educativa_id,
        grado_id=cc.grado_id,
        seccion=cc.seccion,
        creado_por_id=cc.creado_por_id,
    )
    db.add(estudiante)
    await db.flush()
    await db.refresh(estudiante)

    # Cargar nombres para la respuesta
    grado_result = await db.execute(select(Grado).where(Grado.id == cc.grado_id))
    grado = grado_result.scalars().first()
    ie_result = await db.execute(
        select(InstitucionEducativa).where(InstitucionEducativa.id == cc.institucion_educativa_id)
    )
    ie = ie_result.scalars().first()

    return RegistroEstudianteResponse(
        id=estudiante.id,
        codigo_estudiante=codigo_estudiante,
        nombres=estudiante.nombres,
        apellidos=estudiante.apellidos,
        grado=grado.nombre if grado else None,
        seccion=cc.seccion,
        institucion=ie.nombre if ie else None,
    )


@router.get("/registro/validar-codigo/{codigo}")
async def validar_codigo_clase(
    codigo: str,
    db: AsyncSession = Depends(get_db),
):
    """Valida un código de clase y retorna info básica (público)."""
    result = await db.execute(
        select(CodigoClase).where(CodigoClase.codigo == codigo.upper())
    )
    cc = result.scalars().first()
    if not cc or not cc.is_active:
        raise HTTPException(400, "Código inválido o inactivo")
    if cc.fecha_expiracion and cc.fecha_expiracion < datetime.utcnow():
        raise HTTPException(400, "Código expirado")

    grado_result = await db.execute(select(Grado).where(Grado.id == cc.grado_id))
    grado = grado_result.scalars().first()
    ie_result = await db.execute(
        select(InstitucionEducativa).where(InstitucionEducativa.id == cc.institucion_educativa_id)
    )
    ie = ie_result.scalars().first()

    return {
        "valid": True,
        "grado": grado.nombre if grado else None,
        "seccion": cc.seccion,
        "institucion": ie.nombre if ie else None,
    }


# ─── Registro directo por Docente (autenticado) ────────────────────────────────

class RegistroDirectoRequest(BaseModel):
    nombres: str = Field(..., min_length=2, max_length=100)
    apellidos: str = Field(..., min_length=2, max_length=100)
    dni: Optional[str] = Field(None, min_length=8, max_length=8, pattern=r"^\d{8}$")
    password: str = Field(..., min_length=4, max_length=72)
    grado_id: int
    seccion: str = Field(..., min_length=1, max_length=10)


class EstudianteListItem(BaseModel):
    id: int
    codigo_estudiante: Optional[str] = None
    nombres: Optional[str] = None
    apellidos: Optional[str] = None
    dni: Optional[str] = None
    grado_id: Optional[int] = None
    grado_nombre: Optional[str] = None
    seccion: Optional[str] = None
    is_active: bool
    fecha_creacion: Optional[datetime] = None

    class Config:
        from_attributes = True


@router.post("/docente/registrar-estudiante", response_model=RegistroEstudianteResponse, status_code=201)
async def registrar_estudiante_directo(
    data: RegistroDirectoRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    """Permite a un docente (o director/auxiliar/DRE) registrar un estudiante directamente
    en su institución sin necesidad de un código de clase."""
    if current_user.rol_codigo not in [r.value for r in CREADORES_ROLES]:
        raise HTTPException(403, "Solo docentes, auxiliares, directores o especialistas DRE pueden usar este endpoint")

    if not current_user.institucion_educativa_id:
        raise HTTPException(400, "No tienes una institución educativa asignada")

    # Verificar DNI duplicado si se proveyó
    if data.dni:
        existing = await db.execute(select(Usuario).where(Usuario.dni == data.dni))
        if existing.scalars().first():
            raise HTTPException(400, "DNI ya registrado en el sistema")

    # Obtener rol de estudiante
    rol_result = await db.execute(select(Rol).where(Rol.codigo == RolCodigo.ESTUDIANTE.value))
    rol = rol_result.scalars().first()
    if not rol:
        raise HTTPException(500, "Rol estudiante no configurado")

    codigo_estudiante = await _siguiente_codigo_estudiante(db)

    estudiante = Usuario(
        dni=data.dni,
        codigo_estudiante=codigo_estudiante,
        nombres=data.nombres,
        apellidos=data.apellidos,
        password_hash=get_password_hash(data.password),
        rol_id=rol.id,
        ugel_id=current_user.ugel_id,
        institucion_educativa_id=current_user.institucion_educativa_id,
        grado_id=data.grado_id,
        seccion=data.seccion,
        creado_por_id=current_user.id,
    )
    db.add(estudiante)
    await db.flush()
    await db.refresh(estudiante)

    grado_result = await db.execute(select(Grado).where(Grado.id == data.grado_id))
    grado = grado_result.scalars().first()
    ie_result = await db.execute(
        select(InstitucionEducativa).where(
            InstitucionEducativa.id == current_user.institucion_educativa_id
        )
    )
    ie = ie_result.scalars().first()

    return RegistroEstudianteResponse(
        id=estudiante.id,
        codigo_estudiante=codigo_estudiante,
        nombres=estudiante.nombres,
        apellidos=estudiante.apellidos,
        grado=grado.nombre if grado else None,
        seccion=data.seccion,
        institucion=ie.nombre if ie else None,
    )


@router.get("/docente/mis-estudiantes", response_model=List[EstudianteListItem])
async def listar_mis_estudiantes(
    grado_id: Optional[int] = Query(None),
    seccion: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    """Lista los estudiantes registrados por el docente autenticado.
    Filtra opcionalmente por grado_id, seccion y búsqueda de texto."""
    if current_user.rol_codigo not in [r.value for r in CREADORES_ROLES]:
        raise HTTPException(403, "Permisos insuficientes")

    # Rol estudiante
    rol_result = await db.execute(select(Rol).where(Rol.codigo == RolCodigo.ESTUDIANTE.value))
    rol = rol_result.scalars().first()
    if not rol:
        return []

    stmt = select(Usuario).where(
        Usuario.rol_id == rol.id,
        Usuario.creado_por_id == current_user.id,
    )

    if grado_id:
        stmt = stmt.where(Usuario.grado_id == grado_id)
    if seccion:
        stmt = stmt.where(Usuario.seccion == seccion)
    if q:
        like = f"%{q}%"
        from sqlalchemy import or_
        stmt = stmt.where(
            or_(
                Usuario.nombres.ilike(like),
                Usuario.apellidos.ilike(like),
                Usuario.dni.ilike(like),
                Usuario.codigo_estudiante.ilike(like),
            )
        )

    stmt = stmt.order_by(Usuario.apellidos, Usuario.nombres)
    result = await db.execute(stmt)
    estudiantes = result.scalars().all()

    # Cargar nombres de grados
    grado_ids = list({e.grado_id for e in estudiantes if e.grado_id})
    grado_map: dict = {}
    if grado_ids:
        gr = await db.execute(select(Grado).where(Grado.id.in_(grado_ids)))
        grado_map = {g.id: g.nombre for g in gr.scalars().all()}

    return [
        EstudianteListItem(
            id=e.id,
            codigo_estudiante=e.codigo_estudiante,
            nombres=e.nombres,
            apellidos=e.apellidos,
            dni=e.dni,
            grado_id=e.grado_id,
            grado_nombre=grado_map.get(e.grado_id) if e.grado_id else None,
            seccion=e.seccion,
            is_active=e.is_active,
            fecha_creacion=e.fecha_creacion,
        )
        for e in estudiantes
    ]


@router.put("/docente/mis-estudiantes/{estudiante_id}", response_model=EstudianteListItem)
async def actualizar_estudiante(
    estudiante_id: int,
    data: RegistroDirectoRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    """Actualiza los datos básicos de un estudiante registrado por el docente."""
    if current_user.rol_codigo not in [r.value for r in CREADORES_ROLES]:
        raise HTTPException(403, "Permisos insuficientes")

    result = await db.execute(
        select(Usuario).where(
            Usuario.id == estudiante_id,
            Usuario.creado_por_id == current_user.id,
        )
    )
    estudiante = result.scalars().first()
    if not estudiante:
        raise HTTPException(404, "Estudiante no encontrado o no pertenece a tu registro")

    # Verificar DNI duplicado si cambió
    if data.dni and data.dni != estudiante.dni:
        existing = await db.execute(
            select(Usuario).where(Usuario.dni == data.dni, Usuario.id != estudiante_id)
        )
        if existing.scalars().first():
            raise HTTPException(400, "DNI ya registrado en el sistema")

    estudiante.nombres = data.nombres
    estudiante.apellidos = data.apellidos
    estudiante.dni = data.dni
    estudiante.grado_id = data.grado_id
    estudiante.seccion = data.seccion

    if data.password:
        from app.core.security import get_password_hash as _hash
        estudiante.password_hash = _hash(data.password)

    await db.flush()
    await db.refresh(estudiante)

    grado_result = await db.execute(select(Grado).where(Grado.id == data.grado_id))
    grado = grado_result.scalars().first()

    return EstudianteListItem(
        id=estudiante.id,
        codigo_estudiante=estudiante.codigo_estudiante,
        nombres=estudiante.nombres,
        apellidos=estudiante.apellidos,
        dni=estudiante.dni,
        grado_id=estudiante.grado_id,
        grado_nombre=grado.nombre if grado else None,
        seccion=estudiante.seccion,
        is_active=estudiante.is_active,
        fecha_creacion=estudiante.fecha_creacion,
    )


@router.delete("/docente/mis-estudiantes/{estudiante_id}")
async def eliminar_estudiante(
    estudiante_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    """Elimina un estudiante registrado por el docente."""
    if current_user.rol_codigo not in [r.value for r in CREADORES_ROLES]:
        raise HTTPException(403, "Permisos insuficientes")

    result = await db.execute(
        select(Usuario).where(
            Usuario.id == estudiante_id,
            Usuario.creado_por_id == current_user.id,
        )
    )
    estudiante = result.scalars().first()
    if not estudiante:
        raise HTTPException(404, "Estudiante no encontrado o no pertenece a tu registro")

    await db.delete(estudiante)
    await db.flush()
    return {"ok": True, "mensaje": "Estudiante eliminado correctamente"}
