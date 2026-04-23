from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum, DateTime, JSON, Boolean, Float, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
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
    COMUNICACION = "comunicacion"
    MATEMATICA = "matematica"


# =============================================================================
# ORGANIZACIÓN: ROLES, UGELES, INSTITUCIONES EDUCATIVAS
# =============================================================================

class Rol(Base):
    """Roles del sistema. Tabla semilla con 7 registros fijos."""
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(50), unique=True, nullable=False, index=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text, nullable=True)
    nivel = Column(Integer, nullable=False)  # 1=DRE, 2=UGEL, 3=IE, 4=Auxiliar, 5=Docente, 6=Estudiante
    orden = Column(Integer, nullable=False)
    # Módulos habilitados por defecto para este rol (NULL = usar hardcoded en enums.py)
    modulos_default = Column(JSON, nullable=True)

    def __repr__(self):
        return f"<Rol {self.codigo}>"


class Ugel(Base):
    """Unidades de Gestión Educativa Local."""
    __tablename__ = "ugeles"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(20), unique=True, nullable=False)
    nombre = Column(String(200), nullable=False)
    provincia_id = Column(Integer, ForeignKey("provincias.id", ondelete="SET NULL"), nullable=True)
    is_active = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())

    provincia = relationship("Provincia", lazy="joined")
    instituciones = relationship("InstitucionEducativa", back_populates="ugel")

    @property
    def provincia_nombre(self):
        return self.provincia.nombre if self.provincia else None

    def __repr__(self):
        return f"<Ugel {self.nombre}>"


class InstitucionEducativa(Base):
    """Instituciones Educativas dentro de una UGEL."""
    __tablename__ = "instituciones_educativas"

    id = Column(Integer, primary_key=True, index=True)
    codigo_modular = Column(String(20), unique=True, nullable=False)
    nombre = Column(String(300), nullable=False)
    # Lista de niveles: ["inicial"], ["primaria"], ["secundaria"], o combinaciones
    nivel_educativo = Column(JSON, nullable=False)
    direccion = Column(Text, nullable=True)
    ugel_id = Column(Integer, ForeignKey("ugeles.id"), nullable=False)
    distrito_id = Column(Integer, ForeignKey("distritos.id", ondelete="SET NULL"), nullable=True)
    is_active = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())

    ugel = relationship("Ugel", back_populates="instituciones")
    distrito = relationship("Distrito", lazy="joined")

    @property
    def distrito_nombre(self):
        return self.distrito.nombre if self.distrito else None

    def __repr__(self):
        return f"<IE {self.nombre}>"


class CodigoClase(Base):
    """Códigos generados por docentes/directores para auto-registro de estudiantes."""
    __tablename__ = "codigos_clase"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(10), unique=True, nullable=False, index=True)
    creado_por_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    institucion_educativa_id = Column(Integer, ForeignKey("instituciones_educativas.id"), nullable=False)
    grado_id = Column(Integer, ForeignKey("grados.id"), nullable=False)
    seccion = Column(String(10), nullable=False)
    max_estudiantes = Column(Integer, default=40)
    is_active = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    fecha_expiracion = Column(DateTime(timezone=True), nullable=True)

    creado_por = relationship("Usuario", foreign_keys=[creado_por_id])
    institucion_educativa = relationship("InstitucionEducativa")
    grado = relationship("Grado")

    def __repr__(self):
        return f"<CodigoClase {self.codigo} grado={self.grado_id} seccion={self.seccion}>"


# =============================================================================
# MODELOS COMPARTIDOS
# =============================================================================

class Grado(Base):
    """Modelo para grados escolares (compartido entre áreas)."""
    __tablename__ = "grados"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    numero = Column(Integer, nullable=False)
    nivel = Column(String(20), nullable=False)
    orden = Column(Integer, nullable=False)

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
    tipo = Column(String(20), nullable=False)
    descripcion = Column(Text, nullable=True)

    desempenos = relationship("Desempeno", back_populates="capacidad")

    def __repr__(self):
        return f"<Capacidad {self.tipo}: {self.nombre[:50]}>"


class Desempeno(Base):
    """Modelo para desempeños precisados de comprensión lectora."""
    __tablename__ = "desempenos"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(10), nullable=False)
    descripcion = Column(Text, nullable=False)

    grado_id = Column(Integer, ForeignKey("grados.id"), nullable=False)
    capacidad_id = Column(Integer, ForeignKey("capacidades.id"), nullable=False)

    grado = relationship("Grado", back_populates="desempenos")
    capacidad = relationship("Capacidad", back_populates="desempenos")

    def __repr__(self):
        return f"<Desempeno {self.codigo}: {self.descripcion[:50]}>"


