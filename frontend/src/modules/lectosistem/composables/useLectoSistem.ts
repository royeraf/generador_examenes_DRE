import { ref, shallowRef, watch, computed } from 'vue';
import type { Examen, DesempenoItem, Grado, NivelLogro, FilesMetadata } from '../../../shared/types';
import desempenosService from '../../../shared/services/api';
import { NIVELES_DIFICULTAD } from '../../../shared/constants/niveles';
import { useBaseExam } from '../../../shared/composables/useBaseExam';
import { validateFiles, parseUploadError, formatPalabras } from '../../../shared/utils/uploadFeedback';
export type { NivelDificultad } from '../../../shared/constants/niveles';
export type { NivelDificultadOption } from '../../../shared/constants/niveles';

export interface TextoBaseItem {
  id: number;
  titulo: string;
  texto: string;
  uploadingFile: boolean;
  uploadError: string | null;
  filesMetadata: FilesMetadata | null;
}

export type TextosBaseTone = 'uploading' | 'error' | 'empty' | 'partial' | 'ready';

export interface TextosBaseStatus {
  tone: TextosBaseTone;
  label: string;
  tooltip: string;
  count: { filled: number; total: number };
}

const TEXTOS_STORAGE_KEY = 'lectosistem_textos_base';
const USE_TEXTO_STORAGE_KEY = 'lectosistem_use_texto_base';

type PersistedTexto = Pick<TextoBaseItem, 'titulo' | 'texto' | 'filesMetadata'>;

function loadTextosFromStorage(makeTexto: () => TextoBaseItem): TextoBaseItem[] {
  try {
    const raw = localStorage.getItem(TEXTOS_STORAGE_KEY);
    if (!raw) return [makeTexto()];
    const parsed: PersistedTexto[] = JSON.parse(raw);
    if (!Array.isArray(parsed) || parsed.length === 0) return [makeTexto()];
    return parsed.map(p => ({
      ...makeTexto(),
      titulo: p.titulo ?? '',
      texto: p.texto ?? '',
      filesMetadata: p.filesMetadata ?? null,
    }));
  } catch {
    return [makeTexto()];
  }
}

export { NIVELES_DIFICULTAD };

