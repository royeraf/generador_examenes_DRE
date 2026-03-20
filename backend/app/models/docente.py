from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Docente(Base):
    """Modelo para docentes que usan el sistema."""
    __tablename__ = "docentes"

    id = Column(Integer, primary_key=True, index=True)
    dni = Column(String(8), unique=True, index=True, nullable=False)
    nombres = Column(String(100), nullable=True)
    apellidos = Column(String(100), nullable=True)
    profesion = Column(String(100), nullable=True)
    institucion_educativa = Column(String(200), nullable=True)
    nivel_educativo = Column(String(50), nullable=True)
    password_hash = Column(String(200), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)

    # Ubicación geográfica
    provincia_id = Column(Integer, ForeignKey("provincias.id", ondelete="SET NULL"), nullable=True)
    distrito_id = Column(Integer, ForeignKey("distritos.id", ondelete="SET NULL"), nullable=True)

    # Rastreo de creación
    creado_por_id = Column(Integer, ForeignKey("docentes.id", ondelete="SET NULL"), nullable=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    examenes_lectura = relationship("ExamenLectura", back_populates="docente", cascade="all, delete-orphan")
    examenes_matematica = relationship("ExamenMatematica", back_populates="docente", cascade="all, delete-orphan")
    creado_por = relationship("Docente", remote_side=[id], foreign_keys=[creado_por_id])
    provincia = relationship("Provincia", lazy="joined")
    distrito = relationship("Distrito", lazy="joined")

    @property
    def provincia_nombre(self):
        return self.provincia.nombre if self.provincia else None

    @property
    def distrito_nombre(self):
        return self.distrito.nombre if self.distrito else None

    def __repr__(self):
        return f"<Docente {self.dni}: {self.nombres}>"
