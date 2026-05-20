from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, model_validator


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
    grado_id: Optional[int] = None
    seccion: Optional[str] = None
    is_active: Optional[bool] = True
    permisos_modulos: Optional[List[str]] = None


class UsuarioAdminCreate(UsuarioBase):
    """Schema para crear cualquier usuario (por un admin/director/etc.)."""
    dni: Optional[str] = Field(None, min_length=8, max_length=8, pattern=r"^\d{8}$")
    rol_codigo: str
    password: str = Field(..., min_length=4, max_length=72)

    @model_validator(mode="after")
    def validar_identificacion(self):
        # Al menos DNI o será generado código de estudiante automáticamente
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
    grado_id: Optional[int] = None
    seccion: Optional[str] = None
    is_active: Optional[bool] = None
    rol_codigo: Optional[str] = None
    password: Optional[str] = Field(None, min_length=4, max_length=72)
    permisos_modulos: Optional[List[str]] = None


class UsuarioInDBBase(UsuarioBase):
    id: int
    dni: Optional[str] = None
    codigo_estudiante: Optional[str] = None
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
    grado_nombre: Optional[str] = None
    modulos_efectivos: Optional[List[str]] = None


class UsuarioInDB(UsuarioInDBBase):
    password_hash: str


# Alias de compatibilidad para código que todavía usa el schema "Docente"
Docente = Usuario
DocenteAdminCreate = UsuarioAdminCreate
DocenteUpdate = UsuarioUpdate
