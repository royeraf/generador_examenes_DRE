from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


# =============================================================================
# ENUMS
# =============================================================================

class NivelEducativo(str, enum.Enum):
    """Nivel educativo enum."""
    INICIAL = "inicial"
    PRIMARIA = "primaria"
    SECUNDARIA = "secundaria"


class TipoCapacidad(str, enum.Enum):
    """Tipo de capacidad para comprensión lectora."""
    LITERAL = "literal"
    INFERENCIAL = "inferencial"
    CRITICO = "critico"


class AreaCurricular(str, enum.Enum):
    """Área curricular del sistema."""
    COMUNICACION = "comunicacion"  # Comprensión lectora
    MATEMATICA = "matematica"


# =============================================================================
# MODELOS COMPARTIDOS
# =============================================================================

class Grado(Base):
    """Modelo para grados escolares (compartido entre áreas)."""
    __tablename__ = "grados"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)  # "PRIMER GRADO DE PRIMARIA"
    numero = Column(Integer, nullable=False)  # 1, 2, 3, etc. (0 para inicial)
    nivel = Column(String(20), nullable=False)  # "inicial", "primaria" o "secundaria"
    orden = Column(Integer, nullable=False)  # Orden global para ordenar todos los grados
    
    # Relationships - Comunicación
    desempenos = relationship("Desempeno", back_populates="grado")
    
    # Relationships - Matemática
    estandares_mat = relationship("EstandarMatematica", back_populates="grado")
    desempenos_mat = relationship("DesempenoMatematica", back_populates="grado")
    
    def __repr__(self):
        return f"<Grado {self.nombre}>"


# =============================================================================
# MODELOS DE COMUNICACIÓN (Comprensión Lectora) - LectoSistem
# =============================================================================

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
    """Modelo para desempeños precisados de comprensión lectora."""
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


# =============================================================================
# MODELOS DE MATEMÁTICA - MatSistem
# =============================================================================

class CompetenciaMatematica(Base):
    """
    Modelo para las 4 competencias matemáticas según MINEDU.
    
    1. Resuelve problemas de cantidad
    2. Resuelve problemas de regularidad, equivalencia y cambio
    3. Resuelve problemas de forma, movimiento y localización
    4. Resuelve problemas de gestión de datos e incertidumbre
    """
    __tablename__ = "competencias_matematica"
    
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(Integer, nullable=False, unique=True)  # 1, 2, 3, 4
    nombre = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=True)  # Descripción completa de la competencia
    
    # Relationships
    capacidades = relationship("CapacidadMatematica", back_populates="competencia")
    estandares = relationship("EstandarMatematica", back_populates="competencia")
    
    def __repr__(self):
        return f"<CompetenciaMat {self.codigo}: {self.nombre[:50]}>"


class CapacidadMatematica(Base):
    """
    Modelo para capacidades de matemática.
    Cada competencia tiene exactamente 4 capacidades.
    
    Ejemplo para Competencia 1 (Cantidad):
    1. Traduce cantidades a expresiones numéricas
    2. Comunica su comprensión sobre los números y las operaciones
    3. Usa estrategias y procedimientos de estimación y cálculo
    4. Argumenta afirmaciones sobre las relaciones numéricas y las operaciones
    """
    __tablename__ = "capacidades_matematica"
    
    id = Column(Integer, primary_key=True, index=True)
    orden = Column(Integer, nullable=False)  # 1, 2, 3, 4 (orden dentro de la competencia)
    nombre = Column(String(300), nullable=False)
    descripcion = Column(Text, nullable=True)
    
    # Foreign keys
    competencia_id = Column(Integer, ForeignKey("competencias_matematica.id"), nullable=False)
    
    # Relationships
    competencia = relationship("CompetenciaMatematica", back_populates="capacidades")
    desempenos = relationship("DesempenoMatematica", back_populates="capacidad")
    
    def __repr__(self):
        return f"<CapacidadMat {self.orden}: {self.nombre[:50]}>"


class EstandarMatematica(Base):
    """
    Modelo para estándares de aprendizaje de matemática.
    Define el nivel esperado al final de cada ciclo por competencia.
    """
    __tablename__ = "estandares_matematica"
    
    id = Column(Integer, primary_key=True, index=True)
    descripcion = Column(Text, nullable=False)
    ciclo = Column(String(20), nullable=True)  # "II", "III", "IV", "V", "VI", "VII"
    
    # Foreign keys
    grado_id = Column(Integer, ForeignKey("grados.id"), nullable=False)
    competencia_id = Column(Integer, ForeignKey("competencias_matematica.id"), nullable=False)
    
    # Relationships
    grado = relationship("Grado", back_populates="estandares_mat")
    competencia = relationship("CompetenciaMatematica", back_populates="estandares")
    
    def __repr__(self):
        return f"<EstandarMat grado={self.grado_id} comp={self.competencia_id}>"


class DesempenoMatematica(Base):
    """
    Modelo para desempeños de matemática.
    Especifica lo que el estudiante debe lograr por grado y capacidad.
    """
    __tablename__ = "desempenos_matematica"
    
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(10), nullable=False)  # Código secuencial por capacidad
    descripcion = Column(Text, nullable=False)
    
    # Foreign keys
    grado_id = Column(Integer, ForeignKey("grados.id"), nullable=False)
    capacidad_id = Column(Integer, ForeignKey("capacidades_matematica.id"), nullable=False)
    
    # Relationships
    grado = relationship("Grado", back_populates="desempenos_mat")
    capacidad = relationship("CapacidadMatematica", back_populates="desempenos")
    
    def __repr__(self):
        return f"<DesempenoMat {self.codigo}: {self.descripcion[:50]}>"
