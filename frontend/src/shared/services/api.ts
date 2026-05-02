import axios from 'axios';
import type {
  Grado,
  DesempenoItem,
  NivelLogro,
  GenerarPreguntasRequest,
  GenerarExamenResponse,
  Capacidad,
  Docente,
  Provincia,
  Distrito
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || (import.meta.env.PROD ? '/api' : 'http://localhost:8000/api');

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 120000, // 2 minutes
});

// Add auth interceptor
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const desempenosService = {
  /**
   * Obtiene todos los grados disponibles
   */
  async getGrados(): Promise<Grado[]> {
    const response = await apiClient.get<Grado[]>('/lectosistem/grados');
    return response.data;
  },

  /**
   * Obtiene los desempeños de un grado específico
   */
  async getDesempenosPorGrado(
    gradoId: number, 
    tipoCapacidad?: string
  ): Promise<DesempenoItem[]> {
    const params = tipoCapacidad ? { tipo_capacidad: tipoCapacidad } : {};
    const response = await apiClient.get<DesempenoItem[]>(
      `/lectosistem/grados/${gradoId}/desempenos`,
      { params }
    );
    return response.data;
  },

  /**
   * Obtiene los niveles de logro disponibles
   */
  async getNivelesLogro(): Promise<{ niveles: NivelLogro[] }> {
    const response = await apiClient.get<{ niveles: NivelLogro[] }>('/lectosistem/niveles-logro');
    return response.data;
  },

  /**
   * Obtiene las capacidades disponibles
   */
  async getCapacidades(): Promise<Capacidad[]> {
    const response = await apiClient.get<Capacidad[]>('/lectosistem/capacidades');
    return response.data;
  },

  /**
   * Sube uno o más archivos PDF/Word y extrae el texto
   */
  async uploadTextoBase(files: File[]): Promise<{ 
    texto: string; 
    archivos: { filename: string; palabras: number; caracteres: number }[];
    total_archivos: number;
    total_palabras: number;
    total_caracteres: number;
  }> {
    const formData = new FormData();
    files.forEach((file) => {
      formData.append('files', file);
    });
    
    const response = await apiClient.post(
      '/lectosistem/upload-texto',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },

  /**
   * Genera un examen basado en desempeños
   */
  async generarPreguntas(request: GenerarPreguntasRequest): Promise<GenerarExamenResponse> {
    const response = await apiClient.post<GenerarExamenResponse>(
      '/lectosistem/generar',
      request
    );
    return response.data;
  },

  /**
   * Descarga el examen en formato Word
   */
  async descargarWord(examen: object, grado: string): Promise<void> {
    const response = await apiClient.post(
      '/lectosistem/descargar-word',
      { examen, grado },
      { responseType: 'blob' }
    );
    
    // Crear blob y descargar
    const blob = new Blob([response.data], { 
      type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' 
    });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    
    // Obtener nombre del archivo del header o usar default
    const contentDisposition = response.headers['content-disposition'];
    let filename = 'examen.docx';
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename="([^"]+)"/) || contentDisposition.match(/filename=([^\s;]+)/);
      if (filenameMatch) {
        filename = filenameMatch[1];
      }
    }
    
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  },
};

