// Types para el módulo de Matemática (MatSistem)

/**
 * Competencia Matemática (4 en total según MINEDU)
 */
export interface CompetenciaMatematica {
  id: number;
  codigo: number;
  nombre: string;
  descripcion?: string;
}

/**
 * Capacidad Matemática (4 por competencia)
 */
export interface CapacidadMatematica {
  id: number;
  orden: number;
  nombre: string;
  descripcion?: string;
  competencia_id: number;
}

/**
 * Capacidad con información de la competencia
 */
export interface CapacidadMatConCompetencia extends CapacidadMatematica {
  competencia_codigo: number;
  competencia_nombre: string;
}

/**
 * Estándar de aprendizaje matemático
 */
export interface EstandarMatematica {
  id: number;
  descripcion: string;
  ciclo?: string;
  grado_id: number;
  competencia_id: number;
}

/**
 * Desempeño matemático básico
 */
export interface DesempenoMatematica {
  id: number;
  codigo: string;
  descripcion: string;
  grado_id: number;
  capacidad_id: number;
}

/**
 * Desempeño matemático con información completa
 */
export interface DesempenoMatCompleto extends DesempenoMatematica {
  capacidad_orden: number;
  capacidad_nombre: string;
  competencia_id: number;
  competencia_codigo: number;
  competencia_nombre: string;
}

/**
 * Grado para matemática (incluye inicial)
 */
export interface GradoMatematica {
  id: number;
  nombre: string;
  numero: number;
  nivel: 'inicial' | 'primaria' | 'secundaria';
  orden: number;
}

/**
 * Nivel de logro para evaluación
 */
export interface NivelLogroMatematica {
  id: string;
  nombre: string;
  descripcion: string;
  valor: number;
  color: string;
}

/**
 * Currículo completo para un grado y competencia
 */
export interface CurriculoMatematica {
  grado: GradoMatematica;
  competencia: CompetenciaMatematica;
  estandar?: EstandarMatematica;
  capacidades: CapacidadMatematica[];
  desempenos: DesempenoMatCompleto[];
}

/**
 * Item de evaluación para sistematización
 */
export interface ItemEvaluacionMat {
  id: string;
  numero: number;
  nivel_logro: string;  // preinicio, inicio, proceso, logro_esperado, logro_destacado
  desempeno_id: number;
  desempeno: DesempenoMatCompleto;
  clave_correcta?: string;  // A, B, C, D para opción múltiple
  puntaje_maximo?: number;
}

/**
 * Respuesta de estudiante en evaluación
 */
export interface RespuestaEstudianteMat {
  estudiante_id: string;
  estudiante_nombre: string;
  items: {
    item_id: string;
    respuesta: string;
    es_correcta?: boolean;
    puntaje?: number;
  }[];
  nivel_logro_alcanzado?: string;
  puntaje_total?: number;
}

/**
 * Ficha de evaluación matemática
 */
export interface FichaEvaluacionMat {
  id: string;
  titulo: string;
  grado_id: number;
  competencia_id: number;
  fecha_creacion: string;
  items: ItemEvaluacionMat[];
  respuestas: RespuestaEstudianteMat[];
}
