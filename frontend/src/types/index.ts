// Types for desempeños-based question generation

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