# =============================================================================
# MODELOS DE MATEMÁTICA - MatSistem
# =============================================================================

class CompetenciaMatematica(Base):
    """Las 4 competencias matemáticas según MINEDU."""
    __tablename__ = "competencias_matematica"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(Integer, nullable=False, unique=True)
    nombre = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=True)

    capacidades = relationship("CapacidadMatematica", back_populates="competencia")
    estandares = relationship("EstandarMatematica", back_populates="competencia")

    def __repr__(self):
        return f"<CompetenciaMat {self.codigo}: {self.nombre[:50]}>"


class CapacidadMatematica(Base):
    """Capacidades de matemática (4 por competencia)."""
    __tablename__ = "capacidades_matematica"

    id = Column(Integer, primary_key=True, index=True)
    orden = Column(Integer, nullable=False)
    nombre = Column(String(300), nullable=False)
    descripcion = Column(Text, nullable=True)

    competencia_id = Column(Integer, ForeignKey("competencias_matematica.id"), nullable=False)

    competencia = relationship("CompetenciaMatematica", back_populates="capacidades")
    desempenos = relationship("DesempenoMatematica", back_populates="capacidad")

    def __repr__(self):
        return f"<CapacidadMat {self.orden}: {self.nombre[:50]}>"


class EstandarMatematica(Base):
    """Estándares de aprendizaje de matemática por ciclo."""
    __tablename__ = "estandares_matematica"

    id = Column(Integer, primary_key=True, index=True)
    descripcion = Column(Text, nullable=False)
    ciclo = Column(String(20), nullable=True)

    grado_id = Column(Integer, ForeignKey("grados.id"), nullable=False)
    competencia_id = Column(Integer, ForeignKey("competencias_matematica.id"), nullable=False)

    grado = relationship("Grado", back_populates="estandares_mat")
    competencia = relationship("CompetenciaMatematica", back_populates="estandares")

    def __repr__(self):
        return f"<EstandarMat grado={self.grado_id} comp={self.competencia_id}>"


class DesempenoMatematica(Base):
    """Desempeños de matemática por grado y capacidad."""
    __tablename__ = "desempenos_matematica"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(10), nullable=False)
    descripcion = Column(Text, nullable=False)

    grado_id = Column(Integer, ForeignKey("grados.id"), nullable=False)
    capacidad_id = Column(Integer, ForeignKey("capacidades_matematica.id"), nullable=False)

    grado = relationship("Grado", back_populates="desempenos_mat")
    capacidad = relationship("CapacidadMatematica", back_populates="desempenos")

    def __repr__(self):
        return f"<DesempenoMat {self.codigo}: {self.descripcion[:50]}>"


# =============================================================================
# MODELOS DE EXÁMENES GENERADOS
# =============================================================================

