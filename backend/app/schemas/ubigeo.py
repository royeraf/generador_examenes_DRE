from pydantic import BaseModel


class ProvinciaResponse(BaseModel):
    id: int
    nombre: str

    class Config:
        from_attributes = True


class DistritoResponse(BaseModel):
    id: int
    nombre: str
    provincia_id: int

    class Config:
        from_attributes = True