export const adminService = {
  // --- Grados ---
  async getGrados(): Promise<Grado[]> {
    const response = await apiClient.get<Grado[]>('/admin/grados');
    return response.data;
  },
  async createGrado(grado: any): Promise<Grado> {
    const response = await apiClient.post<Grado>('/admin/grados', grado);
    return response.data;
  },
  async updateGrado(id: number, grado: any): Promise<Grado> {
    const response = await apiClient.put<Grado>(`/admin/grados/${id}`, grado);
    return response.data;
  },
  async deleteGrado(id: number): Promise<void> {
    await apiClient.delete(`/admin/grados/${id}`);
  },

  // --- Capacidades ---
  async getCapacidades(): Promise<Capacidad[]> {
    const response = await apiClient.get<Capacidad[]>('/lectosistem/capacidades'); // Reusing existing or could use /admin if implemented there
    return response.data;
  },
  async createCapacidad(capacidad: any): Promise<Capacidad> {
    const response = await apiClient.post<Capacidad>('/admin/capacidades', capacidad);
    return response.data;
  },
  async updateCapacidad(id: number, capacidad: any): Promise<Capacidad> {
    const response = await apiClient.put<Capacidad>(`/admin/capacidades/${id}`, capacidad);
    return response.data;
  },
  async deleteCapacidad(id: number): Promise<void> {
    await apiClient.delete(`/admin/capacidades/${id}`);
  },

  // --- Desempeños ---
  async getDesempenos(gradoId: number): Promise<DesempenoItem[]> {
    // Reusing the existing filter endpoint but typically admin might want all. 
    // For now, let's filter by grado as it makes sense for UI.
    return desempenosService.getDesempenosPorGrado(gradoId);
  },
  async createDesempeno(desempeno: any): Promise<DesempenoItem> {
    const response = await apiClient.post<DesempenoItem>('/admin/desempenos', desempeno);
    return response.data;
  },
  async updateDesempeno(id: number, desempeno: any): Promise<DesempenoItem> {
    const response = await apiClient.put<DesempenoItem>(`/admin/desempenos/${id}`, desempeno);
    return response.data;
  },
  async deleteDesempeno(id: number): Promise<void> {
    await apiClient.delete(`/admin/desempenos/${id}`);
  },
};

// =============================================================================
// SERVICIO DE MATEMÁTICA (MatSistem)
// =============================================================================

import type {
  CompetenciaMatematica,
  CapacidadMatConCompetencia,
  DesempenoMatCompleto,
  GradoMatematica,
  NivelLogroMatematica,
  EstandarMatematica,
  CurriculoMatematica
} from '../types/matematica';

