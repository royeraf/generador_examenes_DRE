from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, model_validator


class PersonaReniecData(BaseModel):
    dni: str
    nombres: str
    apellido_paterno: str
    apellido_materno: str
    nombre_completo: str


class ConsultaDniResponse(BaseModel):
    success: bool
    message: str
    data: Optional[PersonaReniecData] = None


class MatriculaSchema(BaseModel):
    id: int
    año_escolar: int
    grado_id: int
    grado_nombre: Optional[str] = None
    seccion: str
    is_active: bool

    class Config:
        from_attributes = True


class UsuarioBase(BaseModel):
    nombres: Optional[str] = None
    apellidos: Optional[str] = None
    profesion: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    provincia_id: Optional[int] = None
    distrito_id: Optional[int] = None
    ugel_id: Optional[int] = None
    institucion_educativa_id: Optional[int] = None
    is_active: Optional[bool] = True
    permisos_modulos: Optional[List[str]] = None


class UsuarioAdminCreate(UsuarioBase):
    """Schema para crear cualquier usuario (por un admin/director/etc.)."""
    dni: Optional[str] = Field(None, min_length=8, max_length=8, pattern=r"^\d{8}$")
    rol_codigo: str
    password: str = Field(..., min_length=4, max_length=72)
    # Solo para estudiantes — se usan para crear la Matricula inicial
    grado_id: Optional[int] = None
    seccion: Optional[str] = None
    año_escolar: Optional[int] = None

    @model_validator(mode="after")
    def validar_identificacion(self):
        return self


class UsuarioUpdate(BaseModel):
    """Todos los campos opcionales para actualización parcial."""
    nombres: Optional[str] = None
    apellidos: Optional[str] = None
    profesion: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    provincia_id: Optional[int] = None
    distrito_id: Optional[int] = None
    ugel_id: Optional[int] = None
    institucion_educativa_id: Optional[int] = None
    is_active: Optional[bool] = None
    rol_codigo: Optional[str] = None
    password: Optional[str] = Field(None, min_length=4, max_length=72)
    permisos_modulos: Optional[List[str]] = None
    # Solo para estudiantes — actualizan la Matricula activa
    grado_id: Optional[int] = None
    seccion: Optional[str] = None
    año_escolar: Optional[int] = None


class UsuarioInDBBase(UsuarioBase):
    id: int
    dni: Optional[str] = None
    codigo_estudiante: Optional[str] = None  # siempre None para staff; None por compatibilidad
    rol_codigo: Optional[str] = None

    class Config:
        from_attributes = True


class Usuario(UsuarioInDBBase):
    creado_por_id: Optional[int] = None
    fecha_creacion: Optional[datetime] = None
    ultimo_acceso: Optional[datetime] = None
    provincia_nombre: Optional[str] = None
    distrito_nombre: Optional[str] = None
    ugel_nombre: Optional[str] = None
    institucion_nombre: Optional[str] = None
    modulos_efectivos: Optional[List[str]] = None
    matricula_activa: Optional[MatriculaSchema] = None


class UsuarioInDB(UsuarioInDBBase):
    password_hash: str


# Aliases de compatibilidad
Docente = Usuario
DocenteAdminCreate = UsuarioAdminCreate
DocenteUpdate = UsuarioUpdate
