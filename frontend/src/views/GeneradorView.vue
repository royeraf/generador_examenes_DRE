<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue';
import type { Grado, NivelLogro, DesempenoItem, Examen } from '../types';
import desempenosService from '../services/api';
import ComboBox from '../components/ComboBox.vue';
import PromptModal from '../components/PromptModal.vue';
import { useTheme } from '../composables/useTheme';
import {
  FileText,
  BookOpen,
  Hash,
  CloudUpload,
  Zap,
  Copy,
  Check,
  AlertTriangle,
  ClipboardList,
  Loader2,
  HelpCircle,
  Download,
  LayoutGrid,
  X,
  Sun,
  Moon,
  Sparkles,
  FileUp,
  GraduationCap,
  Target,
  Eye,
  EyeOff
} from 'lucide-vue-next';
import Footer from './Footer.vue'

const { isDark, toggleTheme } = useTheme();

// State
const grados = ref<Grado[]>([]);
const nivelesLogro = ref<NivelLogro[]>([]);
const desempenos = ref<DesempenoItem[]>([]);
const selectedGradoId = ref<number | null>(null);
const selectedDesempenoIds = ref<number[]>([]);
const selectedNivelLogro = ref<string>('en_proceso');
const cantidadPreguntas = ref(3);
const textoBase = ref('');
const useTextoBase = ref(false);
const selectedFiles = ref<File[]>([]);
const filesMetadata = ref<{ archivos: { filename: string; palabras: number; caracteres: number }[]; total_palabras: number; total_caracteres: number } | null>(null);
const uploadingFile = ref(false);
const uploadError = ref<string | null>(null);

const loading = ref(false);
const loadingDesempenos = ref(false);
const descargandoWord = ref(false);
const error = ref<string | null>(null);
const resultado = ref<{
  grado: string;
  desempenos_usados: string;
  saludo: string;
  examen: Examen;
  total_preguntas: number;
} | null>(null);
const showPromptModal = ref(false);
const showResults = ref(false);
const activeCapacidadTab = ref<string>('literal');

// Computed
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

const selectedDesempenosCount = computed(() => selectedDesempenoIds.value.length);

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

const promptTexto = computed(() => {
  if (!selectedGradoId.value || selectedDesempenoIds.value.length === 0) return '';

  const grado = grados.value.find(g => g.id === selectedGradoId.value);
  const desempenosSeleccionados = desempenos.value
    .filter(d => selectedDesempenoIds.value.includes(d.id))
    .map(d => `${d.codigo}. ${d.descripcion} (${d.capacidad_tipo.toUpperCase()})`)
    .join('\n');

  let textoLectura = '';
  if (useTextoBase.value && textoBase.value) {
    textoLectura = `\nTEXTO DE LECTURA:\n"""\n${textoBase.value}\n"""\n`;
  }

  return `Eres un experto en la elaboración de preguntas de comprensión lectora que trabaja con estudiantes de Perú. Piensa 10 veces antes de responder.

Primero debes saludar muy amablemente como un experto en la elaboración de preguntas de comprensión lectora.

Luego, el examen debe tener exactamente ${cantidadPreguntas.value} preguntas para estudiantes de ${grado?.nombre || 'el grado seleccionado'}.
${textoLectura}
Usarás los siguientes desempeños que están enumerados e indican entre paréntesis si es de nivel LITERAL, INFERENCIAL o CRÍTICO:
${desempenosSeleccionados}

El examen debe presentar:
1. Un 'título' motivador para el examen
2. Una sección para que los estudiantes ingresen sus 'Apellidos y Nombres' y la 'Fecha'
3. 'Instrucciones precisas en un párrafo' para responder el examen
4. La 'lectura completa' o 'un fragmento de la lectura' que utilizarás para que los estudiantes respondan las preguntas
5. Las preguntas con esquema de opción múltiple (4 alternativas A, B, C, D siendo una sola la correcta, en orden aleatorio)
6. Al final una 'tabla' indicando: los desempeños utilizados, número de pregunta, nivel (LITERAL/INFERENCIAL/CRÍTICO) y alternativa correcta`;
});

