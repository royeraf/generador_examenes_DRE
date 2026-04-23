from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from typing import List
from app.core.database import Base


class Usuario(Base):
    """Modelo unificado de usuario para todos los roles del sistema."""
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)

    # Identificación — dni puede ser null para estudiantes sin DNI
    dni = Column(String(8), unique=True, index=True, nullable=True)
    # Código amigable para estudiantes: EST0001, EST0002, etc.
    codigo_estudiante = Column(String(10), unique=True, index=True, nullable=True)

    nombres = Column(String(100), nullable=True)
    apellidos = Column(String(100), nullable=True)
    profesion = Column(String(100), nullable=True)
    email = Column(String(200), nullable=True)
    telefono = Column(String(20), nullable=True)
    password_hash = Column(String(200), nullable=False)
    is_active = Column(Boolean, default=True)

    # Rol del usuario (FK a tabla roles)
    rol_id = Column(Integer, ForeignKey("roles.id"), nullable=False)

    # Jerarquía organizacional
    ugel_id = Column(Integer, ForeignKey("ugeles.id", ondelete="SET NULL"), nullable=True)
    institucion_educativa_id = Column(
        Integer, ForeignKey("instituciones_educativas.id", ondelete="SET NULL"), nullable=True
    )

    # Solo para estudiantes
    grado_id = Column(Integer, ForeignKey("grados.id", ondelete="SET NULL"), nullable=True)
    seccion = Column(String(10), nullable=True)

    # Ubicación geográfica
    provincia_id = Column(Integer, ForeignKey("provincias.id", ondelete="SET NULL"), nullable=True)
    distrito_id = Column(Integer, ForeignKey("distritos.id", ondelete="SET NULL"), nullable=True)

    # Permisos de módulos (anula los defaults del rol si se especifica)
    # Ejemplo: ["lectosistem", "metricas"]  — NULL = usar defaults del rol
    permisos_modulos = Column(JSON, nullable=True)

    # Rastreo
    creado_por_id = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ultimo_acceso = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    rol = relationship("Rol", lazy="joined")
    ugel = relationship("Ugel", lazy="joined")
    institucion_educativa = relationship("InstitucionEducativa", lazy="joined")
    grado = relationship("Grado", foreign_keys=[grado_id], lazy="joined")
    provincia = relationship("Provincia", lazy="joined")
    distrito = relationship("Distrito", lazy="joined")
    creado_por = relationship("Usuario", remote_side=[id], foreign_keys=[creado_por_id])

    examenes_lectura = relationship("ExamenLectura", back_populates="usuario", cascade="all, delete-orphan")
    examenes_matematica = relationship("ExamenMatematica", back_populates="usuario", cascade="all, delete-orphan")

    @property
    def rol_codigo(self) -> str:
        return self.rol.codigo if self.rol else None

    @property
    def provincia_nombre(self):
        return self.provincia.nombre if self.provincia else None

    @property
    def distrito_nombre(self):
        return self.distrito.nombre if self.distrito else None

    @property
    def grado_nombre(self):
        return self.grado.nombre if self.grado else None

    @property
    def ugel_nombre(self):
        return self.ugel.nombre if self.ugel else None

    @property
    def institucion_nombre(self):
        return self.institucion_educativa.nombre if self.institucion_educativa else None

    @property
    def modulos_efectivos(self) -> List[str]:
        """Módulos accesibles: permisos_modulos > rol.modulos_default > hardcoded enums."""
        if self.permisos_modulos:
            return self.permisos_modulos
        if self.rol and self.rol.modulos_default:
            return self.rol.modulos_default
        from app.models.enums import ROLE_MODULOS_DEFAULT
        return ROLE_MODULOS_DEFAULT.get(self.rol_codigo, [])

    def tiene_modulo(self, modulo: str) -> bool:
        return modulo in self.modulos_efectivos

    # Compatibilidad con código anterior
    @property
    def is_superuser(self) -> bool:
        from app.models.enums import RolCodigo
        return self.rol_codigo in (
            RolCodigo.ESPECIALISTA_DRE_COMUNICACION,
            RolCodigo.ESPECIALISTA_DRE_MATEMATICA,
        )

    def __repr__(self):
        return f"<Usuario {self.dni or self.codigo_estudiante}: {self.nombres}>"
