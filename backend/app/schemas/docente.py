from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class DocenteBase(BaseModel):
    dni: str = Field(..., min_length=8, max_length=8, pattern=r"^\d{8}$")
    nombres: Optional[str] = None
    apellidos: Optional[str] = None
    profesion: Optional[str] = None
    institucion_educativa: Optional[str] = None
    nivel_educativo: Optional[str] = None
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False


class DocenteCreate(DocenteBase):
    password: str = Field(..., min_length=6, max_length=72)


class DocenteAdminCreate(DocenteCreate):
    """Schema para que el admin cree usuarios (normales o admins)."""
    pass


class DocenteUpdate(BaseModel):
    """Todos los campos son opcionales para actualización parcial."""
    nombres: Optional[str] = None
    apellidos: Optional[str] = None
    profesion: Optional[str] = None
    institucion_educativa: Optional[str] = None
    nivel_educativo: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=6, max_length=72)


class DocenteInDBBase(DocenteBase):
    id: int

    class Config:
        from_attributes = True


class Docente(DocenteInDBBase):
    creado_por_id: Optional[int] = None
    fecha_creacion: Optional[datetime] = None


class DocenteInDB(DocenteInDBBase):
    password_hash: str