watch(selectedGradoId, async (newGradoId) => {
  if (!newGradoId) {
    desempenos.value = [];
    selectedDesempenoIds.value = [];
    return;
  }
  loadingDesempenos.value = true;
  try {
    const data = await desempenosService.getDesempenosPorGrado(newGradoId);
    desempenos.value = data;
    selectedDesempenoIds.value = [];
  } catch (e) {
    console.error('Error loading desempeños:', e);
  } finally {
    loadingDesempenos.value = false;
  }
});

onMounted(async () => {
  try {
    const [gradosData, nivelesData] = await Promise.all([
      desempenosService.getGrados(),
      desempenosService.getNivelesLogro()
    ]);
    grados.value = gradosData;
    nivelesLogro.value = nivelesData.niveles;
    if (gradosData.length > 0) {
      selectedGradoId.value = gradosData[0]?.id ?? null;
    }
  } catch (e) {
    console.error('Error loading data:', e);
    error.value = 'Error al cargar los datos iniciales';
  }
});

const toggleDesempeno = (id: number) => {
  const index = selectedDesempenoIds.value.indexOf(id);
  if (index === -1) {
    selectedDesempenoIds.value.push(id);
  } else {
    selectedDesempenoIds.value.splice(index, 1);
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
    const response = await desempenosService.generarPreguntas({
      grado_id: selectedGradoId.value,
      nivel_logro: selectedNivelLogro.value,
      cantidad: cantidadPreguntas.value,
      texto_base: useTextoBase.value ? textoBase.value : undefined,
      desempeno_ids: selectedDesempenoIds.value
    });
    resultado.value = response;
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'Error al generar las preguntas';
    console.error('Error:', e);
  } finally {
    loading.value = false;
  }
};

const descargarExamenWord = async () => {
  if (!resultado.value?.examen) return;
  descargandoWord.value = true;
  try {
    await desempenosService.descargarWord(
      resultado.value.examen,
      resultado.value.grado
    );
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
    'LITERAL': 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400',
    'INFERENCIAL': 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
    'CRITICO': 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400'
  };
  return classes[nivel] || 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300';
};
</script>

