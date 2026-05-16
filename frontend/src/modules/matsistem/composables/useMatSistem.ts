import { ref, shallowRef, watch, computed } from 'vue';
import type { Examen } from '../../../shared/types';
import type {
  GradoMatematica,
  CompetenciaMatematica,
  CapacidadMatConCompetencia,
  DesempenoMatCompleto,
  NivelLogroMatematica
} from '../../../shared/types/matematica';
import desempenosService, { matematicaService } from '../../../shared/services/api';
import { NIVELES_DIFICULTAD } from '../../../shared/constants/niveles';
import { useBaseExam } from '../../../shared/composables/useBaseExam';
export type { NivelDificultad } from '../../../shared/constants/niveles';
export type { NivelDificultadOption } from '../../../shared/constants/niveles';

export interface TipoProductoOption {
  id: number;
  nombre: string;
  descripcion: string;
  icono: string;
}

export { NIVELES_DIFICULTAD };

export const TIPOS_PRODUCTO: TipoProductoOption[] = [
  { id: 1, nombre: 'Situación + Preguntas Abiertas', descripcion: 'Situación integradora con 4 preguntas abiertas', icono: 'PenLine' },
  { id: 2, nombre: 'Situación + Alternativas (5)', descripcion: 'Situación integradora con 4 preguntas de 5 alternativas', icono: 'ListChecks' },
  { id: 3, nombre: 'Cerradas Independientes', descripcion: '4 preguntas cerradas independientes por criterio', icono: 'CheckSquare' },
  { id: 4, nombre: 'Abiertas Independientes', descripcion: '4 preguntas abiertas independientes por criterio', icono: 'FileText' },
  { id: 5, nombre: 'Actividad de Aprendizaje', descripcion: 'Sesión completa INICIO/DESARROLLO/CIERRE', icono: 'BookOpen' }
];