export const matematicaService = {
  /**
   * Obtiene todos los grados disponibles para Matemática
   */
  async getGrados(): Promise<GradoMatematica[]> {
    const response = await apiClient.get<GradoMatematica[]>('/matsistem/grados');
    return response.data;
  },

  /**
   * Obtiene las 4 competencias matemáticas
   */
  async getCompetencias(): Promise<CompetenciaMatematica[]> {
    const response = await apiClient.get<CompetenciaMatematica[]>('/matsistem/competencias');
    return response.data;
  },

  /**
   * Obtiene una competencia específica
   */
  async getCompetencia(competenciaId: number): Promise<CompetenciaMatematica> {
    const response = await apiClient.get<CompetenciaMatematica>(`/matsistem/competencias/${competenciaId}`);
    return response.data;
  },

  /**
   * Obtiene las capacidades matemáticas, opcionalmente filtradas por competencia
   */
  async getCapacidades(competenciaId?: number): Promise<CapacidadMatConCompetencia[]> {
    const params = competenciaId ? { competencia_id: competenciaId } : {};
    const response = await apiClient.get<CapacidadMatConCompetencia[]>('/matsistem/capacidades', { params });
    return response.data;
  },

  /**
   * Obtiene las capacidades de una competencia específica
   */
  async getCapacidadesPorCompetencia(competenciaId: number): Promise<CapacidadMatConCompetencia[]> {
    const response = await apiClient.get<CapacidadMatConCompetencia[]>(
      `/matsistem/competencias/${competenciaId}/capacidades`
    );
    return response.data;
  },

  /**
   * Obtiene los desempeños matemáticos con filtros opcionales
   */
  async getDesempenos(
    gradoId?: number,
    competenciaId?: number,
    capacidadId?: number
  ): Promise<DesempenoMatCompleto[]> {
    const params: Record<string, number> = {};
    if (gradoId) params.grado_id = gradoId;
    if (competenciaId) params.competencia_id = competenciaId;
    if (capacidadId) params.capacidad_id = capacidadId;
    
    const response = await apiClient.get<DesempenoMatCompleto[]>('/matsistem/desempenos', { params });
    return response.data;
  },

  /**
   * Obtiene los desempeños de un grado específico
   */
  async getDesempenosPorGrado(
    gradoId: number,
    competenciaId?: number
  ): Promise<DesempenoMatCompleto[]> {
    const params = competenciaId ? { competencia_id: competenciaId } : {};
    const response = await apiClient.get<DesempenoMatCompleto[]>(
      `/matsistem/grados/${gradoId}/desempenos`,
      { params }
    );
    return response.data;
  },

  /**
   * Obtiene los desempeños de un grado y competencia específicos
   */
  async getDesempenosPorGradoYCompetencia(
    gradoId: number,
    competenciaId: number
  ): Promise<DesempenoMatCompleto[]> {
    const response = await apiClient.get<DesempenoMatCompleto[]>(
      `/matsistem/grados/${gradoId}/competencias/${competenciaId}/desempenos`
    );
    return response.data;
  },

  /**
   * Obtiene el estándar para un grado y competencia
   */
  async getEstandar(gradoId: number, competenciaId: number): Promise<EstandarMatematica | null> {
    const response = await apiClient.get<EstandarMatematica | null>(
      `/matsistem/grados/${gradoId}/competencias/${competenciaId}/estandar`
    );
    return response.data;
  },

  /**
   * Obtiene el currículo completo para un grado y competencia
   */
  async getCurriculo(gradoId: number, competenciaId: number): Promise<CurriculoMatematica> {
    const response = await apiClient.get<CurriculoMatematica>(
      `/matsistem/grados/${gradoId}/competencias/${competenciaId}/curriculo`
    );
    return response.data;
  },

  /**
   * Crea un nuevo desempeño matemático
   */
  async createDesempeno(data: { codigo: string; descripcion: string; grado_id: number; capacidad_id: number }) {
    const response = await apiClient.post('/matsistem/desempenos', data);
    return response.data;
  },

  /**
   * Actualiza un desempeño matemático
   */
  async updateDesempeno(id: number, data: Partial<{ codigo: string; descripcion: string; grado_id: number; capacidad_id: number }>) {
    const response = await apiClient.put(`/matsistem/desempenos/${id}`, data);
    return response.data;
  },

  /**
   * Elimina un desempeño matemático
   */
  async deleteDesempeno(id: number) {
    const response = await apiClient.delete(`/matsistem/desempenos/${id}`);
    return response.data;
  },

  /**
   * Obtiene los niveles de logro para evaluación
   */
  async getNivelesLogro(): Promise<{ niveles: NivelLogroMatematica[] }> {
    const response = await apiClient.get<{ niveles: NivelLogroMatematica[] }>('/matsistem/niveles-logro');
    return response.data;
  },

  /**
   * Genera un examen de matemática con situación problemática
   */
  async generarExamen(request: {
    grado_id: number;
    competencia_id: number;
    desempeno_ids: number[];
    cantidad: number;
    situacion_base?: string;
    modelo?: string;
    nivel_dificultad?: 'basico' | 'intermedio' | 'avanzado';
    contenido_tematico?: string;
    tipo_producto?: number;
  }): Promise<any> {
    const response = await apiClient.post('/matsistem/generar', request);
    return response.data;
  },
};

export default desempenosService;

// =============================================================================
// SERVICIO DE UBIGEO (Provincias y Distritos)
// =============================================================================

export const ubigeoService = {
  async getProvincias(): Promise<Provincia[]> {
    const response = await apiClient.get<Provincia[]>('/ubigeo/provincias')
    return response.data
  },

  async getDistritos(provinciaId: number): Promise<Distrito[]> {
    const response = await apiClient.get<Distrito[]>(`/ubigeo/provincias/${provinciaId}/distritos`)
    return response.data
  },
}

// =============================================================================
// ADMIN USUARIOS SERVICE
// =============================================================================

export interface DocenteCreatePayload {
  dni?: string | null
  nombres?: string
  apellidos?: string
  profesion?: string
  rol_codigo: string
  ugel_id?: number | null
  institucion_educativa_id?: number | null
  provincia_id?: number | null
  distrito_id?: number | null
  is_active?: boolean
  password: string
  permisos_modulos?: string[] | null
}

export interface DocenteUpdatePayload {
  nombres?: string
  apellidos?: string
  profesion?: string
  rol_codigo?: string
  ugel_id?: number | null
  institucion_educativa_id?: number | null
  provincia_id?: number | null
  distrito_id?: number | null
  is_active?: boolean
  password?: string
  permisos_modulos?: string[] | null
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}

