"""
Rutas para auto-registro de estudiantes y gestión de códigos de clase.
"""
import random
import string
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.db_models import CodigoClase, Grado, InstitucionEducativa, Matricula
from app.models.usuario import Usuario
from app.models.estudiante import Estudiante
from app.models.enums import RolCodigo
from app.api.dependencies import get_current_active_user, require_role, require_modulo
from app.core.security import get_password_hash
from app.services.matricula_service import crear_matricula, get_matricula_activa
from app.services.estudiante_service import estudiante_service

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
    año_escolar: int = Field(default_factory=lambda: datetime.now().year)


class CodigoClaseResponse(BaseModel):
    id: int
    codigo: str
    grado_id: int
    grado_nombre: Optional[str] = None
    seccion: str
    año_escolar: int
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


class RegistroDirectoRequest(BaseModel):
    nombres: str = Field(..., min_length=2, max_length=100)
    apellidos: str = Field(..., min_length=2, max_length=100)
    dni: Optional[str] = Field(None, min_length=8, max_length=8, pattern=r"^\d{8}$")
    password: str = Field(..., min_length=4, max_length=72)
    grado_id: int
    seccion: str = Field(..., min_length=1, max_length=10)
    año_escolar: int = Field(default_factory=lambda: datetime.now().year)


class EstudianteListItem(BaseModel):
    id: int
    codigo_estudiante: Optional[str] = None
    nombres: Optional[str] = None
    apellidos: Optional[str] = None
    dni: Optional[str] = None
    # Datos de matrícula activa
    matricula_id: Optional[int] = None
    grado_id: Optional[int] = None
    grado_nombre: Optional[str] = None
    seccion: Optional[str] = None
    año_escolar: Optional[int] = None
    is_active: bool
    fecha_creacion: Optional[datetime] = None

    class Config:
        from_attributes = True


class ImportarEstudianteFila(BaseModel):
    dni: str = Field(..., min_length=8, max_length=8, pattern=r"^\d{8}$")
    nombres: str = Field(..., min_length=2, max_length=100)
    apellidos: str = Field(..., min_length=2, max_length=100)


class ImportarEstudiantesRequest(BaseModel):
    grado_id: int
    seccion: str = Field(..., min_length=1, max_length=10)
    año_escolar: int = Field(default_factory=lambda: datetime.now().year)
    estudiantes: List[ImportarEstudianteFila] = Field(..., min_length=1, max_length=500)


class ImportarEstudiantesResponse(BaseModel):
    creados: int
    pendientes_generacion_usuario: int


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _generar_codigo_clase() -> str:
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choices(chars, k=8))


async def _get_or_create_aula(
    db: AsyncSession,
    institucion_educativa_id: int,
    grado_id: int,
    seccion: str,
    año_escolar: int,
    creado_por_id: int,
) -> CodigoClase:
    result = await db.execute(
        select(CodigoClase).where(
            CodigoClase.institucion_educativa_id == institucion_educativa_id,
            CodigoClase.grado_id == grado_id,
            CodigoClase.seccion == seccion,
            CodigoClase.año_escolar == año_escolar,
        )
    )
    aula = result.scalars().first()
    if aula:
        return aula

    for _ in range(10):
        codigo = _generar_codigo_clase()
        existing = await db.execute(select(CodigoClase).where(CodigoClase.codigo == codigo))
        if not existing.scalars().first():
            break

    aula = CodigoClase(
        codigo=codigo,
        creado_por_id=creado_por_id,
        institucion_educativa_id=institucion_educativa_id,
        grado_id=grado_id,
        seccion=seccion,
        año_escolar=año_escolar,
    )
    db.add(aula)
    await db.flush()
    return aula