export function useMatSistem() {
  const {
    selectedGradoId,
    selectedDesempenoIds,
    selectedNivelDificultad,
    cantidadPreguntas,
    loading,
    loadingDesempenos,
    loadingGrados,
    descargandoWord,
    error,
    showResults,
    activeTab,
    selectedDesempenosCount,
    makeDescargarWord,
  } = useBaseExam();

  // State - Matemática
  const grados = ref<GradoMatematica[]>([]);
  const competencias = ref<CompetenciaMatematica[]>([]);
  const capacidades = ref<CapacidadMatConCompetencia[]>([]);
  const desempenos = ref<DesempenoMatCompleto[]>([]);
  const nivelesLogro = ref<NivelLogroMatematica[]>([]);

  const selectedCompetenciaId = shallowRef<number | null>(null);
  const textoBase = shallowRef('');
  const useTextoBase = shallowRef(false);
  const contenidoTematico = shallowRef('');
  const tipoProducto = shallowRef(2);
  const selectedFiles = ref<File[]>([]);
  const filesMetadata = ref<{ archivos: { filename: string; palabras: number; caracteres: number }[]; total_palabras: number; total_caracteres: number } | null>(null);
  const uploadingFile = shallowRef(false);
  const uploadError = shallowRef<string | null>(null);

  const resultado = ref<{
    grado: string;
    desempenos_usados: string;
    saludo: string;
    examen: Examen;
    total_preguntas: number;
  } | null>(null);
  const activeCapacidadTab = shallowRef<number>(1);

  // Computed - Desempeños agrupados por capacidad (orden 1-4)
  const desempenosPorCapacidad = computed(() => {
    const grupos: Record<number, DesempenoMatCompleto[]> = {
      1: [],
      2: [],
      3: [],
      4: []
    };
    desempenos.value.forEach(d => {
      if (grupos[d.capacidad_orden]) {
        grupos[d.capacidad_orden]!.push(d);
      }
    });
    return grupos;
  });

  const gradosPorNivel = computed(() => {
    return {
      inicial: grados.value.filter(g => g.nivel === 'inicial'),
      primaria: grados.value.filter(g => g.nivel === 'primaria'),
      secundaria: grados.value.filter(g => g.nivel === 'secundaria')
    };
  });

  const gradoOptions = computed(() => {
    const options: { id: number; label: string; group: string }[] = [];
    gradosPorNivel.value.inicial.forEach(g => {
      options.push({ id: g.id, label: 'Inicial 5 años', group: 'Inicial' });
    });
    gradosPorNivel.value.primaria.forEach(g => {
      options.push({ id: g.id, label: `${g.numero}° Primaria`, group: 'Primaria' });
    });
    gradosPorNivel.value.secundaria.forEach(g => {
      options.push({ id: g.id, label: `${g.numero}° Secundaria`, group: 'Secundaria' });
    });
    return options;
  });

  const competenciaOptions = computed(() => {
    return competencias.value.map(c => ({
      id: c.id,
      label: c.nombre,
      group: `Competencia ${c.codigo}`
    }));
  });

  const capacidadesActuales = computed(() => {
    if (!selectedCompetenciaId.value) return [];
    return capacidades.value.filter(c => c.competencia_id === selectedCompetenciaId.value);
  });

  // Watch - Cargar desempeños cuando cambian grado o competencia
  watch([selectedGradoId, selectedCompetenciaId], async ([newGradoId, newCompetenciaId]) => {
    if (!newGradoId || !newCompetenciaId) {
      desempenos.value = [];
      selectedDesempenoIds.value = [];
      return;
    }
    loadingDesempenos.value = true;
    try {
      const data = await matematicaService.getDesempenosPorGradoYCompetencia(newGradoId, newCompetenciaId);
      desempenos.value = data;
      selectedDesempenoIds.value = [];
      const tabWithData = [1, 2, 3, 4].find(orden => data.some(d => d.capacidad_orden === orden));
      activeCapacidadTab.value = tabWithData || 1;
    } catch (e) {
      console.error('Error loading desempeños:', e);
    } finally {
      loadingDesempenos.value = false;
    }
  });

  const loadInitialData = async () => {
    try {
      loadingGrados.value = true;
      const [gradosData, competenciasData, capacidadesData, nivelesData] = await Promise.all([
        matematicaService.getGrados(),
        matematicaService.getCompetencias(),
        matematicaService.getCapacidades(),
        matematicaService.getNivelesLogro()
      ]);

      grados.value = gradosData;
      competencias.value = competenciasData;
      capacidades.value = capacidadesData;
      nivelesLogro.value = nivelesData.niveles;

      if (gradosData.length > 0 && !selectedGradoId.value) {
        const firstSecundaria = gradosData.find(g => g.nivel === 'secundaria');
        selectedGradoId.value = firstSecundaria?.id ?? gradosData[0]?.id ?? null;
      }
      if (competenciasData.length > 0 && !selectedCompetenciaId.value) {
        selectedCompetenciaId.value = competenciasData[0]?.id ?? null;
      }
    } catch (e) {
      console.error('Error loading data:', e);
      error.value = 'Error al cargar los datos iniciales';
    } finally {
      loadingGrados.value = false;
    }
  };

  const selectAllCapacidad = (orden: number) => {
    const ids = desempenosPorCapacidad.value[orden]?.map(d => d.id) || [];
    ids.forEach(id => {
      if (!selectedDesempenoIds.value.includes(id)) {
        selectedDesempenoIds.value.push(id);
      }
    });
  };

  const deselectAllCapacidad = (orden: number) => {
    const ids = desempenosPorCapacidad.value[orden]?.map(d => d.id) || [];
    selectedDesempenoIds.value = selectedDesempenoIds.value.filter(id => !ids.includes(id));
  };

  const deselectAll = () => {
    selectedDesempenoIds.value = [];
  };

  const handleFileUpload = async (event: Event) => {
    const input = event.target as HTMLInputElement;
    const files = input.files;
    if (!files || files.length === 0) {
      selectedFiles.value = [];
      filesMetadata.value = null;
      textoBase.value = '';
      return;
    }
    const fileArray: File[] = Array.from(files);
    for (const file of fileArray) {
      const extension = file.name.split('.').pop()?.toLowerCase();
      if (!['pdf', 'docx', 'doc'].includes(extension || '')) {
        uploadError.value = `Archivo "${file.name}" no soportado. Solo PDF o Word.`;
        input.value = '';
        selectedFiles.value = [];
        return;
      }
    }
    selectedFiles.value = fileArray;
    uploadingFile.value = true;
    uploadError.value = null;
    try {
      const result = await desempenosService.uploadTextoBase(fileArray);
      textoBase.value = result.texto;
      filesMetadata.value = {
        archivos: result.archivos,
        total_palabras: result.total_palabras,
        total_caracteres: result.total_caracteres
      };
    } catch (e: any) {
      uploadError.value = e.response?.data?.detail || 'Error al procesar los archivos';
      selectedFiles.value = [];
      textoBase.value = '';
      input.value = '';
    } finally {
      uploadingFile.value = false;
    }
  };

  const clearFiles = () => {
    selectedFiles.value = [];
    filesMetadata.value = null;
    textoBase.value = '';
    uploadError.value = null;
  };

  const generarPreguntas = async () => {
    if (!selectedGradoId.value) {
      error.value = 'Por favor, selecciona un grado';
      return;
    }
    if (!selectedCompetenciaId.value) {
      error.value = 'Por favor, selecciona una competencia';
      return;
    }
    if (selectedDesempenoIds.value.length === 0) {
      error.value = 'Por favor, selecciona al menos un desempeño';
      return;
    }
    loading.value = true;
    error.value = null;
    resultado.value = null;
    showResults.value = true;
    try {
      const response = await matematicaService.generarExamen({
        grado_id: selectedGradoId.value,
        competencia_id: selectedCompetenciaId.value,
        desempeno_ids: selectedDesempenoIds.value,
        cantidad: cantidadPreguntas.value,
        situacion_base: useTextoBase.value ? textoBase.value : undefined,
        modelo: 'gemini',
        nivel_dificultad: selectedNivelDificultad.value,
        contenido_tematico: contenidoTematico.value || undefined,
        tipo_producto: tipoProducto.value
      });

      resultado.value = {
        grado: response.grado,
        desempenos_usados: response.desempenos_usados,
        saludo: response.saludo,
        examen: {
          titulo: response.examen?.titulo ?? '',
          grado: response.examen?.grado ?? '',
          instrucciones: response.examen?.instrucciones ?? '',
          lectura: response.examen?.situacion_problematica ?? '',
          preguntas: (response.examen?.preguntas ?? []).map((p: any) => ({
            numero: p.numero,
            enunciado: p.enunciado,
            opciones: p.opciones,
            desempeno_codigo: p.desempeno_codigo,
            nivel: p.capacidad
          })),
          tabla_respuestas: (response.examen?.tabla_respuestas ?? []).map((t: any) => ({
            pregunta: t.pregunta,
            desempeno: t.desempeno,
            nivel: t.capacidad,
            respuesta_correcta: t.respuesta_correcta,
            justificacion: t.justificacion
          }))
        },
        total_preguntas: response.total_preguntas ?? 0
      };
    } catch (e: any) {
      error.value = e.response?.data?.detail || 'Error al generar el examen de matemática';
      console.error('Error:', e);
    } finally {
      loading.value = false;
    }
  };

  const descargarExamenWord = makeDescargarWord(resultado);

  return {
    grados,
    competencias,
    capacidades,
    desempenos,
    nivelesLogro,
    selectedGradoId,
    selectedCompetenciaId,
    selectedDesempenoIds,
    selectedNivelDificultad,
    nivelesDificultad: NIVELES_DIFICULTAD,
    tiposProducto: TIPOS_PRODUCTO,
    cantidadPreguntas,
    textoBase,
    useTextoBase,
    contenidoTematico,
    tipoProducto,
    selectedFiles,
    filesMetadata,
    uploadingFile,
    uploadError,
    loading,
    loadingDesempenos,
    loadingGrados,
    descargandoWord,
    error,
    resultado,
    showResults,
    activeCapacidadTab,
    activeTab,
    desempenosPorCapacidad,
    selectedDesempenosCount,
    gradoOptions,
    competenciaOptions,
    capacidadesActuales,
    loadInitialData,
    selectAllCapacidad,
    deselectAllCapacidad,
    deselectAll,
    handleFileUpload,
    clearFiles,
    generarPreguntas,
    descargarExamenWord
  };
}