<template>
  <div
    class="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/50 to-indigo-100/50 dark:from-slate-950 dark:via-slate-900 dark:to-indigo-950/50 transition-colors">

    <!-- Decorative Background Elements -->
    <div class="fixed inset-0 overflow-hidden pointer-events-none">
      <div class="absolute -top-24 -right-24 w-96 h-96 bg-indigo-200/40 dark:bg-indigo-500/10 rounded-full blur-3xl">
      </div>
      <div class="absolute top-1/3 -left-24 w-80 h-80 bg-blue-200/40 dark:bg-blue-500/10 rounded-full blur-3xl"></div>
      <div class="absolute bottom-0 right-1/4 w-72 h-72 bg-purple-200/30 dark:bg-purple-500/10 rounded-full blur-3xl">
      </div>
      <div class="absolute top-2/3 left-1/3 w-64 h-64 bg-emerald-200/20 dark:bg-emerald-500/5 rounded-full blur-3xl">
      </div>
    </div>

    <!-- Header -->
    <header class="bg-white dark:bg-slate-800 border-b border-gray-200 dark:border-slate-700 sticky top-0 z-50">
      <div class="max-w-7xl mx-auto px-6 py-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 bg-indigo-600 rounded-lg flex items-center justify-center">
              <Sparkles class="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 class="text-xl font-bold text-slate-900 dark:text-white">Generador de Preguntas</h1>
              <p class="text-slate-500 dark:text-slate-400 text-sm">Sistema de evaluación DREHCO</p>
            </div>
          </div>

          <div class="flex items-center gap-3">
            <button v-if="resultado && !loading" @click="showResults = !showResults"
              class="px-4 py-2 rounded-lg font-medium text-sm flex items-center gap-2 transition-colors" :class="showResults
                ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400'
                : 'bg-gray-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300'">
              <Eye v-if="showResults" class="w-4 h-4" />
              <EyeOff v-else class="w-4 h-4" />
              {{ showResults ? 'Ocultar' : 'Ver Resultado' }}
            </button>

            <button @click="toggleTheme"
              class="p-2.5 rounded-lg bg-gray-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 hover:bg-gray-200 dark:hover:bg-slate-600 transition-colors">
              <Sun v-if="isDark" class="w-5 h-5" />
              <Moon v-else class="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </header>

    <main class="max-w-7xl mx-auto px-6 py-6">

      <!-- Configuration Row -->
      <div class="grid md:grid-cols-3 gap-4 mb-6">

        <!-- Grade Selection -->
        <div class="bg-white dark:bg-slate-800 rounded-lg p-4 border border-gray-200 dark:border-slate-700">
          <label class="flex items-center gap-2 text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">
            <GraduationCap class="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
            Grado
          </label>
          <ComboBox v-model="selectedGradoId" :options="gradoOptions" placeholder="Seleccionar grado..." />
        </div>

        <!-- Quantity -->
        <div class="bg-white dark:bg-slate-800 rounded-lg p-4 border border-gray-200 dark:border-slate-700">
          <label class="flex items-center gap-2 text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">
            <Hash class="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
            Cantidad de Preguntas
          </label>
          <div class="flex items-center gap-4">
            <input type="range" v-model="cantidadPreguntas" min="1" max="10"
              class="flex-1 h-2 bg-gray-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer accent-indigo-600" />
            <span
              class="w-10 h-10 rounded-lg bg-indigo-100 dark:bg-indigo-900/30 flex items-center justify-center text-lg font-bold text-indigo-700 dark:text-indigo-400">
              {{ cantidadPreguntas }}
            </span>
          </div>
        </div>

        <!-- File Upload -->
        <div class="bg-white dark:bg-slate-800 rounded-lg p-4 border border-gray-200 dark:border-slate-700">
          <label class="flex items-center gap-2 cursor-pointer select-none mb-3">
            <input type="checkbox" v-model="useTextoBase"
              class="w-4 h-4 rounded border-gray-300 dark:border-slate-600 text-indigo-600 focus:ring-indigo-500" />
            <FileUp class="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
            <span class="text-sm font-medium text-slate-700 dark:text-slate-300">Usar Texto Base</span>
          </label>

          <div v-if="useTextoBase" class="space-y-2">
            <div v-if="selectedFiles.length === 0 && !uploadingFile" class="relative">
              <input type="file" accept=".pdf,.docx,.doc" multiple @change="handleFileUpload"
                class="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10" />
              <div
                class="flex items-center justify-center py-3 px-3 bg-gray-50 dark:bg-slate-900 border-2 border-dashed border-gray-300 dark:border-slate-600 rounded-lg hover:border-indigo-400 transition-colors">
                <div class="text-center">
                  <CloudUpload class="w-5 h-5 text-gray-400 mx-auto mb-1" />
                  <span class="text-gray-500 dark:text-slate-400 text-xs">PDF o Word</span>
                </div>
              </div>
            </div>

            <div v-if="uploadingFile"
              class="flex items-center justify-center gap-2 py-3 bg-gray-50 dark:bg-slate-900 rounded-lg">
              <Loader2 class="w-4 h-4 text-indigo-600 animate-spin" />
              <span class="text-indigo-600 dark:text-indigo-400 text-sm">Procesando...</span>
            </div>

            <div v-if="selectedFiles.length > 0 && !uploadingFile && filesMetadata" class="space-y-2">
              <div v-for="(archivo, index) in filesMetadata.archivos" :key="index"
                class="flex items-center gap-2 p-2 bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800 rounded-lg text-xs">
                <FileText class="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                <span class="flex-1 truncate text-slate-700 dark:text-slate-200">{{ archivo.filename }}</span>
                <span class="text-slate-500">{{ archivo.palabras }}p</span>
              </div>
              <button @click="clearFiles" class="text-xs text-red-500 hover:text-red-600 flex items-center gap-1">
                <X class="w-3 h-3" /> Quitar
              </button>
            </div>

            <div v-if="uploadError"
              class="p-2 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
              <p class="text-red-600 dark:text-red-400 text-xs flex items-center gap-1">
                <AlertTriangle class="w-3 h-3" />
                {{ uploadError }}
              </p>
            </div>
          </div>

          <p v-else class="text-gray-400 dark:text-slate-500 text-xs">
            Activa para usar lectura personalizada
          </p>
        </div>
      </div>

      <!-- Main Content -->
      <div class="grid lg:grid-cols-2 gap-6">

        <!-- Left: Desempeños -->
        <div class="flex flex-col space-y-3">

          <!-- Desempeños Card -->
          <div
            class="h-[580px] flex flex-col bg-white dark:bg-slate-800 rounded-xl border border-gray-200 dark:border-slate-700 overflow-hidden shadow-sm">

            <!-- Card Header -->
            <div class="bg-gradient-to-r from-indigo-500 to-purple-600 px-4 py-3">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <div class="w-8 h-8 bg-white/20 rounded-lg flex items-center justify-center">
                    <Target class="w-4 h-4 text-white" />
                  </div>
                  <div>
                    <h2 class="text-base font-semibold text-white">Desempeños</h2>
                    <span v-if="desempenos.length" class="text-xs text-white/70">
                      {{ desempenos.length }} disponibles
                    </span>
                  </div>
                </div>
                <span v-if="selectedDesempenosCount > 0"
                  class="px-2.5 py-1 rounded-full bg-white/20 text-white text-xs font-medium backdrop-blur-sm">
                  {{ selectedDesempenosCount }} seleccionados
                </span>
              </div>
            </div>

            <!-- Loading -->
            <div v-if="loadingDesempenos" class="p-4 space-y-3">
              <div v-for="i in 3" :key="i" class="space-y-2">
                <div class="h-4 w-24 bg-gray-200 dark:bg-slate-700 rounded animate-pulse"></div>
                <div v-for="j in 2" :key="j" class="flex items-start gap-2 p-2 bg-gray-50 dark:bg-slate-900 rounded-lg">
                  <div class="w-4 h-4 bg-gray-200 dark:bg-slate-700 rounded animate-pulse"></div>
                  <div class="flex-1 space-y-1.5">
                    <div class="h-2.5 w-full bg-gray-200 dark:bg-slate-700 rounded animate-pulse"></div>
                    <div class="h-2.5 w-2/3 bg-gray-200 dark:bg-slate-700 rounded animate-pulse"></div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Desempeños List with Tabs -->
            <div v-else-if="desempenos.length > 0" class="flex-1 flex flex-col overflow-hidden">

              <!-- Tab Navigation -->
              <div class="flex border-b border-gray-200 dark:border-slate-700">
                <button v-for="tipo in ['literal', 'inferencial', 'critico']" :key="tipo"
                  @click="activeCapacidadTab = tipo"
                  class="flex-1 relative px-4 py-3 text-xs font-bold uppercase tracking-wide transition-colors" :class="activeCapacidadTab === tipo
                    ? {
                      'text-emerald-600 dark:text-emerald-400': tipo === 'literal',
                      'text-amber-600 dark:text-amber-400': tipo === 'inferencial',
                      'text-purple-600 dark:text-purple-400': tipo === 'critico'
                    }
                    : 'text-slate-400 dark:text-slate-500 hover:text-slate-600 dark:hover:text-slate-300'">
                  <div class="flex items-center justify-center gap-2">
                    <span>{{ getCapacidadLabel(tipo) }}</span>
                    <span v-if="desempenosPorCapacidad[tipo]?.length"
                      class="text-[10px] px-1.5 py-0.5 rounded-full font-medium" :class="activeCapacidadTab === tipo
                        ? {
                          'bg-emerald-100 text-emerald-600 dark:bg-emerald-900/50 dark:text-emerald-400': tipo === 'literal',
                          'bg-amber-100 text-amber-600 dark:bg-amber-900/50 dark:text-amber-400': tipo === 'inferencial',
                          'bg-purple-100 text-purple-600 dark:bg-purple-900/50 dark:text-purple-400': tipo === 'critico'
                        }
                        : 'bg-slate-100 dark:bg-slate-800'">
                      {{ desempenosPorCapacidad[tipo].length }}
                    </span>
                  </div>
                  <!-- Active indicator -->
                  <div v-if="activeCapacidadTab === tipo" class="absolute bottom-0 left-0 right-0 h-0.5" :class="{
                    'bg-emerald-500': tipo === 'literal',
                    'bg-amber-500': tipo === 'inferencial',
                    'bg-purple-500': tipo === 'critico'
                  }"></div>
                </button>
              </div>

              <!-- Tab Content -->
              <div class="flex-1 flex flex-col overflow-hidden p-3">
                <!-- Actions Bar -->
                <div class="flex items-center justify-between mb-3 px-1">
                  <span class="text-xs text-slate-500 dark:text-slate-400">
                    Selecciona los desempeños a evaluar
                  </span>
                  <div class="flex gap-2 text-[11px] font-medium">
                    <button @click="selectAllCapacidad(activeCapacidadTab)"
                      class="px-2.5 py-1 rounded-full transition-colors" :class="{
                        'text-emerald-600 hover:bg-emerald-50 dark:text-emerald-400 dark:hover:bg-emerald-900/20': activeCapacidadTab === 'literal',
                        'text-amber-600 hover:bg-amber-50 dark:text-amber-400 dark:hover:bg-amber-900/20': activeCapacidadTab === 'inferencial',
                        'text-purple-600 hover:bg-purple-50 dark:text-purple-400 dark:hover:bg-purple-900/20': activeCapacidadTab === 'critico'
                      }">
                      Seleccionar todos
                    </button>
                    <button @click="deselectAllCapacidad(activeCapacidadTab)"
                      class="px-2.5 py-1 rounded-full text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors">
                      Ninguno
                    </button>
                  </div>
                </div>

                <!-- Items Grid -->
                <div class="flex-1 overflow-y-auto space-y-1.5 pr-1">
                  <template v-if="desempenosPorCapacidad[activeCapacidadTab]?.length">
                    <label v-for="des in desempenosPorCapacidad[activeCapacidadTab]" :key="des.id"
                      class="group flex items-start gap-3 p-3 rounded-xl cursor-pointer transition-all duration-150 border"
                      :class="selectedDesempenoIds.includes(des.id)
                        ? {
                          'bg-emerald-50 dark:bg-emerald-900/20 border-emerald-200 dark:border-emerald-800 ring-1 ring-emerald-300 dark:ring-emerald-700': activeCapacidadTab === 'literal',
                          'bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800 ring-1 ring-amber-300 dark:ring-amber-700': activeCapacidadTab === 'inferencial',
                          'bg-purple-50 dark:bg-purple-900/20 border-purple-200 dark:border-purple-800 ring-1 ring-purple-300 dark:ring-purple-700': activeCapacidadTab === 'critico'
                        }
                        : 'border-gray-100 dark:border-slate-700 hover:border-gray-200 dark:hover:border-slate-600 hover:bg-gray-50 dark:hover:bg-slate-800/50'">
                      <div class="relative flex items-center justify-center mt-0.5">
                        <input type="checkbox" :checked="selectedDesempenoIds.includes(des.id)"
                          @change="toggleDesempeno(des.id)"
                          class="h-5 w-5 rounded-md border-2 transition-colors cursor-pointer" :class="selectedDesempenoIds.includes(des.id)
                            ? {
                              'border-emerald-500 text-emerald-600 dark:border-emerald-400': activeCapacidadTab === 'literal',
                              'border-amber-500 text-amber-600 dark:border-amber-400': activeCapacidadTab === 'inferencial',
                              'border-purple-500 text-purple-600 dark:border-purple-400': activeCapacidadTab === 'critico'
                            }
                            : 'border-gray-300 dark:border-slate-500 group-hover:border-indigo-400'" />
                      </div>
                      <div class="flex-1 min-w-0">
                        <div class="flex items-center gap-2 mb-1">
                          <span class="text-[10px] px-2 py-0.5 rounded-md font-mono font-bold" :class="{
                            'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-400': activeCapacidadTab === 'literal',
                            'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-400': activeCapacidadTab === 'inferencial',
                            'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-400': activeCapacidadTab === 'critico'
                          }">
                            {{ des.codigo }}
                          </span>
                        </div>
                        <p class="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
                          {{ des.descripcion }}
                        </p>
                      </div>
                    </label>
                  </template>

                  <!-- Empty Tab -->
                  <div v-else class="py-8 text-center">
                    <p class="text-slate-400 dark:text-slate-500 text-sm">
                      No hay desempeños de tipo {{ getCapacidadLabel(activeCapacidadTab) }}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <!-- Empty -->
            <div v-else class="flex-1 flex flex-col items-center justify-center px-6 text-center">
              <div
                class="w-14 h-14 bg-gradient-to-br from-indigo-100 to-purple-100 dark:from-indigo-900/30 dark:to-purple-900/30 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <BookOpen class="w-7 h-7 text-indigo-500 dark:text-indigo-400" />
              </div>
              <h3 class="text-slate-700 dark:text-slate-200 font-medium mb-1">Sin desempeños</h3>
              <p class="text-slate-500 dark:text-slate-400 text-sm">Selecciona un grado para ver los desempeños
                disponibles</p>
            </div>
          </div>

          <!-- Generate Button -->
          <button @click="generarPreguntas" :disabled="loading || !selectedGradoId || selectedDesempenoIds.length === 0"
            class="w-full px-6 py-4 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2">
            <Loader2 v-if="loading" class="w-5 h-5 animate-spin" />
            <Zap v-else class="w-5 h-5" />
            {{ loading ? 'Generando...' : 'Generar Examen' }}
          </button>

          <!-- Error -->
          <div v-if="error"
            class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 p-4 rounded-lg text-sm flex items-start gap-2">
            <AlertTriangle class="w-5 h-5 flex-shrink-0" />
            <p>{{ error }}</p>
          </div>

          <!-- Prompt Button -->
          <button v-if="promptTexto" @click="showPromptModal = true"
            class="w-full px-4 py-3 bg-white dark:bg-slate-800 rounded-lg border border-gray-200 dark:border-slate-700 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors">
            <span class="text-slate-700 dark:text-slate-300 text-sm font-medium flex items-center gap-2">
              <Copy class="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
              Ver Prompt
            </span>
            <span class="text-xs text-slate-400 dark:text-slate-500">Clic para abrir</span>
          </button>
        </div>

        <!-- Right: Results -->
        <div class="flex flex-col">

          <!-- Empty State -->
          <div v-if="!resultado && !loading"
            class="h-[580px] bg-white dark:bg-slate-800 rounded-xl border border-gray-200 dark:border-slate-700 text-center flex flex-col items-center justify-center shadow-sm">
            <Zap class="w-12 h-12 text-gray-300 dark:text-slate-600 mb-4" />
            <h3 class="text-lg font-semibold text-slate-800 dark:text-white mb-2">Listo para generar</h3>
            <p class="text-slate-500 dark:text-slate-400 text-sm max-w-xs">
              Selecciona los desempeños y genera tu examen con IA.
            </p>
          </div>

          <!-- Loading State -->
          <div v-if="loading"
            class="h-[580px] bg-white dark:bg-slate-800 rounded-xl border border-gray-200 dark:border-slate-700 text-center flex flex-col items-center justify-center shadow-sm">
            <div
              class="w-14 h-14 border-4 border-gray-200 dark:border-slate-600 border-t-indigo-600 dark:border-t-indigo-400 rounded-full animate-spin mb-4">
            </div>
            <h3 class="text-lg font-semibold text-slate-800 dark:text-white mb-2">Generando Examen</h3>
            <p class="text-slate-500 dark:text-slate-400 text-sm">Esto puede tomar unos segundos...</p>
          </div>

          <!-- Results -->
          <div v-if="resultado && !loading && showResults"
            class="h-[580px] bg-white dark:bg-slate-800 rounded-xl border border-gray-200 dark:border-slate-700 shadow-sm flex flex-col overflow-hidden">

            <!-- Results Header -->
            <div class="bg-gradient-to-r from-emerald-500 to-teal-600 px-4 py-3 flex-shrink-0">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <div class="w-8 h-8 bg-white/20 rounded-lg flex items-center justify-center">
                    <ClipboardList class="w-4 h-4 text-white" />
                  </div>
                  <div>
                    <h2 class="text-base font-semibold text-white">{{ resultado.examen.titulo }}</h2>
                    <span class="text-xs text-white/70">
                      {{ resultado.total_preguntas }} preguntas · {{ resultado.examen.grado }}
                    </span>
                  </div>
                </div>
                <button @click="descargarExamenWord" :disabled="descargandoWord"
                  class="px-3 py-1.5 bg-white/20 hover:bg-white/30 text-white text-xs font-medium rounded-lg transition-colors flex items-center gap-1.5">
                  <Loader2 v-if="descargandoWord" class="w-3.5 h-3.5 animate-spin" />
                  <Download v-else class="w-3.5 h-3.5" />
                  {{ descargandoWord ? 'Generando...' : 'Descargar Word' }}
                </button>
              </div>
            </div>

            <!-- Scrollable Content -->
            <div class="flex-1 overflow-y-auto p-4 space-y-4">

              <!-- Instrucciones -->
              <div
                class="bg-indigo-50 dark:bg-indigo-900/20 rounded-lg p-3 border border-indigo-100 dark:border-indigo-800">
                <p class="text-slate-700 dark:text-slate-300 text-sm">
                  <strong class="text-indigo-700 dark:text-indigo-400">Instrucciones:</strong>
                  {{ resultado.examen.instrucciones }}
                </p>
              </div>

              <!-- Lectura -->
              <div class="bg-gray-50 dark:bg-slate-900 rounded-lg p-4 border border-gray-200 dark:border-slate-700">
                <h4 class="text-sm font-semibold text-slate-800 dark:text-white mb-2 flex items-center gap-2">
                  <BookOpen class="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
                  Lectura
                </h4>
                <p class="text-slate-700 dark:text-slate-300 text-sm leading-7 whitespace-pre-line">
                  {{ resultado.examen.lectura }}
                </p>
              </div>

              <!-- Preguntas -->
              <div class="space-y-3">
                <h4 class="text-sm font-semibold text-slate-800 dark:text-white flex items-center gap-2">
                  <HelpCircle class="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
                  Preguntas
                </h4>

                <div v-for="pregunta in resultado.examen.preguntas" :key="pregunta.numero"
                  class="bg-white dark:bg-slate-800 rounded-lg p-4 border border-gray-200 dark:border-slate-700">
                  <div class="flex items-start gap-3">
                    <span
                      class="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
                      {{ pregunta.numero }}
                    </span>
                    <div class="flex-1">
                      <span class="inline-block px-2 py-0.5 text-[10px] font-semibold uppercase rounded mb-2"
                        :class="getNivelBadgeClass(pregunta.nivel)">
                        {{ pregunta.nivel }}
                      </span>
                      <p class="text-slate-800 dark:text-slate-200 font-medium mb-3">{{ pregunta.enunciado }}</p>

                      <div class="space-y-2">
                        <div v-for="opcion in pregunta.opciones" :key="opcion.letra"
                          class="flex items-center gap-2 text-sm py-2 px-3 rounded-lg border"
                          :class="opcion.es_correcta
                            ? 'bg-emerald-50 dark:bg-emerald-900/20 border-emerald-200 dark:border-emerald-800 text-emerald-700 dark:text-emerald-400'
                            : 'bg-gray-50 dark:bg-slate-900 border-gray-200 dark:border-slate-700 text-slate-600 dark:text-slate-400'">
                          <span class="font-semibold">{{ opcion.letra }})</span>
                          <span class="flex-1">{{ opcion.texto }}</span>
                          <Check v-if="opcion.es_correcta" class="w-4 h-4" />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Answer Table -->
              <div class="bg-white dark:bg-slate-800 rounded-lg p-4 border border-gray-200 dark:border-slate-700">
                <h4 class="text-sm font-semibold text-slate-800 dark:text-white mb-3 flex items-center gap-2">
                  <LayoutGrid class="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
                  Tabla de Respuestas
                </h4>
                <div class="overflow-x-auto rounded-lg border border-gray-200 dark:border-slate-700">
                  <table class="w-full text-sm">
                    <thead>
                      <tr class="bg-gray-50 dark:bg-slate-900 border-b border-gray-200 dark:border-slate-700">
                        <th class="text-left py-2 px-3 text-slate-500 dark:text-slate-400 font-medium text-xs">#</th>
                        <th class="text-left py-2 px-3 text-slate-500 dark:text-slate-400 font-medium text-xs">Desempeño
                        </th>
                        <th class="text-left py-2 px-3 text-slate-500 dark:text-slate-400 font-medium text-xs">Nivel
                        </th>
                        <th class="text-center py-2 px-3 text-slate-500 dark:text-slate-400 font-medium text-xs">Rpta.
                        </th>
                      </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-100 dark:divide-slate-700">
                      <tr v-for="fila in resultado.examen.tabla_respuestas" :key="fila.pregunta">
                        <td class="py-2 px-3 text-slate-800 dark:text-slate-200 font-semibold">{{ fila.pregunta }}</td>
                        <td class="py-2 px-3 text-slate-600 dark:text-slate-400 text-xs">{{ fila.desempeno }}</td>
                        <td class="py-2 px-3">
                          <span class="px-2 py-0.5 text-[10px] font-semibold rounded"
                            :class="getNivelBadgeClass(fila.nivel)">
                            {{ fila.nivel }}
                          </span>
                        </td>
                        <td class="py-2 px-3 text-center">
                          <span
                            class="w-6 h-6 bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 rounded-lg inline-flex items-center justify-center font-bold text-xs">
                            {{ fila.respuesta_correcta }}
                          </span>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              <p class="text-center text-xs text-slate-400 dark:text-slate-500">
                Examen generado por IA - Revisar antes de usar
              </p>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- Footer -->
    <Footer />

    <!-- Prompt Modal -->
    <PromptModal :isOpen="showPromptModal" :promptText="promptTexto" @close="showPromptModal = false" />
  </div>
</template>

<style scoped>
/* Scrollbar sutil */
::-webkit-scrollbar {
  width: 4px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background-color: #cbd5e1;
  border-radius: 20px;
}

.dark ::-webkit-scrollbar-thumb {
  background-color: #475569;
}
</style>