async def _siguiente_codigo_estudiante(db: AsyncSession) -> str:
    result = await db.execute(
        select(func.max(Estudiante.codigo_estudiante)).where(
            Estudiante.codigo_estudiante.isnot(None)
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

    # Contar matriculas activas agrupadas por ie+grado+seccion+año en un solo query
    estudiantes_map: dict = {}
    if codigos:
        from sqlalchemy import tuple_
        claves = [(c.institucion_educativa_id, c.grado_id, c.seccion, c.año_escolar) for c in codigos]
        cnt_r = await db.execute(
            select(
                Matricula.institucion_educativa_id,
                Matricula.grado_id,
                Matricula.seccion,
                Matricula.año_escolar,
                func.count(Matricula.id).label("total"),
            )
            .where(
                tuple_(
                    Matricula.institucion_educativa_id,
                    Matricula.grado_id,
                    Matricula.seccion,
                    Matricula.año_escolar,
                ).in_(claves),
                Matricula.is_active == True,
            )
            .group_by(
                Matricula.institucion_educativa_id,
                Matricula.grado_id,
                Matricula.seccion,
                Matricula.año_escolar,
            )
        )
        for row in cnt_r:
            estudiantes_map[(row.institucion_educativa_id, row.grado_id, row.seccion, row.año_escolar)] = row.total

    return [
        CodigoClaseResponse(
            id=c.id, codigo=c.codigo,
            grado_id=c.grado_id, grado_nombre=grado_map.get(c.grado_id),
            seccion=c.seccion, año_escolar=c.año_escolar, max_estudiantes=c.max_estudiantes,
            is_active=c.is_active, fecha_creacion=c.fecha_creacion,
            fecha_expiracion=c.fecha_expiracion,
            institucion_nombre=ie_map.get(c.institucion_educativa_id),
            total_estudiantes=estudiantes_map.get(
                (c.institucion_educativa_id, c.grado_id, c.seccion, c.año_escolar), 0
            ),
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

    duplicado = await db.execute(
        select(CodigoClase).where(
            CodigoClase.institucion_educativa_id == current_user.institucion_educativa_id,
            CodigoClase.grado_id == data.grado_id,
            CodigoClase.seccion == data.seccion,
            CodigoClase.año_escolar == data.año_escolar,
            CodigoClase.is_active == True,
        )
    )
    if duplicado.scalars().first():
        raise HTTPException(400, "Ya existe un aula activa para ese grado, sección y año escolar en tu institución")

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
        año_escolar=data.año_escolar,
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
        seccion=cc.seccion, año_escolar=cc.año_escolar,
        max_estudiantes=cc.max_estudiantes,
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




# ─── Auto-registro de estudiantes (público) ───────────────────────────────────

@router.post("/registro/estudiante", response_model=RegistroEstudianteResponse)
async def registrar_estudiante(
    data: RegistroEstudianteRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CodigoClase).where(CodigoClase.codigo == data.codigo_clase.upper())
    )
    cc = result.scalars().first()
    if not cc or not cc.is_active:
        raise HTTPException(400, "Código de clase inválido o inactivo")

    if cc.fecha_expiracion and cc.fecha_expiracion < datetime.now(timezone.utc):
        raise HTTPException(400, "El código de clase ha expirado")

    if data.dni:
        existing = await db.execute(select(Estudiante).where(Estudiante.dni == data.dni))
        if existing.scalars().first():
            raise HTTPException(400, "DNI ya registrado")

    # Contar matriculados en este grado/sección/año via tabla matriculas
    count_result = await db.execute(
        select(func.count(Matricula.id)).where(
            Matricula.grado_id == cc.grado_id,
            Matricula.seccion == cc.seccion,
            Matricula.año_escolar == cc.año_escolar,
            Matricula.institucion_educativa_id == cc.institucion_educativa_id,
            Matricula.is_active == True,
        )
    )
    if (count_result.scalar() or 0) >= cc.max_estudiantes:
        raise HTTPException(400, "El código de clase ha alcanzado el máximo de estudiantes")

    codigo_estudiante = await _siguiente_codigo_estudiante(db)

    estudiante = await estudiante_service.crear_estudiante(
        db,
        dni=data.dni,
        nombres=data.nombres,
        apellidos=data.apellidos,
        password=data.password,
        institucion_educativa_id=cc.institucion_educativa_id,
        creado_por_id=cc.creado_por_id,
        codigo_estudiante=codigo_estudiante,
        grado_id=cc.grado_id,
        seccion=cc.seccion,
        año_escolar=cc.año_escolar,
    )
    matricula = await get_matricula_activa(db, estudiante.id)

    ie_result = await db.execute(
        select(InstitucionEducativa).where(InstitucionEducativa.id == cc.institucion_educativa_id)
    )
    ie = ie_result.scalars().first()

    return RegistroEstudianteResponse(
        id=estudiante.id,
        codigo_estudiante=codigo_estudiante,
        nombres=estudiante.nombres,
        apellidos=estudiante.apellidos,
        grado=matricula.grado.nombre if matricula.grado else None,
        seccion=matricula.seccion,
        institucion=ie.nombre if ie else None,
    )


@router.get("/registro/validar-codigo/{codigo}")
async def validar_codigo_clase(
    codigo: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CodigoClase).where(CodigoClase.codigo == codigo.upper())
    )
    cc = result.scalars().first()
    if not cc or not cc.is_active:
        raise HTTPException(400, "Código inválido o inactivo")
    if cc.fecha_expiracion and cc.fecha_expiracion < datetime.now(timezone.utc):
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

@router.post("/docente/registrar-estudiante", response_model=RegistroEstudianteResponse, status_code=201)
async def registrar_estudiante_directo(
    data: RegistroDirectoRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    if current_user.rol_codigo not in [r.value for r in CREADORES_ROLES]:
        raise HTTPException(403, "Solo docentes, auxiliares, directores o especialistas DRE pueden usar este endpoint")

    if not current_user.institucion_educativa_id:
        raise HTTPException(400, "No tienes una institución educativa asignada")

    if data.dni:
        existing = await db.execute(select(Estudiante).where(Estudiante.dni == data.dni))
        if existing.scalars().first():
            raise HTTPException(400, "DNI ya registrado en el sistema")

    codigo_estudiante = await _siguiente_codigo_estudiante(db)
    año_escolar = data.año_escolar or datetime.now().year

    await _get_or_create_aula(
        db,
        institucion_educativa_id=current_user.institucion_educativa_id,
        grado_id=data.grado_id,
        seccion=data.seccion,
        año_escolar=año_escolar,
        creado_por_id=current_user.id,
    )

    estudiante = await estudiante_service.crear_estudiante(
        db,
        dni=data.dni,
        nombres=data.nombres,
        apellidos=data.apellidos,
        password=data.password,
        institucion_educativa_id=current_user.institucion_educativa_id,
        creado_por_id=current_user.id,
        codigo_estudiante=codigo_estudiante,
        grado_id=data.grado_id,
        seccion=data.seccion,
        año_escolar=año_escolar,
        ugel_id=current_user.ugel_id,
    )
    matricula = await get_matricula_activa(db, estudiante.id)

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
        grado=matricula.grado.nombre if matricula.grado else None,
        seccion=matricula.seccion,
        institucion=ie.nombre if ie else None,
    )


@router.post("/docente/importar-estudiantes", response_model=ImportarEstudiantesResponse, status_code=201)
async def importar_estudiantes_desde_nomina(
    data: ImportarEstudiantesRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    if current_user.rol_codigo not in [r.value for r in CREADORES_ROLES]:
        raise HTTPException(403, "Solo docentes, auxiliares, directores o especialistas DRE pueden usar este endpoint")

    if not current_user.institucion_educativa_id:
        raise HTTPException(400, "No tienes una institución educativa asignada")

    grado_result = await db.execute(select(Grado).where(Grado.id == data.grado_id))
    if not grado_result.scalars().first():
        raise HTTPException(400, "El grado seleccionado no existe")

    dnis = [fila.dni.strip() for fila in data.estudiantes]
    duplicated_dnis = sorted({dni for dni in dnis if dnis.count(dni) > 1})
    if duplicated_dnis:
        raise HTTPException(400, f"El archivo contiene DNI repetidos: {', '.join(duplicated_dnis[:10])}")

    existing_result = await db.execute(select(Estudiante.dni).where(Estudiante.dni.in_(dnis)))
    existing_dnis = sorted({dni for dni in existing_result.scalars().all() if dni})
    if existing_dnis:
        raise HTTPException(400, f"Los siguientes DNI ya están registrados: {', '.join(existing_dnis[:10])}")

    año_escolar = data.año_escolar or datetime.now().year

    await _get_or_create_aula(
        db,
        institucion_educativa_id=current_user.institucion_educativa_id,
        grado_id=data.grado_id,
        seccion=data.seccion.strip(),
        año_escolar=año_escolar,
        creado_por_id=current_user.id,
    )

    creados = 0
    for fila in data.estudiantes:
        await estudiante_service.crear_estudiante(
            db,
            dni=fila.dni.strip(),
            nombres=fila.nombres.strip(),
            apellidos=fila.apellidos.strip(),
            password=f"PENDIENTE-{fila.dni.strip()}",
            institucion_educativa_id=current_user.institucion_educativa_id,
            creado_por_id=current_user.id,
            is_active=False,
            grado_id=data.grado_id,
            seccion=data.seccion.strip(),
            año_escolar=año_escolar,
            ugel_id=current_user.ugel_id,
        )
        creados += 1

    return ImportarEstudiantesResponse(creados=creados, pendientes_generacion_usuario=creados)


@router.get("/docente/mis-estudiantes", response_model=List[EstudianteListItem])
async def listar_mis_estudiantes(
    grado_id: Optional[int] = Query(None),
    seccion: Optional[str] = Query(None),
    año_escolar: Optional[int] = Query(None),
    q: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    if current_user.rol_codigo not in [r.value for r in CREADORES_ROLES]:
        raise HTTPException(403, "Permisos insuficientes")

    from sqlalchemy import and_, or_
    stmt = (
        select(Estudiante, Matricula)
        .outerjoin(Matricula, and_(
            Matricula.estudiante_id == Estudiante.id,
            Matricula.is_active == True,
        ))
        .where(Estudiante.creado_por_id == current_user.id)
    )

    if grado_id:
        stmt = stmt.where(Matricula.grado_id == grado_id)
    if seccion:
        stmt = stmt.where(Matricula.seccion == seccion)
    if año_escolar:
        stmt = stmt.where(Matricula.año_escolar == año_escolar)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            or_(
                Estudiante.nombres.ilike(like),
                Estudiante.apellidos.ilike(like),
                Estudiante.dni.ilike(like),
                Estudiante.codigo_estudiante.ilike(like),
            )
        )

    stmt = stmt.order_by(Estudiante.apellidos, Estudiante.nombres)
    result = await db.execute(stmt)
    rows = result.all()

    # Cargar nombres de grados en batch
    grado_ids = list({m.grado_id for _, m in rows if m})
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
            matricula_id=m.id if m else None,
            grado_id=m.grado_id if m else None,
            grado_nombre=grado_map.get(m.grado_id) if m else None,
            seccion=m.seccion if m else None,
            año_escolar=m.año_escolar if m else None,
            is_active=e.is_active,
            fecha_creacion=e.fecha_creacion,
        )
        for e, m in rows
    ]


@router.put("/docente/mis-estudiantes/{estudiante_id}", response_model=EstudianteListItem)
async def actualizar_estudiante(
    estudiante_id: int,
    data: RegistroDirectoRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    if current_user.rol_codigo not in [r.value for r in CREADORES_ROLES]:
        raise HTTPException(403, "Permisos insuficientes")

    result = await db.execute(
        select(Estudiante).where(
            Estudiante.id == estudiante_id,
            Estudiante.creado_por_id == current_user.id,
        )
    )
    estudiante = result.scalars().first()
    if not estudiante:
        raise HTTPException(404, "Estudiante no encontrado o no pertenece a tu registro")

    if data.dni and data.dni != estudiante.dni:
        existing = await db.execute(
            select(Estudiante).where(Estudiante.dni == data.dni, Estudiante.id != estudiante_id)
        )
        if existing.scalars().first():
            raise HTTPException(400, "DNI ya registrado en el sistema")

    estudiante.nombres = data.nombres
    estudiante.apellidos = data.apellidos
    estudiante.dni = data.dni

    if data.password:
        from app.core.security import get_password_hash as _hash
        if not estudiante.codigo_estudiante:
            estudiante.codigo_estudiante = await _siguiente_codigo_estudiante(db)
        estudiante.password_hash = _hash(data.password)
        estudiante.is_active = True

    # Actualizar matrícula activa
    matricula = await get_matricula_activa(db, estudiante_id)
    if matricula:
        matricula.grado_id = data.grado_id
        matricula.seccion = data.seccion
        matricula.año_escolar = data.año_escolar
    else:
        matricula = await crear_matricula(
            db,
            estudiante_id=estudiante_id,
            grado_id=data.grado_id,
            seccion=data.seccion,
            año_escolar=data.año_escolar,
            institucion_educativa_id=estudiante.institucion_educativa_id,
            ugel_id=estudiante.ugel_id,
        )

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
        matricula_id=matricula.id,
        grado_id=matricula.grado_id,
        grado_nombre=grado.nombre if grado else None,
        seccion=matricula.seccion,
        año_escolar=matricula.año_escolar,
        is_active=estudiante.is_active,
        fecha_creacion=estudiante.fecha_creacion,
    )


@router.patch("/docente/mis-estudiantes/{estudiante_id}/toggle-active")
async def toggle_estudiante_activo(
    estudiante_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    if current_user.rol_codigo not in [r.value for r in CREADORES_ROLES]:
        raise HTTPException(403, "Permisos insuficientes")

    result = await db.execute(
        select(Estudiante).where(
            Estudiante.id == estudiante_id,
            Estudiante.creado_por_id == current_user.id,
        )
    )
    estudiante = result.scalars().first()
    if not estudiante:
        raise HTTPException(404, "Estudiante no encontrado o no pertenece a tu registro")

    estudiante.is_active = not estudiante.is_active
    await db.flush()
    return {"id": estudiante.id, "is_active": estudiante.is_active}


# ─── Nueva matrícula / avance de año ─────────────────────────────────────────

class NuevaMatriculaRequest(BaseModel):
    grado_id: int
    seccion: str = Field(..., min_length=1, max_length=10)
    año_escolar: int = Field(default_factory=lambda: datetime.now().year)


@router.post("/docente/mis-estudiantes/{estudiante_id}/nueva-matricula", response_model=EstudianteListItem)
async def nueva_matricula(
    estudiante_id: int,
    data: NuevaMatriculaRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    """Crea una nueva matrícula para el estudiante, archivando la anterior.
    Usado para avanzar de año escolar."""
    if current_user.rol_codigo not in [r.value for r in CREADORES_ROLES]:
        raise HTTPException(403, "Permisos insuficientes")

    result = await db.execute(
        select(Estudiante).where(
            Estudiante.id == estudiante_id,
            Estudiante.creado_por_id == current_user.id,
        )
    )
    estudiante = result.scalars().first()
    if not estudiante:
        raise HTTPException(404, "Estudiante no encontrado o no pertenece a tu registro")

    # Verificar que no exista ya una matrícula para ese año
    existing = await db.execute(
        select(Matricula).where(
            Matricula.estudiante_id == estudiante_id,
            Matricula.año_escolar == data.año_escolar,
        )
    )
    if existing.scalars().first():
        raise HTTPException(400, f"El estudiante ya tiene una matrícula para {data.año_escolar}")

    # Desactivar todas las matrículas anteriores
    mats = await db.execute(
        select(Matricula).where(
            Matricula.estudiante_id == estudiante_id,
            Matricula.is_active == True,
        )
    )
    for m in mats.scalars().all():
        m.is_active = False

    # Crear la nueva matrícula activa
    nueva = await crear_matricula(
        db,
        estudiante_id=estudiante_id,
        grado_id=data.grado_id,
        seccion=data.seccion,
        año_escolar=data.año_escolar,
        institucion_educativa_id=estudiante.institucion_educativa_id,
        ugel_id=estudiante.ugel_id,
    )

    await db.flush()

    grado_result = await db.execute(select(Grado).where(Grado.id == data.grado_id))
    grado = grado_result.scalars().first()

    return EstudianteListItem(
        id=estudiante.id,
        codigo_estudiante=estudiante.codigo_estudiante,
        nombres=estudiante.nombres,
        apellidos=estudiante.apellidos,
        dni=estudiante.dni,
        matricula_id=nueva.id,
        grado_id=nueva.grado_id,
        grado_nombre=grado.nombre if grado else None,
        seccion=nueva.seccion,
        año_escolar=nueva.año_escolar,
        is_active=estudiante.is_active,
        fecha_creacion=estudiante.fecha_creacion,
    )