// =============================================================================
// ROLES CONFIG SERVICE
// =============================================================================

export interface RolConfig {
  id: number
  codigo: string
  nombre: string
  descripcion: string | null
  nivel: number
  orden: number
  modulos_default: string[] | null
  modulos_efectivos: string[]
}

export const rolesConfigService = {
  async getAll(): Promise<RolConfig[]> {
    const response = await apiClient.get<RolConfig[]>('/admin/roles-config')
    return response.data
  },
  async update(rolCodigo: string, modulosDefault: string[] | null): Promise<RolConfig> {
    const response = await apiClient.put<RolConfig>(`/admin/roles-config/${rolCodigo}`, {
      modulos_default: modulosDefault,
    })
    return response.data
  },
}

export const adminUsuariosService = {
  async getAll(page: number = 1, size: number = 10, search?: string): Promise<PaginatedResponse<Docente>> {
    const params: Record<string, any> = { page, size }
    if (search) {
      params.q = search;
    }
    const response = await apiClient.get<PaginatedResponse<Docente>>('/admin/docentes', { params })
    return response.data
  },

  async create(data: DocenteCreatePayload): Promise<Docente> {
    const response = await apiClient.post<Docente>('/admin/docentes', data)
    return response.data
  },

  async update(id: number, data: DocenteUpdatePayload): Promise<Docente> {
    const response = await apiClient.put<Docente>(`/admin/docentes/${id}`, data)
    return response.data
  },

  async delete(id: number): Promise<void> {
    await apiClient.delete(`/admin/docentes/${id}`)
  },

  async toggleActive(id: number): Promise<Docente> {
    const response = await apiClient.patch<Docente>(`/admin/docentes/${id}/toggle-active`)
    return response.data
  },
}

// =============================================================================
// SERVICIO DE EXÁMENES GUARDADOS
// =============================================================================

export const examenesService = {
  // --- Lectura ---
  async saveExamenLectura(data: any): Promise<any> {
    const response = await apiClient.post('/examenes/lectura', data);
    return response.data;
  },
  async getExamenesLectura(): Promise<any[]> {
    const response = await apiClient.get('/examenes/lectura');
    return response.data;
  },
  async getExamenLectura(id: number): Promise<any> {
    const response = await apiClient.get(`/examenes/lectura/${id}`);
    return response.data;
  },
  async deleteExamenLectura(id: number): Promise<void> {
    await apiClient.delete(`/examenes/lectura/${id}`);
  },

  // --- Matemática ---
  async saveExamenMatematica(data: any): Promise<any> {
    const response = await apiClient.post('/examenes/matematica', data);
    return response.data;
  },
  async getExamenesMatematica(): Promise<any[]> {
    const response = await apiClient.get('/examenes/matematica');
    return response.data;
  },
  async getExamenMatematica(id: number): Promise<any> {
    const response = await apiClient.get(`/examenes/matematica/${id}`);
    return response.data;
  },
  async deleteExamenMatematica(id: number): Promise<void> {
    await apiClient.delete(`/examenes/matematica/${id}`);
  },
};

// =============================================================================
// SERVICIO DE ORGANIZACIÓN (UGELes e IEs)
// =============================================================================

import type { Ugel, InstitucionEducativa, Grado as GradoType } from '../types'

export interface UgelCreatePayload {
  codigo: string
  nombre: string
  provincia_id?: number | null
  is_active?: boolean
}

export interface IECreatePayload {
  codigo_modular: string
  nombre: string
  nivel_educativo: string[]
  direccion?: string | null
  ugel_id: number
  distrito_id?: number | null
  is_active?: boolean
}

