from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Estudiante(Base):
    """Perfil de estudiante, separado del staff (tabla usuarios)."""
    __tablename__ = "estudiantes"

    id = Column(Integer, primary_key=True, index=True)
    dni = Column(String(8), unique=True, index=True, nullable=True)
    codigo_estudiante = Column(String(10), unique=True, index=True, nullable=True)
    nombres = Column(String(100), nullable=True)
    apellidos = Column(String(100), nullable=True)
    password_hash = Column(String(200), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    institucion_educativa_id = Column(
        Integer, ForeignKey("instituciones_educativas.id", ondelete="SET NULL"), nullable=True
    )
    distrito_id = Column(
        Integer, ForeignKey("distritos.id", ondelete="SET NULL"), nullable=True
    )
    creado_por_id = Column(
        Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ultimo_acceso = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    institucion_educativa = relationship("InstitucionEducativa", lazy="joined")
    distrito = relationship("Distrito", lazy="joined")
    creado_por = relationship("Usuario", foreign_keys=[creado_por_id])
    matriculas = relationship(
        "Matricula",
        foreign_keys="Matricula.estudiante_id",
        order_by="Matricula.año_escolar.desc()",
        lazy="select",
    )

    # ── Interface compatible con Usuario para auth y dependencias ─────────────

    @property
    def rol_codigo(self) -> str:
        from app.models.enums import RolCodigo
        return RolCodigo.ESTUDIANTE.value

    @property
    def modulos_efectivos(self) -> list:
        return []

    def tiene_modulo(self, modulo: str) -> bool:
        return False

    @property
    def is_superuser(self) -> bool:
        return False

    @property
    def institucion_nombre(self):
        return self.institucion_educativa.nombre if self.institucion_educativa else None

    @property
    def distrito_nombre(self):
        return self.distrito.nombre if self.distrito else None

    @property
    def ugel_id(self):
        return self.institucion_educativa.ugel_id if self.institucion_educativa else None

    @property
    def ugel_nombre(self):
        return None

    @property
    def provincia_nombre(self):
        return None

    @property
    def provincia_id(self):
        return None

    @property
    def permisos_modulos(self):
        return None

    @property
    def profesion(self):
        return None

    @property
    def email(self):
        return None

    @property
    def telefono(self):
        return None

    def __repr__(self):
        return f"<Estudiante {self.codigo_estudiante or self.dni}: {self.nombres}>"
