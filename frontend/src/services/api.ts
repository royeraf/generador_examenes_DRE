import axios from 'axios';
import type {
  Grado,
  DesempenoItem,
  NivelLogro,
  GenerarPreguntasRequest,
  GenerarExamenResponse,
  Capacidad,
  Docente
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
  }): Promise<{
    grado: string;
    competencia: string;
    desempenos_usados: string;
    saludo: string;
    examen: {
      titulo: string;
      grado: string;
      competencia: string;
      instrucciones: string;
      situacion_problematica: string;
      preguntas: Array<{
        numero: number;
        enunciado: string;
        opciones: Array<{ letra: string; texto: string; es_correcta: boolean }>;
        capacidad: string;
        desempeno_codigo: string;
        criterio_evaluacion: string;
      }>;
      tabla_respuestas: Array<{
        pregunta: number;
        capacidad: string;
        desempeno: string;
        respuesta_correcta: string;
        justificacion: string;
      }>;
    };
    total_preguntas: number;
  }> {
    const response = await apiClient.post('/matsistem/generar', request);
    return response.data;
  },
};

export default desempenosService;

// =============================================================================
// ADMIN USUARIOS SERVICE
// =============================================================================

export interface DocenteCreatePayload {
  dni: string
  nombres?: string
  apellidos?: string
  profesion?: string
  institucion_educativa?: string
  nivel_educativo?: string
  is_active?: boolean
  is_superuser?: boolean
  password: string
}

export interface DocenteUpdatePayload {
  nombres?: string
  apellidos?: string
  profesion?: string
  institucion_educativa?: string
  nivel_educativo?: string
  is_active?: boolean
  is_superuser?: boolean
  password?: string
}

export const adminUsuariosService = {
  async getAll(): Promise<Docente[]> {
    const response = await apiClient.get<Docente[]>('/admin/docentes')
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