export const organizacionService = {
  async getUgeles(soloActivas = false): Promise<Ugel[]> {
    const response = await apiClient.get<Ugel[]>('/organizacion/ugeles', {
      params: { solo_activas: soloActivas },
    })
    return response.data
  },
  async createUgel(data: UgelCreatePayload): Promise<Ugel> {
    const response = await apiClient.post<Ugel>('/organizacion/ugeles', data)
    return response.data
  },
  async updateUgel(id: number, data: Partial<UgelCreatePayload>): Promise<Ugel> {
    const response = await apiClient.put<Ugel>(`/organizacion/ugeles/${id}`, data)
    return response.data
  },
  async deleteUgel(id: number): Promise<void> {
    await apiClient.delete(`/organizacion/ugeles/${id}`)
  },

  async getInstituciones(ugelId?: number, soloActivas = false): Promise<InstitucionEducativa[]> {
    const response = await apiClient.get<InstitucionEducativa[]>('/organizacion/instituciones', {
      params: { ugel_id: ugelId, solo_activas: soloActivas },
    })
    return response.data
  },
  async getInstitucion(id: number): Promise<InstitucionEducativa> {
    const response = await apiClient.get<InstitucionEducativa>(`/organizacion/instituciones/${id}`)
    return response.data
  },
  async createInstitucion(data: IECreatePayload): Promise<InstitucionEducativa> {
    const response = await apiClient.post<InstitucionEducativa>('/organizacion/instituciones', data)
    return response.data
  },
  async updateInstitucion(id: number, data: Partial<IECreatePayload>): Promise<InstitucionEducativa> {
    const response = await apiClient.put<InstitucionEducativa>(`/organizacion/instituciones/${id}`, data)
    return response.data
  },
  async deleteInstitucion(id: number): Promise<void> {
    await apiClient.delete(`/organizacion/instituciones/${id}`)
  },

  async getMiUgel(): Promise<Ugel> {
    const response = await apiClient.get<Ugel>('/organizacion/mi-ugel')
    return response.data
  },
  async getMiInstitucion(): Promise<InstitucionEducativa> {
    const response = await apiClient.get<InstitucionEducativa>('/organizacion/mi-institucion')
    return response.data
  },
  async getGrados(): Promise<GradoType[]> {
    const response = await apiClient.get<GradoType[]>('/organizacion/grados')
    return response.data
  },
  async getIEAnalytics(ieId: number): Promise<{
    total_estudiantes: number
    total_docentes: number
    total_examenes_lectura: number
    total_examenes_matematica: number
    total_examenes: number
    total_asignaciones: number
    total_completados: number
    recientes: Array<{ id: number; titulo: string; grado: string; area: string; fecha: string | null; docente: string }>
  }> {
    const response = await apiClient.get(`/organizacion/instituciones/${ieId}/analytics`)
    return response.data
  },
}

// =============================================================================
// SERVICIO DE REGISTRO Y CÓDIGOS DE CLASE
// =============================================================================

export interface CodigoClase {
  id: number
  codigo: string
  grado_id: number
  grado_nombre: string | null
  seccion: string
  max_estudiantes: number
  is_active: boolean
  fecha_creacion: string | null
  fecha_expiracion: string | null
  institucion_nombre: string | null
  total_estudiantes: number
}

export interface CodigoClaseCreatePayload {
  grado_id: number
  seccion: string
  max_estudiantes?: number
  fecha_expiracion?: string | null
}

export interface RegistroEstudiantePayload {
  codigo_clase: string
  nombres: string
  apellidos: string
  dni?: string | null
  password: string
}

export const codigosClaseService = {
  async getAll(): Promise<CodigoClase[]> {
    const response = await apiClient.get<CodigoClase[]>('/codigos-clase')
    return response.data
  },
  async create(data: CodigoClaseCreatePayload): Promise<CodigoClase> {
    const response = await apiClient.post<CodigoClase>('/codigos-clase', data)
    return response.data
  },
  async toggle(id: number): Promise<{ id: number; is_active: boolean }> {
    const response = await apiClient.put(`/codigos-clase/${id}/toggle`)
    return response.data
  },
  async delete(id: number): Promise<void> {
    await apiClient.delete(`/codigos-clase/${id}`)
  },
}

export const registroService = {
  async registrarEstudiante(data: RegistroEstudiantePayload) {
    const response = await apiClient.post('/registro/estudiante', data)
    return response.data
  },
  async validarCodigo(codigo: string) {
    const response = await apiClient.get(`/registro/validar-codigo/${codigo}`)
    return response.data
  },
}


// =============================================================================
// SERVICIO DE ASIGNACIONES DE EXÁMENES
// =============================================================================