export function useLectoSistem() {
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

  const grados = ref<Grado[]>([]);
  const desempenos = ref<DesempenoItem[]>([]);
  const niveles = ref<NivelLogro[]>([]);

  const selectedNivelLogro = shallowRef<string>('en_proceso');
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

  const cantidadLiteral = shallowRef(1);
  const cantidadInferencial = shallowRef(1);
  const cantidadCritico = shallowRef(1);
  const useTextoBase = shallowRef(localStorage.getItem(USE_TEXTO_STORAGE_KEY) === 'true');

  let _nextTextoId = 1;
  const _makeTexto = (): TextoBaseItem => ({ id: _nextTextoId++, titulo: '', texto: '', uploadingFile: false, uploadError: null, filesMetadata: null });
  const textosBase = ref<TextoBaseItem[]>(loadTextosFromStorage(_makeTexto));
  // Sincronizar _nextTextoId con los IDs ya asignados al cargar
  _nextTextoId = textosBase.value.length + 1;

  watch(textosBase, (val) => {
    const toSave: PersistedTexto[] = val.map(t => ({ titulo: t.titulo, texto: t.texto, filesMetadata: t.filesMetadata }));
    localStorage.setItem(TEXTOS_STORAGE_KEY, JSON.stringify(toSave));
  }, { deep: true });

  watch(useTextoBase, (val) => {
    localStorage.setItem(USE_TEXTO_STORAGE_KEY, String(val));
  });

  const addTexto = () => { if (textosBase.value.length < 4) textosBase.value.push(_makeTexto()); };
  const removeTexto = (idx: number) => {
    if (textosBase.value.length > 1) textosBase.value.splice(idx, 1);
  };
  const clearTextos = () => { _nextTextoId = 1; textosBase.value = [_makeTexto()]; };

  const resultado = ref<{
    grado: string;
    desempenos_usados: string;
    saludo: string;
    examen: Examen;
    lecturas?: { titulo: string; texto: string }[];
    total_preguntas: number;
  } | null>(null);
  const activeCapacidadTab = shallowRef<string>('literal');

  const totalBreakdown = computed(() => cantidadLiteral.value + cantidadInferencial.value + cantidadCritico.value);
  const isBreakdownValid = computed(() => totalBreakdown.value === Number(cantidadPreguntas.value));

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
      const data = await desempenosService.getDesempenosPorGrado(newVal);
      desempenos.value = data;
      selectedDesempenoIds.value = [];
      const tabWithData = ['literal', 'inferencial', 'critico'].find(tipo => data.some(d => d.capacidad_tipo === tipo));
      activeCapacidadTab.value = tabWithData || 'literal';
    } catch (e) {
      console.error('Error loading desempeños:', e);
    } finally {
      loadingDesempenos.value = false;
    }
  });

  const loadInitialData = async () => {
    try {
      loadingGrados.value = true;
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
    } finally {
      loadingGrados.value = false;
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

  const handleFileUploadAt = async (idx: number, event: Event) => {
    const item = textosBase.value[idx];
    if (!item) return;
    const input = event.target as HTMLInputElement;
    const files = input.files;
    if (!files || files.length === 0) return;
    const fileArray: File[] = Array.from(files);
    const validationError = validateFiles(fileArray);
    if (validationError) {
      item.uploadError = validationError;
      input.value = '';
      return;
    }
    item.uploadingFile = true;
    item.uploadError = null;
    try {
      const result = await desempenosService.uploadTextoBase(fileArray);
      item.texto = result.texto;
      item.filesMetadata = {
        archivos: result.archivos,
        total_palabras: result.total_palabras,
        total_caracteres: result.total_caracteres,
        advertencias: result.advertencias
      };
      input.value = '';
    } catch (e: any) {
      item.uploadError = parseUploadError(e);
      item.texto = '';
      input.value = '';
      console.error('Error al subir archivo de texto base:', e);
    } finally {
      item.uploadingFile = false;
    }
  };

  const clearFilesAt = (idx: number) => {
    const item = textosBase.value[idx];
    if (!item) return;
    item.texto = '';
    item.uploadError = null;
    item.filesMetadata = null;
  };

  const textosBaseStatus = computed<TextosBaseStatus>(() => {
    const items = textosBase.value;
    const conTexto = items.filter(t => t.texto.trim().length > 0);
    const conArchivo = items.filter(t => t.filesMetadata && t.filesMetadata.archivos.length > 0);
    const count = { filled: conTexto.length, total: items.length };

    if (items.some(t => t.uploadingFile)) {
      return { tone: 'uploading', label: 'Procesando...', tooltip: 'Extrayendo texto del archivo, espera un momento.', count };
    }

    const errores = items
      .map((t, i) => (t.uploadError ? `Texto ${i + 1}: ${t.uploadError}` : null))
      .filter((m): m is string => !!m);
    if (errores.length > 0) {
      return { tone: 'error', label: 'Error al subir', tooltip: errores.join(' · '), count };
    }

    if (conTexto.length === 0) {
      return {
        tone: 'empty',
        label: 'Sin texto base',
        tooltip: 'Sube un PDF/Word o escribe el texto en "Textos Base".',
        count
      };
    }

    const archivosResumen = conArchivo
      .flatMap(t => t.filesMetadata!.archivos.map(a => `${a.filename} (${formatPalabras(a.palabras)})`))
      .join(' · ');

    if (conTexto.length < items.length) {
      return {
        tone: 'partial',
        label: 'con contenido',
        tooltip: archivosResumen || 'Algunos textos aún no tienen contenido.',
        count
      };
    }

    if (conArchivo.length > 0) {
      const totalPalabras = conArchivo.reduce((sum, t) => sum + (t.filesMetadata?.total_palabras || 0), 0);
      return {
        tone: 'ready',
        label: conArchivo.length === 1
          ? `1 archivo · ${formatPalabras(totalPalabras)}`
          : `${conArchivo.length} archivos · ${formatPalabras(totalPalabras)}`,
        tooltip: archivosResumen,
        count
      };
    }

    return {
      tone: 'ready',
      label: conTexto.length === 1 ? 'texto listo' : 'textos listos',
      tooltip: 'Contenido escrito manualmente.',
      count
    };
  });

  const generarPreguntas = async () => {
    if (!selectedGradoId.value) {
      error.value = 'Por favor, selecciona un grado';
      return;
    }
    if (selectedDesempenoIds.value.length === 0) {
      error.value = 'Por favor, selecciona al menos un desempeño';
      return;
    }
    if (useTextoBase.value && !textosBase.value.some(t => t.texto.trim())) {
      error.value = 'Activaste "Usar Textos Base" pero no cargaste ningún texto. Sube un archivo, escribe el texto o desactiva la opción.';
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
        cantidad_literal: cantidadLiteral.value,
        cantidad_inferencial: cantidadInferencial.value,
        cantidad_critico: cantidadCritico.value,
        nivel_logro: selectedNivelLogro.value,
        nivel_dificultad: selectedNivelDificultad.value,
        tipo_textual: selectedTipoTextual.value || undefined,
        formato_textual: selectedFormatoTextual.value || undefined,
        textos_base: useTextoBase.value
          ? textosBase.value.filter(t => t.texto.trim()).map(t => ({ titulo: t.titulo.trim(), texto: t.texto.trim() }))
          : undefined
      });
    } catch (e: any) {
      error.value = e.response?.data?.detail || 'Error al generar el examen';
      console.error('Error:', e);
    } finally {
      loading.value = false;
    }
  };

  const descargarExamenWord = makeDescargarWord(resultado);

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
      'CRITICO': 'bg-violet-100 text-violet-700 dark:bg-violet-900/30 dark:text-violet-400',
      'CRÍTICO': 'bg-violet-100 text-violet-700 dark:bg-violet-900/30 dark:text-violet-400'
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
    cantidadLiteral,
    cantidadInferencial,
    cantidadCritico,
    isBreakdownValid,
    totalBreakdown,
    useTextoBase,
    textosBase,
    textosBaseStatus,
    addTexto,
    removeTexto,
    clearTextos,
    handleFileUploadAt,
    clearFilesAt,
    selectedTipoTextual,
    selectedFormatoTextual,
    tipoTextualOptions,
    formatoTextualOptions,
    
    loading,
    loadingDesempenos,
    loadingGrados,
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
    generarPreguntas,
    descargarExamenWord,
    getCapacidadLabel,
    getNivelBadgeClass
  };
}