class ExamenLectura(Base):
    """Exámenes de comprensión lectora generados por docentes."""
    __tablename__ = "examenes_lectura"

    id = Column(Integer, primary_key=True, index=True)
    # FK a usuarios (antes docentes) — columna renombrada para compatibilidad
    docente_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    grado_id = Column(Integer, ForeignKey("grados.id"), nullable=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    titulo = Column(String(300), nullable=True)
    grado_nombre = Column(String(100), nullable=True)
    nivel_dificultad = Column(String(50), nullable=True)
    modelo_ia = Column(String(50), nullable=True)

    saludo = Column(Text, nullable=True)
    instrucciones = Column(Text, nullable=True)
    lectura = Column(Text, nullable=True)
    preguntas = Column(JSON, nullable=True)
    tabla_respuestas = Column(JSON, nullable=True)
    desempenos_usados = Column(Text, nullable=True)

    usuario = relationship("Usuario", back_populates="examenes_lectura", foreign_keys=[docente_id])
    grado = relationship("Grado")

    def __repr__(self):
        return f"<ExamenLectura id={self.id} docente={self.docente_id} grado={self.grado_nombre}>"


class ExamenMatematica(Base):
    """Exámenes de matemática generados por docentes."""
    __tablename__ = "examenes_matematica"

    id = Column(Integer, primary_key=True, index=True)
    docente_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    grado_id = Column(Integer, ForeignKey("grados.id"), nullable=True)
    competencia_id = Column(Integer, ForeignKey("competencias_matematica.id"), nullable=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    titulo = Column(String(300), nullable=True)
    grado_nombre = Column(String(100), nullable=True)
    nivel_dificultad = Column(String(50), nullable=True)
    modelo_ia = Column(String(50), nullable=True)

    saludo = Column(Text, nullable=True)
    situacion_problematica = Column(Text, nullable=True)
    preguntas = Column(JSON, nullable=True)
    tabla_respuestas = Column(JSON, nullable=True)
    desempenos_usados = Column(Text, nullable=True)

    usuario = relationship("Usuario", back_populates="examenes_matematica", foreign_keys=[docente_id])
    grado = relationship("Grado")
    competencia = relationship("CompetenciaMatematica")

    def __repr__(self):
        return f"<ExamenMatematica id={self.id} docente={self.docente_id} grado={self.grado_nombre}>"


# =============================================================================
# FASE 3: SISTEMA DE EXÁMENES PARA ESTUDIANTES
# =============================================================================

class AsignacionExamen(Base):
    """Asignación de un examen generado a un grado/sección por un docente."""
    __tablename__ = "asignaciones_examen"

    id = Column(Integer, primary_key=True, index=True)
    tipo_examen = Column(String(20), nullable=False)  # "lectura" o "matematica"
    examen_lectura_id = Column(Integer, ForeignKey("examenes_lectura.id", ondelete="SET NULL"), nullable=True)
    examen_matematica_id = Column(Integer, ForeignKey("examenes_matematica.id", ondelete="SET NULL"), nullable=True)
    asignado_por_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)

    institucion_educativa_id = Column(Integer, ForeignKey("instituciones_educativas.id"), nullable=True)
    grado_id = Column(Integer, ForeignKey("grados.id"), nullable=True)
    seccion = Column(String(10), nullable=True)  # None = todas las secciones

    fecha_inicio = Column(DateTime(timezone=True), nullable=True)
    fecha_fin = Column(DateTime(timezone=True), nullable=True)
    duracion_minutos = Column(Integer, nullable=True)
    intentos_permitidos = Column(Integer, default=1)
    mostrar_resultados = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())

    asignado_por = relationship("Usuario", foreign_keys=[asignado_por_id])
    examen_lectura = relationship("ExamenLectura")
    examen_matematica = relationship("ExamenMatematica")
    institucion_educativa = relationship("InstitucionEducativa")
    grado = relationship("Grado")
    intentos = relationship("IntentoExamen", back_populates="asignacion", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<AsignacionExamen id={self.id} tipo={self.tipo_examen}>"


class IntentoExamen(Base):
    """Registro de un intento de un estudiante en un examen asignado."""
    __tablename__ = "intentos_examen"

    id = Column(Integer, primary_key=True, index=True)
    asignacion_id = Column(Integer, ForeignKey("asignaciones_examen.id"), nullable=False)
    estudiante_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)

    numero_intento = Column(Integer, nullable=False, default=1)
    estado = Column(String(20), nullable=False, default="pendiente")  # EstadoIntento enum values

    fecha_inicio = Column(DateTime(timezone=True), nullable=True)
    fecha_fin = Column(DateTime(timezone=True), nullable=True)

    respuestas = Column(JSON, nullable=True)  # {"1": "A", "2": "C", ...}
    puntaje_total = Column(Float, nullable=True)  # 0-100
    preguntas_correctas = Column(Integer, nullable=True)
    preguntas_total = Column(Integer, nullable=True)
    nivel_logro = Column(String(50), nullable=True)  # NivelLogro enum values
    resultados_por_desempeno = Column(JSON, nullable=True)  # detalle por desempeño

    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("asignacion_id", "estudiante_id", "numero_intento", name="uq_intento"),
    )

    asignacion = relationship("AsignacionExamen", back_populates="intentos")
    estudiante = relationship("Usuario", foreign_keys=[estudiante_id])

    def __repr__(self):
        return f"<IntentoExamen id={self.id} estudiante={self.estudiante_id} estado={self.estado}>"


class ProgresoEstudiante(Base):
    """Tabla agregada de progreso por estudiante y área curricular."""
    __tablename__ = "progreso_estudiante"

    id = Column(Integer, primary_key=True, index=True)
    estudiante_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    area = Column(String(20), nullable=False)  # "comunicacion" o "matematica"

    total_examenes_completados = Column(Integer, default=0)
    puntaje_promedio = Column(Float, nullable=True)
    nivel_logro_actual = Column(String(50), nullable=True)
    dominio_desempenos = Column(JSON, nullable=True)
    ultima_actividad = Column(DateTime(timezone=True), nullable=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("estudiante_id", "area", name="uq_progreso_estudiante_area"),
    )

    estudiante = relationship("Usuario", foreign_keys=[estudiante_id])

    def __repr__(self):
        return f"<ProgresoEstudiante estudiante={self.estudiante_id} area={self.area}>"