export interface AsignacionPayload {
  tipo_examen: 'lectura' | 'matematica'
  examen_id: number
  grado_id: number
  seccion?: string | null
  fecha_inicio?: string | null
  fecha_fin?: string | null
  duracion_minutos?: number | null
  intentos_permitidos?: number
  mezclar_preguntas?: boolean
  mezclar_alternativas?: boolean
}

export interface Asignacion {
  id: number
  tipo_examen: string
  grado_id: number
  seccion: string | null
  fecha_inicio: string | null
  fecha_fin: string | null
  duracion_minutos: number | null
  intentos_permitidos: number
  mezclar_preguntas?: boolean
  mezclar_alternativas?: boolean
  is_active: boolean
  fecha_creacion: string
}

export interface UpdateAsignacionPayload {
  fecha_inicio: string | null
  fecha_fin: string | null
  duracion_minutos: number | null
  intentos_permitidos: number
  mezclar_preguntas: boolean
  mezclar_alternativas: boolean
  is_active: boolean
}

export const asignacionesService = {
  async asignar(data: AsignacionPayload): Promise<Asignacion> {
    const response = await apiClient.post<Asignacion>('/examenes/asignar', data)
    return response.data
  },
  async getAsignaciones(): Promise<Asignacion[]> {
    const response = await apiClient.get<Asignacion[]>('/examenes/asignaciones')
    return response.data
  },
  async getResultados(id: number) {
    const response = await apiClient.get(`/examenes/asignaciones/${id}/resultados`)
    return response.data
  },
  async updateAsignacion(id: number, data: UpdateAsignacionPayload): Promise<void> {
    await apiClient.put(`/examenes/asignaciones/${id}`, data)
  },
  async deleteAsignacion(id: number): Promise<void> {
    await apiClient.delete(`/examenes/asignaciones/${id}`)
  },
}

// =============================================================================
// SERVICIO DE GESTIÓN DE ESTUDIANTES POR DOCENTE
// =============================================================================

export interface EstudianteDocente {
  id: number
  codigo_estudiante: string | null
  nombres: string | null
  apellidos: string | null
  dni: string | null
  grado_id: number | null
  grado_nombre: string | null
  seccion: string | null
  is_active: boolean
  fecha_creacion: string | null
}

export interface RegistrarEstudianteDirectoPayload {
  nombres: string
  apellidos: string
  dni?: string | null
  password: string
  grado_id: number
  seccion: string
}

export interface ImportarEstudianteFilaPayload {
  dni: string
  nombres: string
  apellidos: string
}

export interface ImportarEstudiantesPayload {
  grado_id: number
  seccion: string
  estudiantes: ImportarEstudianteFilaPayload[]
}

export interface RegistroEstudianteDirectoResponse {
  id: number
  codigo_estudiante: string
  nombres: string | null
  apellidos: string | null
  grado: string | null
  seccion: string | null
  institucion: string | null
}

export interface ImportarEstudiantesResponse {
  creados: number
  pendientes_generacion_usuario: number
}

export const docenteEstudiantesService = {
  async getMisEstudiantes(params?: { grado_id?: number; seccion?: string; q?: string }): Promise<EstudianteDocente[]> {
    const response = await apiClient.get<EstudianteDocente[]>('/docente/mis-estudiantes', { params })
    return response.data
  },

  async registrar(data: RegistrarEstudianteDirectoPayload): Promise<RegistroEstudianteDirectoResponse> {
    const response = await apiClient.post<RegistroEstudianteDirectoResponse>('/docente/registrar-estudiante', data)
    return response.data
  },

  async importarNomina(data: ImportarEstudiantesPayload): Promise<ImportarEstudiantesResponse> {
    const response = await apiClient.post<ImportarEstudiantesResponse>('/docente/importar-estudiantes', data)
    return response.data
  },

  async actualizar(id: number, data: RegistrarEstudianteDirectoPayload): Promise<EstudianteDocente> {
    const response = await apiClient.put<EstudianteDocente>(`/docente/mis-estudiantes/${id}`, data)
    return response.data
  },

  async eliminar(id: number): Promise<void> {
    await apiClient.delete(`/docente/mis-estudiantes/${id}`)
  },
}
