import axios from 'axios';
import type { 
  Grado, 
  DesempenoItem, 
  NivelLogro, 
  GenerarPreguntasRequest, 
  GenerarExamenResponse,
  Capacidad
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const desempenosService = {
  /**
   * Obtiene todos los grados disponibles
   */
  async getGrados(): Promise<Grado[]> {
    const response = await apiClient.get<Grado[]>('/desempenos/grados');
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
      `/desempenos/grados/${gradoId}/desempenos`,
      { params }
    );
    return response.data;
  },

  /**
   * Obtiene los niveles de logro disponibles
   */
  async getNivelesLogro(): Promise<{ niveles: NivelLogro[] }> {
    const response = await apiClient.get<{ niveles: NivelLogro[] }>('/desempenos/niveles-logro');
    return response.data;
  },

  /**
   * Obtiene las capacidades disponibles
   */
  async getCapacidades(): Promise<Capacidad[]> {
    const response = await apiClient.get<Capacidad[]>('/desempenos/capacidades');
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
      '/desempenos/upload-texto',
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
      '/desempenos/generar',
      request
    );
    return response.data;
  },

  /**
   * Descarga el examen en formato Word
   */
  async descargarWord(examen: object, grado: string): Promise<void> {
    const response = await apiClient.post(
      '/desempenos/descargar-word',
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
      const filenameMatch = contentDisposition.match(/filename="?(.+)"?/);
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

export default desempenosService;
