from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class SesionAccesoOut(BaseModel):
    id: int
    exito: bool
    motivo: Optional[str] = None
    tipo_usuario: Optional[str] = None
    usuario_id: Optional[int] = None
    identificador: Optional[str] = None
    nombres: Optional[str] = None
    apellidos: Optional[str] = None
    rol_codigo: Optional[str] = None
    institucion_educativa_id: Optional[int] = None
    institucion_nombre: Optional[str] = None
    ugel_id: Optional[int] = None
    ugel_nombre: Optional[str] = None
    ip: Optional[str] = None
    dispositivo: Optional[str] = None
    sistema_operativo: Optional[str] = None
    navegador: Optional[str] = None
    es_movil: bool = False
    login_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    logout_at: Optional[datetime] = None
    is_active: bool = True
    en_linea: bool = False
    duracion_minutos: Optional[int] = None


class ConteoItem(BaseModel):
    clave: str
    total: int


class PuntoSerie(BaseModel):
    periodo: str
    total: int
    exitos: int = 0
    fallidos: int = 0


class ResumenMonitoreo(BaseModel):
    sesiones_activas: int
    estudiantes_activos: int
    staff_activos: int
    logins_hoy: int
    fallidos_hoy: int
    sesiones_hoy: int
    activos_por_rol: List[ConteoItem]
    activos_por_ugel: List[ConteoItem]
    top_instituciones: List[ConteoItem]
    ultima_actualizacion: datetime


class EstadisticasMonitoreo(BaseModel):
    accesos_por_hora: List[PuntoSerie]
    accesos_por_dia: List[PuntoSerie]
    dispositivos: List[ConteoItem]
    sistemas_operativos: List[ConteoItem]
    navegadores: List[ConteoItem]
    top_instituciones: List[ConteoItem]
    ultima_actualizacion: datetime
