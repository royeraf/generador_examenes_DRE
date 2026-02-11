from typing import Optional
from pydantic import BaseModel, Field

class DocenteBase(BaseModel):
    dni: str = Field(..., min_length=8, max_length=8, pattern=r"^\d{8}$")
    nombres: Optional[str] = None
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False

class DocenteCreate(DocenteBase):
    password: str = Field(..., min_length=6, max_length=72)

class DocenteUpdate(DocenteBase):
    password: Optional[str] = None

class DocenteInDBBase(DocenteBase):
    id: int

    class Config:
        from_attributes = True

class Docente(DocenteInDBBase):
    pass

class DocenteInDB(DocenteInDBBase):
    password_hash: str
