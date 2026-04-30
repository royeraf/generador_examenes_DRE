// Types for desempeños-based question generation

export type RolCodigo =
  | 'especialista_dre_comunicacion'
  | 'especialista_dre_matematica'
  | 'responsable_ugel'
  | 'director'
  | 'auxiliar'
  | 'docente'
  | 'estudiante'

export type NivelLogroCode = 'pre_inicio' | 'inicio' | 'proceso' | 'satisfactorio' | 'destacado'

export interface Rol {
  id: number
  codigo: RolCodigo
  nombre: string
  nivel: number
}

export interface Ugel {
  id: number
  codigo: string
  nombre: string
  provincia_id: number | null
  provincia_nombre?: string | null
  is_active: boolean
  fecha_creacion?: string | null
}

export interface InstitucionEducativa {
  id: number
  codigo_modular: string
  nombre: string
  nivel_educativo: string[]
  direccion?: string | null
  ugel_id: number
  ugel_nombre?: string | null
  distrito_id: number | null
  distrito_nombre?: string | null
  is_active: boolean
  fecha_creacion?: string | null
}

export interface Usuario {
  id: number
  dni: string | null
  codigo_estudiante: string | null
  nombres: string | null
  apellidos: string | null
  profesion: string | null
  email: string | null
  telefono: string | null
  provincia_id: number | null
  distrito_id: number | null
  ugel_id: number | null
  institucion_educativa_id: number | null
  grado_id: number | null
  seccion: string | null
  provincia_nombre: string | null
  distrito_nombre: string | null
  ugel_nombre: string | null
  institucion_nombre: string | null
  grado_nombre: string | null
  is_active: boolean
  rol_codigo: RolCodigo | null
  creado_por_id: number | null
  fecha_creacion: string | null
  ultimo_acceso: string | null
  permisos_modulos: string[] | null
  modulos_efectivos?: string[]
}

// Alias de compatibilidad
export type Docente = Usuario

export interface Provincia {
  id: number
  nombre: string
}

export interface Distrito {
  id: number
  nombre: string
  provincia_id: number
}

export interface Grado {
  id: number;
  nombre: string;
  numero: number;
  nivel: string;
}

export interface Capacidad {
  id: number;
  nombre: string;
  tipo: 'literal' | 'inferencial' | 'critico';
  descripcion?: string;
}

export interface DesempenoItem {
  id: number;
  codigo: string;
  descripcion: string;
  capacidad_tipo: string;
  capacidad_nombre?: string;
}

export interface NivelLogro {
  id: string;
  nombre: string;
  descripcion: string;
  recomendacion: string;
}

export interface GenerarPreguntasRequest {
  grado_id: number;
  nivel_logro: string;
  nivel_dificultad: 'basico' | 'intermedio' | 'avanzado';
  cantidad: number;
  texto_base?: string;
  desempeno_ids?: number[];
  tipo_textual?: string;
  formato_textual?: string;
  cantidad_literal?: number;
  cantidad_inferencial?: number;
  cantidad_critico?: number;
}

// Nueva estructura para opciones de pregunta
export interface OpcionPregunta {
  letra: string;
  texto: string;
  es_correcta: boolean;
}

// Nueva estructura para pregunta del examen
export interface PreguntaExamen {
  numero: number;
  enunciado: string;
  opciones: OpcionPregunta[];
  desempeno_codigo: string;
  nivel: string; // En comunicación: LITERAL/INFERENCIAL/CRITICO, en matemática: nombre de capacidad
}

// Fila de la tabla de respuestas
export interface FilaTablaRespuestas {
  pregunta: number;
  desempeno: string;
  nivel: string;
  respuesta_correcta: string;
  justificacion?: string;
}

// Estructura del examen generado
export interface Examen {
  titulo: string;
  grado: string;
  instrucciones: string;
  lectura: string;
  preguntas: PreguntaExamen[];
  tabla_respuestas: FilaTablaRespuestas[];
}

// Respuesta completa del generador
export interface GenerarExamenResponse {
  grado: string;
  desempenos_usados: string;
  saludo: string;
  examen: Examen;
  total_preguntas: number;
}

// Mantener compatibilidad con estructura anterior (deprecada)
export interface PreguntaGenerada {
  enunciado: string;
  tipo: 'multiple' | 'verdadero_falso' | 'desarrollo';
  opciones?: { texto: string; es_correcta: boolean }[];
  respuesta_correcta?: string;
  explicacion?: string;
  desempeno_evaluado?: string;
}

export interface GenerarPreguntasResponse {
  grado: string;
  nivel_logro: string;
  desempeno_base: string;
  capacidad: string;
  preguntas: PreguntaGenerada[];
  total: number;
}

// Exam History Types
export interface ExamenHistoryEntry {
  id: string;
  fechaCreacion: string;
  gradoLabel: string;
  gradoId: number | null;
  resultado: GenerarExamenResponse;
}

// Sistematizador Types
export interface PreguntaConfig {
  descripcion: string;
  desempenoId: number | null;
  clave: string;
}

export interface NivelConfig {
  nombre: string;
  descripcion: string;
  preguntas: PreguntaConfig[];
  color: string;
  bg: string;
  key: string;
}

export interface Estudiante {
  nombre: string;
  respuestas: Record<string, string[]>;
  puntajes?: Record<string, { correctas: number, total: number, porcentaje: number }>;
  nivelFinal?: string | null;
}

export interface Stats {
  total: number;
  'pre-inicio': number;
  'inicio': number;
  'proceso': number;
  'satisfactorio': number;
  'destacado': number;
}
