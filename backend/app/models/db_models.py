from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class NivelEducativo(str, enum.Enum):
    """Nivel educativo enum."""
    PRIMARIA = "primaria"
    SECUNDARIA = "secundaria"


class TipoCapacidad(str, enum.Enum):
    """Tipo de capacidad para comprensión lectora."""
    LITERAL = "literal"
    INFERENCIAL = "inferencial"
    CRITICO = "critico"


class Grado(Base):
    """Modelo para grados escolares."""
    __tablename__ = "grados"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)  # "PRIMER GRADO DE PRIMARIA"
    numero = Column(Integer, nullable=False)  # 1, 2, 3, etc.
    nivel = Column(String(20), nullable=False)  # "primaria" o "secundaria"
    orden = Column(Integer, nullable=False)  # Orden global para ordenar todos los grados
    
    # Relationship
    desempenos = relationship("Desempeno", back_populates="grado")
    
    def __repr__(self):
        return f"<Grado {self.nombre}>"


class Capacidad(Base):
    """Modelo para capacidades de comprensión lectora."""
    __tablename__ = "capacidades"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(200), nullable=False)
    tipo = Column(String(20), nullable=False)  # literal, inferencial, critico
    descripcion = Column(Text, nullable=True)
    
    # Relationship
    desempenos = relationship("Desempeno", back_populates="capacidad")
    
    def __repr__(self):
        return f"<Capacidad {self.tipo}: {self.nombre[:50]}>"


class Desempeno(Base):
    """Modelo para desempeños precisados."""
    __tablename__ = "desempenos"
    
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(10), nullable=False)  # "01", "02", etc.
    descripcion = Column(Text, nullable=False)
    
    # Foreign keys
    grado_id = Column(Integer, ForeignKey("grados.id"), nullable=False)
    capacidad_id = Column(Integer, ForeignKey("capacidades.id"), nullable=False)
    
    # Relationships
    grado = relationship("Grado", back_populates="desempenos")
    capacidad = relationship("Capacidad", back_populates="desempenos")
    
    def __repr__(self):
        return f"<Desempeno {self.codigo}: {self.descripcion[:50]}>"
