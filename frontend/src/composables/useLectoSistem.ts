import { ref, shallowRef, watch, computed } from 'vue';
import type { Examen, DesempenoItem, Grado, NivelLogro } from '../types';
import desempenosService from '../services/api';

// Tipo para niveles de dificultad
export type NivelDificultad = 'basico' | 'intermedio' | 'avanzado';

export interface NivelDificultadOption {
  id: NivelDificultad;
  nombre: string;
  descripcion: string;
  icono: string;
}

export const NIVELES_DIFICULTAD: NivelDificultadOption[] = [
  {
    id: 'basico',
    nombre: 'Básico',
    descripcion: 'Preguntas simples y sencillas',
    icono: 'Sprout'
  },
  {
    id: 'intermedio',
    nombre: 'Intermedio',
    descripcion: 'Demanda cognitiva media',
    icono: 'Leaf'
  },
  {
    id: 'avanzado',
    nombre: 'Avanzado',
    descripcion: 'Alta demanda cognitiva',
    icono: 'TreeDeciduous'
  }
];

export function useLectoSistem() {
  const grados = ref<Grado[]>([]);
  const desempenos = ref<DesempenoItem[]>([]);
  const niveles = ref<NivelLogro[]>([]);

  const selectedGradoId = shallowRef<number | null>(null);
  const selectedDesempenoIds = ref<number[]>([]);
  const selectedNivelLogro = shallowRef<string>('en_proceso');
  const selectedNivelDificultad = shallowRef<NivelDificultad>('intermedio');
  const selectedTipoTextual = shallowRef<string | null>(null);
  const selectedFormatoTextual = shallowRef<string | null>(null);

  const tipoTextualOptions = [
    { id: 'narrativo', label: 'Narrativo (Cuento, Noticia)' },
    { id: 'descriptivo', label: 'Descriptivo (Guía, Artículo)' },
    { id: 'instructivo', label: 'Instructivo (Receta, Manual)' },
    { id: 'argumentativo', label: 'Argumentativo (Ensayo, Opinión)' },
    { id: 'expositivo', label: 'Expositivo (Informe, Divulgación)' }
  ];

  const formatoTextualOptions = [
    { id: 'continuo', label: 'Continuo (Párrafos)' },
    { id: 'discontinuo', label: 'Discontinuo (Tablas, Gráficos)' },
    { id: 'mixto', label: 'Mixto (Ambos)' },
    { id: 'multiple', label: 'Múltiple (Varias Fuentes)' }
  ];

  const cantidadPreguntas = shallowRef(3);
  const textoBase = shallowRef('');
  const useTextoBase = shallowRef(false);
  const selectedFiles = ref<File[]>([]);
  const filesMetadata = ref<{ archivos: { filename: string; palabras: number; caracteres: number }[]; total_palabras: number; total_caracteres: number } | null>(null);
  const uploadingFile = shallowRef(false);
  const uploadError = shallowRef<string | null>(null);

  const loading = shallowRef(false);
  const loadingDesempenos = shallowRef(false);
  const descargandoWord = shallowRef(false);
  const error = shallowRef<string | null>(null);
  const resultado = ref<{
    grado: string;
    desempenos_usados: string;
    saludo: string;
    examen: Examen;
    total_preguntas: number;
  } | null>(null);
  const showResults = shallowRef(false);
  const activeCapacidadTab = shallowRef<string>('literal');
  const activeTab = shallowRef<string>('generador');

  const selectedDesempenosCount = computed(() => selectedDesempenoIds.value.length);

  const desempenosPorCapacidad = computed(() => {
    const grupos: Record<string, DesempenoItem[]> = {
      literal: [],
      inferencial: [],
      critico: []
    };
    desempenos.value.forEach(d => {
      if (grupos[d.capacidad_tipo]) {
        grupos[d.capacidad_tipo]!.push(d);
      }
    });
    return grupos;
  });

  const gradosPorNivel = computed(() => {
    return {
      primaria: grados.value.filter(g => g.nivel === 'primaria'),
      secundaria: grados.value.filter(g => g.nivel === 'secundaria')
    };
  });

  const gradoOptions = computed(() => {
    const options: { id: number; label: string; group: string }[] = [];
    gradosPorNivel.value.primaria.forEach(g => {
      options.push({ id: g.id, label: `${g.numero}° Primaria`, group: 'Primaria' });
    });
    gradosPorNivel.value.secundaria.forEach(g => {
      options.push({ id: g.id, label: `${g.numero}° Secundaria`, group: 'Secundaria' });
    });
    return options;
  });

  const desempenoOptions = computed(() => {
    return desempenos.value.map(d => ({
      id: d.id,
      label: `${d.codigo} - ${d.descripcion.substring(0, 100)}${d.descripcion.length > 100 ? '...' : ''}`,
      group: d.capacidad_tipo ? d.capacidad_tipo.toUpperCase() : 'General'
    }));
  });

  watch(selectedGradoId, async (newVal) => {
    if (!newVal) {
      desempenos.value = [];
      selectedDesempenoIds.value = [];
      return;
    }
    loadingDesempenos.value = true;
    try {
      desempenos.value = await desempenosService.getDesempenosPorGrado(newVal);
      selectedDesempenoIds.value = [];
    } catch (e) {
      console.error('Error loading desempeños:', e);
    } finally {
      loadingDesempenos.value = false;
    }
  });

  const loadInitialData = async () => {
    try {
      const [gradosData, nivelesData] = await Promise.all([
        desempenosService.getGrados(),
        desempenosService.getNivelesLogro()
      ]);
      grados.value = gradosData;
      niveles.value = nivelesData.niveles;
      if (gradosData.length > 0 && !selectedGradoId.value) {
        selectedGradoId.value = gradosData[0]?.id ?? null;
      }
    } catch (e) {
      console.error('Error loading data:', e);
      error.value = 'Error al cargar los datos iniciales';
    }
  };

  const selectAllCapacidad = (tipo: string) => {
    const ids = desempenosPorCapacidad.value[tipo]?.map(d => d.id) || [];
    ids.forEach(id => {
      if (!selectedDesempenoIds.value.includes(id)) {
        selectedDesempenoIds.value.push(id);
      }
    });
  };

  const deselectAllCapacidad = (tipo: string) => {
    const ids = desempenosPorCapacidad.value[tipo]?.map(d => d.id) || [];
    selectedDesempenoIds.value = selectedDesempenoIds.value.filter(id => !ids.includes(id));
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
    if (selectedDesempenoIds.value.length === 0) {
      error.value = 'Por favor, selecciona al menos un desempeño';
      return;
    }
    loading.value = true;
    error.value = null;
    resultado.value = null;
    showResults.value = true;
    try {
      resultado.value = await desempenosService.generarPreguntas({
        grado_id: selectedGradoId.value,
        desempeno_ids: selectedDesempenoIds.value,
        cantidad: cantidadPreguntas.value,
        nivel_logro: selectedNivelLogro.value,
        nivel_dificultad: selectedNivelDificultad.value,
        tipo_textual: selectedTipoTextual.value || undefined,
        formato_textual: selectedFormatoTextual.value || undefined,
        texto_base: useTextoBase.value ? textoBase.value : undefined
      });
    } catch (e: any) {
      error.value = e.response?.data?.detail || 'Error al generar el examen';
      console.error('Error:', e);
    } finally {
      loading.value = false;
    }
  };

  const descargarExamenWord = async () => {
    if (!resultado.value?.examen) return;
    descargandoWord.value = true;
    try {
      await desempenosService.descargarWord(resultado.value.examen, resultado.value.grado);
    } catch (e: any) {
      error.value = 'Error al descargar el documento Word';
      console.error('Error:', e);
    } finally {
      descargandoWord.value = false;
    }
  };

  const getCapacidadLabel = (tipo: string): string => {
    const labels: Record<string, string> = {
      'literal': 'LITERAL',
      'inferencial': 'INFERENCIAL',
      'critico': 'CRÍTICO'
    };
    return labels[tipo] || tipo;
  };

  const getNivelBadgeClass = (nivel: string): string => {
    const classes: Record<string, string> = {
      'LITERAL': 'bg-teal-100 text-teal-700 dark:bg-teal-900/30 dark:text-teal-400',
      'INFERENCIAL': 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
      'CRITICO': 'bg-violet-100 text-violet-700 dark:bg-violet-900/30 dark:text-violet-400'
    };
    return classes[nivel] || 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300';
  };

  return {
    grados,
    desempenos,
    niveles,
    selectedGradoId,
    selectedDesempenoIds,
    selectedNivelLogro,
    selectedNivelDificultad,
    nivelesDificultad: NIVELES_DIFICULTAD,
    cantidadPreguntas,
    textoBase,
    useTextoBase,
    selectedFiles,
    filesMetadata,
    uploadingFile,
    uploadError,
    // New fields
    selectedTipoTextual,
    selectedFormatoTextual,
    tipoTextualOptions,
    formatoTextualOptions,
    
    loading,
    loadingDesempenos,
    descargandoWord,
    error,
    resultado,
    showResults,
    activeCapacidadTab,
    activeTab,
    selectedDesempenosCount,
    desempenosPorCapacidad,
    gradoOptions,
    desempenoOptions,
    loadInitialData,
    selectAllCapacidad,
    deselectAllCapacidad,
    handleFileUpload,
    clearFiles,
    generarPreguntas,
    descargarExamenWord,
    getCapacidadLabel,
    getNivelBadgeClass
  };
}
