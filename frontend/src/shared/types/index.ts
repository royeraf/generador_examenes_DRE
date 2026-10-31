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

export interface Matricula {
  id: number
  año_escolar: number
  grado_id: number
  grado_nombre: string | null
  seccion: string
  is_active: boolean
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
  provincia_nombre: string | null
  distrito_nombre: string | null
  ugel_nombre: string | null
  institucion_nombre: string | null
  is_active: boolean
  rol_codigo: RolCodigo | null
  creado_por_id: number | null
  creado_por_nombre?: string | null
  fecha_creacion: string | null
  ultimo_acceso: string | null
  permisos_modulos: string[] | null
  modulos_efectivos?: string[]
  matricula_activa?: Matricula | null
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
  orden: number;
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
  textos_base?: { titulo: string; texto: string }[];
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
  tipo?: 'cerrada' | 'abierta' | string;
  contexto?: string | null;
  respuesta_esperada?: string | null;
  espacio_respuesta?: string | null;
}

// Fila de la tabla de respuestas
export interface FilaTablaRespuestas {
  pregunta: number;
  desempeno: string;
  nivel: string;
  respuesta_correcta: string;
  respuesta_esperada?: string | null;
  justificacion?: string;
  retroalimentacion_correcta?: string;
  retroalimentacion_incorrecta?: string;
  tipo?: 'cerrada' | 'abierta' | string;
}

// Estructura del examen generado
export interface Examen {
  titulo: string;
  grado: string;
  instrucciones: string;
  lectura: string;
  lecturas?: { titulo: string; texto: string }[];
  preguntas: PreguntaExamen[];
  tabla_respuestas: FilaTablaRespuestas[];
  // MatSistem: tipo de producto y snapshot de la actividad (tipo 5).
  tipo_producto?: number | null;
  contenido_json?: unknown;
  situacion_problematica?: string;
}

// Respuesta completa del generador
export interface GenerarExamenResponse {
  grado: string;
  desempenos_usados: string;
  saludo: string;
  examen: Examen;
  lecturas?: { titulo: string; texto: string }[];
  total_preguntas: number;
  advertencias_calidad?: string[];
  tipo_producto?: number;
  tipo_producto_nombre?: string;
  es_actividad?: boolean;
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

// Feedback de subida de archivos (textos/problemas base en PDF/Word)
export interface ArchivoMetadata {
  filename: string;
  palabras: number;
  caracteres: number;
  size_kb?: number;
  extension?: string;
  ocr_aplicado?: boolean;
  ocr_paginas?: number;
  total_paginas?: number;
}

export interface UploadAdvertencia {
  archivo: string;
  error: string;
}

export interface FilesMetadata {
  archivos: ArchivoMetadata[];
  total_palabras: number;
  total_caracteres: number;
  advertencias?: UploadAdvertencia[];
}
