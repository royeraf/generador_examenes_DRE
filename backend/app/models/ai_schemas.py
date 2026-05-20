"""
Pydantic schemas para las respuestas estructuradas de la IA (Gemini structured output).
Estos schemas garantizan que la IA devuelva JSON válido con la estructura exacta esperada.
"""
from pydantic import BaseModel
from typing import List, Optional


# ---------------------------------------------------------------------------
# Compartidos
# ---------------------------------------------------------------------------

class CriterioEvaluacion(BaseModel):
    criterio: int
    capacidad: str
    descripcion: str


# ---------------------------------------------------------------------------
# Preguntas genéricas (generar_preguntas en gemini_service / preguntas.py)
# ---------------------------------------------------------------------------

class OpcionGeneral(BaseModel):
    texto: str
    es_correcta: bool


class PreguntaGeneral(BaseModel):
    enunciado: str
    tipo: str
    opciones: List[OpcionGeneral]
    respuesta_correcta: str
    explicacion: str
    dificultad: str
    competencia_asociada: str


class RespuestaPreguntas(BaseModel):
    preguntas: List[PreguntaGeneral]


# ---------------------------------------------------------------------------
# LectoSistem
# ---------------------------------------------------------------------------

class OpcionLecto(BaseModel):
    letra: str
    texto: str
    es_correcta: bool


class PreguntaLecto(BaseModel):
    numero: int
    enunciado: str
    opciones: List[OpcionLecto]
    desempeno_codigo: str
    nivel: str  # LITERAL | INFERENCIAL | CRITICO


class TablaRespuestaLecto(BaseModel):
    pregunta: int
    desempeno: str
    nivel: str
    respuesta_correcta: str
    justificacion: str
    retroalimentacion_correcta: str   # 2-3 oraciones motivadoras para quien acierta
    retroalimentacion_incorrecta: str # 2-3 oraciones explicativas para quien falla


class ExamenLecto(BaseModel):
    titulo: str
    grado: str
    instrucciones: str
    lectura: str
    preguntas: List[PreguntaLecto]
    tabla_respuestas: List[TablaRespuestaLecto]


class RespuestaLecto(BaseModel):
    saludo: str
    examen: ExamenLecto


# ---------------------------------------------------------------------------
# MatSistem — tipos de producto 1 a 4
# ---------------------------------------------------------------------------

class OpcionMat(BaseModel):
    letra: str
    texto: str
    es_correcta: Optional[bool] = None


class PreguntaMat(BaseModel):
    numero: int
    contexto: Optional[str] = None          # tipos 3, 4 (preguntas independientes)
    enunciado: str
    tipo: str                               # "abierta" | "cerrada"
    opciones: Optional[List[OpcionMat]] = None          # tipos 2, 3
    espacio_respuesta: Optional[str] = None             # tipos 1, 4
    capacidad: str
    desempeno_codigo: str
    criterio_evaluacion: str


class TablaRespuestaMat(BaseModel):
    pregunta: int
    capacidad: str
    desempeno: str
    respuesta_correcta: Optional[str] = None   # preguntas cerradas
    respuesta_esperada: Optional[str] = None   # preguntas abiertas
    justificacion: str
    retroalimentacion_correcta: str   # 2-3 oraciones motivadoras para quien acierta
    retroalimentacion_incorrecta: str # 2-3 oraciones explicativas para quien falla


class ExamenMat(BaseModel):
    titulo: str
    grado: str
    competencia: str
    instrucciones: str
    situacion_problematica: Optional[str] = None   # tipos 1, 2
    criterios_evaluacion: List[CriterioEvaluacion]
    preguntas: List[PreguntaMat]
    tabla_respuestas: List[TablaRespuestaMat]


class RespuestaMat(BaseModel):
    saludo: str
    examen: ExamenMat


# ---------------------------------------------------------------------------
# MatSistem — tipo de producto 5 (Actividad de Aprendizaje)
# ---------------------------------------------------------------------------

class InicioActividad(BaseModel):
    tipo: str
    descripcion: str


class DesarrolloActividad(BaseModel):
    capacidad: str
    descripcion: str
    materiales: Optional[List[str]] = None
    preguntas_guia: Optional[List[str]] = None


class CierreActividad(BaseModel):
    tipo: str
    descripcion: Optional[str] = None
    preguntas: Optional[List[str]] = None


class MomentoInicio(BaseModel):
    duracion: str
    actividades: List[InicioActividad]


class MomentoDesarrollo(BaseModel):
    duracion: str
    actividades: List[DesarrolloActividad]


class MomentoCierre(BaseModel):
    duracion: str
    actividades: List[CierreActividad]


class ActividadAprendizaje(BaseModel):
    titulo: str
    grado: str
    competencia: str
    duracion: str
    proposito: str
    criterios_evaluacion: List[CriterioEvaluacion]
    inicio: MomentoInicio
    desarrollo: MomentoDesarrollo
    cierre: MomentoCierre


class RespuestaActividad(BaseModel):
    saludo: str
    actividad: ActividadAprendizaje
