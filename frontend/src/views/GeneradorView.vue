<script setup lang="ts">
import { ref, shallowRef, onMounted, watch, computed } from 'vue';
import type { Grado, NivelLogro, DesempenoItem, Examen } from '../types';
import desempenosService from '../services/api';
import ComboBox from '../components/ComboBox.vue';
import PromptModal from '../components/PromptModal.vue';
import Sistematizador from '../components/Sistematizador.vue';
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
  EyeOff,
  Pencil,
  Sigma,
  Brain,
  Rocket,
  Star,
  Award,
  Atom,
  Calculator,
  Globe,
  Trophy,
  Palette,
  Layers,
  FileQuestion,
  Medal,
  Music,
  Compass,
  Microscope,
  Ruler,
  PenTool,
  Shapes,
  Puzzle,
  Wand2,
  Infinity,
  FileSearch,
  Lightbulb,
  ClipboardCheck
} from 'lucide-vue-next';
import Footer from './Footer.vue'
import logoDre from '../assets/logo.png'
import mascotaLectosistem from '../assets/mascota_lectosistem.png'
import Checkbox from '../components/Checkbox.vue'

const { isDark, toggleTheme } = useTheme();

// State
const grados = ref<Grado[]>([]);
const nivelesLogro = ref<NivelLogro[]>([]);
const desempenos = ref<DesempenoItem[]>([]);
const selectedGradoId = shallowRef<number | null>(null);
const selectedDesempenoIds = ref<number[]>([]);
const selectedNivelLogro = shallowRef<string>('en_proceso');
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
const showPromptModal = shallowRef(false);
const showResults = shallowRef(false);
const activeCapacidadTab = shallowRef<string>('literal');
const activeTab = shallowRef<string>('generador');

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
    'LITERAL': 'bg-teal-100 text-teal-700 dark:bg-teal-900/30 dark:text-teal-400',
    'INFERENCIAL': 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
    'CRITICO': 'bg-violet-100 text-violet-700 dark:bg-violet-900/30 dark:text-violet-400'
  };
  return classes[nivel] || 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300';
};
</script>

<template>
  <div
    class="min-h-screen flex flex-col bg-gradient-to-br from-teal-50/50 via-amber-50/30 to-sky-50/50 dark:from-slate-950 dark:via-slate-900 dark:to-teal-950/30 transition-colors edu-pattern-bg">

    <!-- Decorative Background Elements - Tema Educativo -->
    <div class="fixed inset-0 overflow-hidden pointer-events-none">
      <!-- Círculos decorativos con colores educativos -->
      <div
        class="absolute -top-24 -right-24 w-96 h-96 bg-teal-200/40 dark:bg-teal-500/10 rounded-full blur-3xl animate-float">
      </div>
      <div class="absolute top-1/3 -left-24 w-80 h-80 bg-amber-200/40 dark:bg-amber-500/10 rounded-full blur-3xl"
        style="animation-delay: 2s;"></div>
      <div
        class="absolute bottom-0 right-1/4 w-72 h-72 bg-sky-200/30 dark:bg-sky-500/10 rounded-full blur-3xl animate-float"
        style="animation-delay: 4s;">
      </div>
      <div class="absolute top-2/3 left-1/3 w-64 h-64 bg-violet-200/20 dark:bg-violet-500/5 rounded-full blur-3xl">
      </div>
      <!-- Círculos adicionales -->
      <div
        class="absolute top-1/4 right-1/3 w-48 h-48 bg-rose-200/20 dark:bg-rose-500/5 rounded-full blur-3xl animate-float"
        style="animation-delay: 6s;">
      </div>
      <div class="absolute bottom-1/4 left-1/4 w-56 h-56 bg-emerald-200/25 dark:bg-emerald-500/5 rounded-full blur-3xl"
        style="animation-delay: 3.5s;">
      </div>

      <!-- Elementos decorativos educativos flotantes - Iconos -->
      <div class="absolute top-20 right-[15%] text-teal-400/40 dark:text-teal-500/25 animate-float">
        <BookOpen class="w-16 h-16" />
      </div>
      <div class="absolute top-[40%] left-[8%] text-amber-400/40 dark:text-amber-500/25 animate-float"
        style="animation-delay: 3s;">
        <Pencil class="w-12 h-12" />
      </div>
      <div class="absolute bottom-[20%] right-[10%] text-sky-400/40 dark:text-sky-500/25 animate-float"
        style="animation-delay: 1s;">
        <Star class="w-14 h-14" />
      </div>
      <div class="absolute bottom-[35%] left-[20%] text-violet-400/35 dark:text-violet-500/20 animate-float"
        style="animation-delay: 5s;">
        <GraduationCap class="w-10 h-10" />
      </div>
      <!-- Más iconos educativos -->
      <div class="absolute top-[15%] left-[25%] text-emerald-400/35 dark:text-emerald-500/20 animate-float"
        style="animation-delay: 2.5s;">
        <Calculator class="w-10 h-10" />
      </div>
      <div class="absolute top-[55%] right-[20%] text-rose-400/35 dark:text-rose-500/20 animate-float"
        style="animation-delay: 4.5s;">
        <Globe class="w-12 h-12" />
      </div>
      <div class="absolute bottom-[45%] right-[35%] text-amber-400/35 dark:text-amber-500/20 animate-float"
        style="animation-delay: 1.5s;">
        <Trophy class="w-9 h-9" />
      </div>
      <div class="absolute top-[70%] left-[12%] text-cyan-400/35 dark:text-cyan-500/20 animate-float"
        style="animation-delay: 6.5s;">
        <Atom class="w-11 h-11" />
      </div>
      <div class="absolute top-[30%] right-[8%] text-pink-400/35 dark:text-pink-500/20 animate-float"
        style="animation-delay: 3.5s;">
        <Palette class="w-10 h-10" />
      </div>
      <div class="absolute bottom-[15%] left-[40%] text-indigo-400/35 dark:text-indigo-500/20 animate-float"
        style="animation-delay: 7s;">
        <Layers class="w-8 h-8" />
      </div>
      <div class="absolute top-[85%] right-[25%] text-teal-400/30 dark:text-teal-500/18 animate-float"
        style="animation-delay: 5.5s;">
        <FileQuestion class="w-9 h-9" />
      </div>
      <div class="absolute top-[10%] left-[45%] text-amber-400/30 dark:text-amber-500/18 animate-float"
        style="animation-delay: 8s;">
        <Medal class="w-8 h-8" />
      </div>

      <!-- Nuevos iconos educativos flotantes -->
      <div class="absolute top-[5%] right-[40%] text-purple-400/35 dark:text-purple-500/20 animate-float"
        style="animation-delay: 2s;">
        <Music class="w-9 h-9" />
      </div>
      <div class="absolute top-[45%] left-[5%] text-blue-400/35 dark:text-blue-500/20 animate-float"
        style="animation-delay: 4s;">
        <Compass class="w-11 h-11" />
      </div>
      <div class="absolute top-[60%] right-[5%] text-green-400/35 dark:text-green-500/20 animate-float"
        style="animation-delay: 9s;">
        <Microscope class="w-12 h-12" />
      </div>
      <div class="absolute bottom-[8%] left-[15%] text-orange-400/35 dark:text-orange-500/20 animate-float"
        style="animation-delay: 6s;">
        <Ruler class="w-10 h-10" />
      </div>
      <div class="absolute top-[20%] left-[65%] text-red-400/30 dark:text-red-500/18 animate-float"
        style="animation-delay: 3s;">
        <PenTool class="w-8 h-8" />
      </div>
      <div class="absolute bottom-[55%] right-[45%] text-cyan-400/30 dark:text-cyan-500/18 animate-float"
        style="animation-delay: 7.5s;">
        <Shapes class="w-9 h-9" />
      </div>
      <div class="absolute top-[75%] left-[55%] text-lime-400/35 dark:text-lime-500/20 animate-float"
        style="animation-delay: 1.5s;">
        <Puzzle class="w-11 h-11" />
      </div>
      <div class="absolute bottom-[40%] left-[70%] text-fuchsia-400/35 dark:text-fuchsia-500/20 animate-float"
        style="animation-delay: 8.5s;">
        <Wand2 class="w-8 h-8" />
      </div>
      <div class="absolute top-[50%] right-[55%] text-sky-400/30 dark:text-sky-500/18 animate-float"
        style="animation-delay: 4.5s;">
        <Infinity class="w-10 h-10" />
      </div>
      <div class="absolute bottom-[25%] right-[60%] text-violet-400/30 dark:text-violet-500/18 animate-float"
        style="animation-delay: 10s;">
        <Sigma class="w-9 h-9" />
      </div>

      <!-- Círculos adicionales de fondo -->
      <div
        class="absolute top-[80%] left-[60%] w-40 h-40 bg-lime-300/25 dark:bg-lime-500/10 rounded-full blur-3xl animate-float"
        style="animation-delay: 5s;">
      </div>
      <div
        class="absolute top-[40%] right-[50%] w-52 h-52 bg-fuchsia-300/20 dark:bg-fuchsia-500/8 rounded-full blur-3xl"
        style="animation-delay: 7s;">
      </div>
    </div>

    <!-- Header Educativo -->
    <header
      class="bg-gradient-to-r from-teal-600 via-teal-500 to-sky-500 dark:from-slate-800 dark:via-slate-800 dark:to-slate-800 border-b border-teal-400/20 dark:border-slate-700 sticky top-0 z-50 shadow-lg shadow-teal-500/20 dark:shadow-none">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 py-3 sm:py-4">
        <div class="flex items-center justify-between gap-2">
          <div class="flex items-center gap-2 sm:gap-4">
            <!-- Logo con icono de libro -->
            <div class="relative flex-shrink-0">
              <div
                class="w-10 h-10 sm:w-14 sm:h-14 bg-white/90 backdrop-blur-sm rounded-xl sm:rounded-2xl flex items-center justify-center shadow-lg border border-white/30 p-1">
                <img :src="logoDre" alt="Logo DRE" class="w-full h-full object-contain" />
              </div>
              <!-- Estrella decorativa -->
              <div
                class="absolute -top-1 -right-1 w-4 h-4 sm:w-5 sm:h-5 bg-amber-400 rounded-full flex items-center justify-center shadow-md animate-pulse">
                <Star class="w-2 h-2 sm:w-3 sm:h-3 text-white fill-white" />
              </div>
            </div>
            <div class="min-w-0">
              <h1 class="text-lg sm:text-2xl font-bold text-white tracking-tight flex items-center gap-2 truncate">
                LectoSistem
                <span
                  class="text-[10px] sm:text-xs bg-amber-400 text-amber-900 px-2 py-0.5 rounded-full font-semibold">DRE</span>
              </h1>
              <p
                class="text-teal-100 dark:text-slate-400 text-[10px] sm:text-sm font-medium flex items-center gap-1 truncate">
                <GraduationCap class="w-3 h-3 sm:w-4 sm:h-4" />
                <span class="truncate">Lectura inteligente</span>
              </p>
            </div>
          </div>

          <!-- Mascota LECTOSISTEM -->
          <div class="hidden md:flex items-center">
            <div class="relative group">
              <img :src="mascotaLectosistem" alt="Mascota LECTOSISTEM"
                class="h-16 w-auto object-contain drop-shadow-lg transition-all duration-500 group-hover:scale-110 group-hover:drop-shadow-2xl animate-mascota-float" />
              <!-- Burbuja de diálogo -->
              <div
                class="absolute -top-2 -right-2 opacity-0 group-hover:opacity-100 transition-all duration-300 transform group-hover:translate-y-0 translate-y-2">
                <div
                  class="bg-white dark:bg-slate-700 rounded-full px-2 py-1 shadow-lg border-2 border-amber-300 dark:border-amber-500">
                  <span class="text-[10px] font-bold text-amber-600 dark:text-amber-400 whitespace-nowrap">¡Hola!
                    👋</span>
                </div>
              </div>
            </div>
          </div>

          <div class="flex items-center gap-2 sm:gap-3">
            <button v-if="resultado && !loading && activeTab === 'generador'" @click="showResults = !showResults"
              class="px-3 py-1.5 sm:px-4 sm:py-2 rounded-lg sm:rounded-xl font-medium text-[10px] sm:text-sm flex items-center gap-1.5 sm:gap-2 transition-all duration-300 bg-white/20 backdrop-blur-sm text-white border border-white/30 hover:bg-white/30">
              <Eye v-if="showResults" class="w-3 h-3 sm:w-4 sm:h-4" />
              <EyeOff v-else class="w-3 h-3 sm:w-4 sm:h-4" />
              <span class="hidden sm:inline">{{ showResults ? 'Ocultar' : 'Ver Resultado' }}</span>
              <span class="sm:hidden">{{ showResults ? 'Cerrar' : 'Ver' }}</span>
            </button>

            <button @click="toggleTheme"
              class="p-2.5 rounded-xl bg-white/20 backdrop-blur-sm text-white border border-white/30 hover:bg-white/30 dark:bg-slate-700 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-600 transition-all duration-300">
              <Sun v-if="isDark" class="w-5 h-5" />
              <Moon v-else class="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </header>

    <main class="flex-1 max-w-7xl mx-auto px-4 sm:px-6 py-4 sm:py-6 w-full">

      <!-- Tabs Navigation - Estilo Educativo -->
      <div class="mb-6 overflow-x-auto pb-2 scrollbar-hide">
        <div
          class="bg-white dark:bg-slate-800 rounded-2xl p-1.5 sm:p-2 shadow-lg border border-gray-100 dark:border-slate-700 flex sm:inline-flex gap-1 sm:gap-2 min-w-max">
          <button @click="activeTab = 'generador'"
            class="flex items-center gap-2 px-3 py-2 sm:px-5 sm:py-3 rounded-lg sm:rounded-xl font-semibold text-xs sm:text-sm transition-all duration-300 whitespace-nowrap"
            :class="activeTab === 'generador'
              ? 'bg-gradient-to-r from-teal-500 to-teal-600 text-white shadow-lg shadow-teal-500/30'
              : 'text-slate-600 dark:text-slate-400 hover:bg-teal-50 dark:hover:bg-slate-700'">
            <Brain class="w-4 h-4 sm:w-5 sm:h-5" />
            <span>Generador de Examen</span>
            <Sparkles v-if="activeTab === 'generador'" class="w-3 h-3 sm:w-4 sm:h-4 text-amber-300" />
          </button>

          <button @click="activeTab = 'sistematizador'"
            class="flex items-center gap-2 px-3 py-2 sm:px-5 sm:py-3 rounded-lg sm:rounded-xl font-semibold text-xs sm:text-sm transition-all duration-300 whitespace-nowrap"
            :class="activeTab === 'sistematizador'
              ? 'bg-gradient-to-r from-amber-500 to-orange-500 text-white shadow-lg shadow-amber-500/30'
              : 'text-slate-600 dark:text-slate-400 hover:bg-amber-50 dark:hover:bg-slate-700'">
            <LayoutGrid class="w-4 h-4 sm:w-5 sm:h-5" />
            <span>Sistematizador</span>
            <Award v-if="activeTab === 'sistematizador'" class="w-3 h-3 sm:w-4 sm:h-4 text-yellow-300" />
          </button>
        </div>
      </div>

      <!-- Generator Tab Content -->
      <div v-show="activeTab === 'generador'">
        <!-- Configuration Row - Diseño Educativo -->
        <div class="grid md:grid-cols-3 gap-4 mb-6">

          <!-- Grade Selection -->
          <div
            class="bg-white dark:bg-slate-800 rounded-2xl p-5 border-2 border-teal-100 dark:border-slate-700 shadow-sm hover:shadow-md hover:border-teal-200 transition-all duration-300">
            <label class="flex items-center gap-2 text-sm font-bold text-slate-700 dark:text-slate-300 mb-3">
              <div
                class="w-8 h-8 bg-gradient-to-br from-teal-400 to-teal-600 rounded-lg flex items-center justify-center">
                <GraduationCap class="w-4 h-4 text-white" />
              </div>
              Grado Escolar
            </label>
            <ComboBox v-model="selectedGradoId" :options="gradoOptions" placeholder="Seleccionar grado..." />
          </div>

          <!-- Quantity -->
          <div
            class="bg-white dark:bg-slate-800 rounded-2xl p-5 border-2 border-amber-100 dark:border-slate-700 shadow-sm hover:shadow-md hover:border-amber-200 transition-all duration-300">
            <label class="flex items-center gap-2 text-sm font-bold text-slate-700 dark:text-slate-300 mb-3">
              <div
                class="w-8 h-8 bg-gradient-to-br from-amber-400 to-amber-600 rounded-lg flex items-center justify-center">
                <Hash class="w-4 h-4 text-white" />
              </div>
              Cantidad de Preguntas
            </label>
            <div class="flex items-center gap-4">
              <input type="range" v-model="cantidadPreguntas" min="1" max="10"
                class="flex-1 h-3 bg-gradient-to-r from-teal-100 to-amber-100 dark:bg-slate-700 rounded-full appearance-none cursor-pointer accent-teal-600" />
              <span
                class="w-12 h-12 rounded-xl bg-gradient-to-br from-teal-500 to-teal-600 flex items-center justify-center text-xl font-bold text-white shadow-lg shadow-teal-500/30">
                {{ cantidadPreguntas }}
              </span>
            </div>
          </div>

          <!-- File Upload -->
          <div
            class="bg-white dark:bg-slate-800 rounded-2xl p-5 border-2 border-sky-100 dark:border-slate-700 shadow-sm hover:shadow-md hover:border-sky-200 transition-all duration-300">
            <Checkbox v-model="useTextoBase" class="items-center mb-3">
              <div class="flex items-center gap-2">
                <div
                  class="w-8 h-8 bg-gradient-to-br from-sky-400 to-sky-600 rounded-lg flex items-center justify-center">
                  <FileUp class="w-4 h-4 text-white" />
                </div>
                <span class="text-sm font-bold text-slate-700 dark:text-slate-300">Usar Texto Base</span>
              </div>
            </Checkbox>

            <div v-if="useTextoBase" class="space-y-2">
              <div v-if="selectedFiles.length === 0 && !uploadingFile" class="relative">
                <input type="file" accept=".pdf,.docx,.doc" multiple @change="handleFileUpload"
                  class="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10" />
                <div
                  class="flex items-center justify-center py-4 px-3 bg-gradient-to-br from-sky-50 to-teal-50 dark:bg-slate-900 border-2 border-dashed border-sky-300 dark:border-slate-600 rounded-xl hover:border-teal-400 hover:bg-teal-50 transition-all duration-300">
                  <div class="text-center">
                    <CloudUpload class="w-6 h-6 text-teal-500 mx-auto mb-1" />
                    <span class="text-teal-600 dark:text-slate-400 text-xs font-medium">📄 PDF o Word</span>
                  </div>
                </div>
              </div>

              <div v-if="uploadingFile"
                class="flex items-center justify-center gap-2 py-4 bg-teal-50 dark:bg-slate-900 rounded-xl">
                <Loader2 class="w-5 h-5 text-teal-600 animate-spin" />
                <span class="text-teal-600 dark:text-teal-400 text-sm font-medium">Procesando...</span>
              </div>

              <div v-if="selectedFiles.length > 0 && !uploadingFile && filesMetadata" class="space-y-2">
                <div v-for="(archivo, index) in filesMetadata.archivos" :key="index"
                  class="flex items-center gap-2 p-3 bg-gradient-to-r from-teal-50 to-emerald-50 dark:bg-emerald-900/20 border-2 border-teal-200 dark:border-emerald-800 rounded-xl text-xs">
                  <FileText class="w-5 h-5 text-teal-600 dark:text-emerald-400" />
                  <span class="flex-1 truncate text-slate-700 dark:text-slate-200 font-medium">{{ archivo.filename
                  }}</span>
                  <span class="text-teal-600 font-bold bg-teal-100 px-2 py-0.5 rounded-full">{{ archivo.palabras
                  }}p</span>
                </div>
                <button @click="clearFiles"
                  class="text-xs text-red-500 hover:text-red-600 flex items-center gap-1 font-medium">
                  <X class="w-3 h-3" /> Quitar archivo
                </button>
              </div>

              <div v-if="uploadError"
                class="p-3 bg-red-50 dark:bg-red-900/20 border-2 border-red-200 dark:border-red-800 rounded-xl">
                <p class="text-red-600 dark:text-red-400 text-xs flex items-center gap-1 font-medium">
                  <AlertTriangle class="w-4 h-4" />
                  {{ uploadError }}
                </p>
              </div>
            </div>

            <p v-else class="text-slate-400 dark:text-slate-500 text-xs mt-2 flex items-center gap-1">
              <BookOpen class="w-3 h-3" /> Activa para usar lectura personalizada
            </p>
          </div>
        </div>

        <!-- Main Content -->
        <div class="grid lg:grid-cols-2 gap-4 sm:gap-6">

          <!-- Left: Desempeños -->
          <div class="flex flex-col space-y-3 order-1 lg:order-1">

            <!-- Desempeños Card -->
            <div
              class="h-[500px] sm:h-[580px] lg:h-[650px] flex flex-col bg-white dark:bg-slate-800 rounded-2xl border-2 border-teal-100 dark:border-slate-700 overflow-hidden shadow-lg">

              <!-- Card Header - Educativo -->
              <div class="bg-gradient-to-r from-teal-500 via-teal-600 to-sky-500 px-5 py-4">
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-3">
                    <div
                      class="w-10 h-10 bg-white/20 backdrop-blur-sm rounded-xl flex items-center justify-center shadow-lg">
                      <Target class="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <h2 class="text-lg font-bold text-white">
                        Desempeños
                      </h2>
                      <span v-if="desempenos.length" class="text-xs text-teal-100 font-medium">
                        {{ desempenos.length }} disponibles para evaluar
                      </span>
                    </div>
                  </div>
                  <span v-if="selectedDesempenosCount > 0"
                    class="px-3 py-1.5 rounded-full bg-amber-400 text-amber-900 text-xs font-bold shadow-lg">
                    ✓ {{ selectedDesempenosCount }} seleccionados
                  </span>
                </div>
              </div>

              <!-- Loading -->
              <div v-if="loadingDesempenos" class="p-4 space-y-3">
                <div v-for="i in 3" :key="i" class="space-y-2">
                  <div class="h-4 w-24 bg-gray-200 dark:bg-slate-700 rounded animate-pulse"></div>
                  <div v-for="j in 2" :key="j"
                    class="flex items-start gap-2 p-2 bg-gray-50 dark:bg-slate-900 rounded-lg">
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

                <!-- Tab Navigation - Niveles de Comprensión -->
                <div class="flex overflow-x-auto scrollbar-hide bg-gray-50 dark:bg-slate-900 p-1.5 gap-1 min-w-full">
                  <button v-for="tipo in ['literal', 'inferencial', 'critico']" :key="tipo"
                    @click="activeCapacidadTab = tipo"
                    class="flex-1 min-w-[100px] relative px-2 sm:px-4 py-2 sm:py-2.5 text-[10px] sm:text-xs font-bold uppercase tracking-wide transition-all duration-300 rounded-lg whitespace-nowrap"
                    :class="activeCapacidadTab === tipo
                      ? {
                        'bg-teal-500 text-white shadow-lg shadow-teal-500/30': tipo === 'literal',
                        'bg-amber-500 text-white shadow-lg shadow-amber-500/30': tipo === 'inferencial',
                        'bg-violet-500 text-white shadow-lg shadow-violet-500/30': tipo === 'critico'
                      }
                      : 'text-slate-500 dark:text-slate-400 hover:bg-white dark:hover:bg-slate-800'">
                    <div class="flex items-center justify-center gap-1.5 sm:gap-2">
                      <BookOpen v-if="tipo === 'literal'" class="w-3 h-3 sm:w-4 h-4" />
                      <FileSearch v-else-if="tipo === 'inferencial'" class="w-3 h-3 sm:w-4 h-4" />
                      <Lightbulb v-else class="w-3 h-3 sm:w-4 h-4" />
                      <span>{{ getCapacidadLabel(tipo) }}</span>
                    </div>
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
                      <Checkbox v-for="des in desempenosPorCapacidad[activeCapacidadTab]" :key="des.id"
                        v-model="selectedDesempenoIds" :value="des.id"
                        class="group flex items-start gap-3 p-3 rounded-xl cursor-pointer transition-all duration-150 border"
                        :class="selectedDesempenoIds.includes(des.id)
                          ? {
                            'bg-emerald-50 dark:bg-emerald-900/20 border-emerald-200 dark:border-emerald-800 ring-1 ring-emerald-300 dark:ring-emerald-700': activeCapacidadTab === 'literal',
                            'bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800 ring-1 ring-amber-300 dark:ring-amber-700': activeCapacidadTab === 'inferencial',
                            'bg-purple-50 dark:bg-purple-900/20 border-purple-200 dark:border-purple-800 ring-1 ring-purple-300 dark:ring-purple-700': activeCapacidadTab === 'critico'
                          }
                          : 'border-gray-100 dark:border-slate-700 hover:border-gray-200 dark:hover:border-slate-600 hover:bg-gray-50 dark:hover:bg-slate-800/50'"
                        :color="activeCapacidadTab === 'literal'
                          ? 'checked:bg-emerald-600 checked:border-emerald-600 dark:checked:bg-emerald-500 dark:checked:border-emerald-500 focus:ring-emerald-500/50'
                          : (activeCapacidadTab === 'inferencial'
                            ? 'checked:bg-amber-600 checked:border-amber-600 dark:checked:bg-amber-500 dark:checked:border-amber-500 focus:ring-amber-500/50'
                            : 'checked:bg-purple-600 checked:border-purple-600 dark:checked:bg-purple-500 dark:checked:border-purple-500 focus:ring-purple-500/50')">
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
                      </Checkbox>
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

            <!-- Generate Button - Educativo -->
            <button @click="generarPreguntas"
              :disabled="loading || !selectedGradoId || selectedDesempenoIds.length === 0"
              class="w-full px-4 py-4 sm:px-6 sm:py-5 bg-gradient-to-r from-teal-500 via-teal-600 to-sky-500 hover:from-teal-600 hover:via-teal-700 hover:to-sky-600 text-white font-bold rounded-2xl transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 sm:gap-3 shadow-xl shadow-teal-500/30 hover:shadow-2xl hover:shadow-teal-500/40 hover:-translate-y-1 text-base sm:text-lg">
              <Loader2 v-if="loading" class="w-5 h-5 sm:w-6 sm:h-6 animate-spin" />
              <template v-else>
                <Rocket class="w-5 h-5 sm:w-6 sm:h-6" />
                <span>{{ loading ? 'Generando...' : 'Generar Examen con IA' }}</span>
              </template>
              <span v-if="loading" class="hidden sm:inline">Generando examen mágico...</span>
            </button>

            <!-- Error -->
            <div v-if="error"
              class="bg-red-50 dark:bg-red-900/20 border-2 border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 p-4 rounded-2xl text-sm flex items-start gap-3">
              <div
                class="w-10 h-10 bg-red-100 dark:bg-red-900/30 rounded-xl flex items-center justify-center flex-shrink-0">
                <AlertTriangle class="w-5 h-5" />
              </div>
              <p class="font-medium">{{ error }}</p>
            </div>

            <!-- Prompt Button - Educativo -->
            <button v-if="promptTexto" @click="showPromptModal = true"
              class="w-full px-5 py-4 bg-white dark:bg-slate-800 rounded-2xl border-2 border-amber-200 dark:border-slate-700 flex items-center justify-between hover:bg-amber-50 dark:hover:bg-slate-700 hover:border-amber-300 transition-all duration-300 group">
              <span class="text-slate-700 dark:text-slate-300 text-sm font-bold flex items-center gap-3">
                <div
                  class="w-10 h-10 bg-gradient-to-br from-amber-400 to-orange-500 rounded-xl flex items-center justify-center shadow-lg shadow-amber-500/20 group-hover:scale-110 transition-transform">
                  <Copy class="w-5 h-5 text-white" />
                </div>
                Ver Prompt Generado
              </span>
              <span
                class="text-xs text-amber-600 dark:text-slate-500 font-medium bg-amber-100 dark:bg-slate-700 px-3 py-1 rounded-full">Clic
                para copiar</span>
            </button>
          </div>

          <!-- Right: Results -->
          <div class="flex flex-col order-2 lg:order-2">

            <!-- Empty State -->
            <div v-if="!resultado && !loading"
              class="h-[300px] sm:h-[580px] lg:h-[650px] bg-white dark:bg-slate-800 rounded-xl border border-gray-200 dark:border-slate-700 text-center flex flex-col items-center justify-center shadow-sm p-6">
              <Zap class="w-10 h-10 sm:w-12 sm:h-12 text-gray-300 dark:text-slate-600 mb-4" />
              <h3 class="text-base sm:text-lg font-semibold text-slate-800 dark:text-white mb-2">Listo para generar</h3>
              <p class="text-slate-500 dark:text-slate-400 text-xs sm:text-sm max-w-xs">
                Selecciona los desempeños y genera tu examen con IA.
              </p>
            </div>

            <!-- Loading State -->
            <div v-if="loading"
              class="h-[400px] sm:h-[580px] lg:h-[650px] bg-white dark:bg-slate-800 rounded-xl border border-gray-200 dark:border-slate-700 text-center flex flex-col items-center justify-center shadow-sm p-6">
              <div
                class="w-10 h-10 sm:w-14 sm:h-14 border-4 border-gray-200 dark:border-slate-600 border-t-indigo-600 dark:border-t-indigo-400 rounded-full animate-spin mb-4">
              </div>
              <h3 class="text-base sm:text-lg font-semibold text-slate-800 dark:text-white mb-2">Generando Examen</h3>
              <p class="text-slate-500 dark:text-slate-400 text-xs sm:text-sm">Esto puede tomar unos segundos...</p>
            </div>

            <!-- Results -->
            <div v-if="resultado && !loading && showResults"
              class="h-[500px] sm:h-[580px] lg:h-[650px] bg-white dark:bg-slate-800 rounded-2xl border-2 border-amber-200 dark:border-slate-700 shadow-xl flex flex-col overflow-hidden">

              <!-- Results Header - Celebratorio -->
              <div
                class="bg-gradient-to-r from-amber-400 via-amber-500 to-orange-500 px-4 sm:px-5 py-3 sm:py-4 flex-shrink-0">
                <div class="flex flex-col sm:flex-row items-center justify-between gap-3">
                  <div class="flex items-center gap-3 w-full sm:w-auto">
                    <div
                      class="w-10 h-10 sm:w-12 sm:h-12 bg-white/20 backdrop-blur-sm rounded-xl sm:rounded-2xl flex items-center justify-center shadow-lg flex-shrink-0">
                      <Award class="w-5 h-5 sm:w-6 sm:h-6 text-white" />
                    </div>
                    <div class="min-w-0 flex-1">
                      <h2 class="text-base sm:text-lg font-bold text-white truncate">
                        {{ resultado.examen.titulo }}
                      </h2>
                      <span class="text-[10px] sm:text-xs text-amber-100 font-medium block">
                        {{ resultado.total_preguntas }} preguntas · {{ resultado.examen.grado }}
                      </span>
                    </div>
                  </div>
                  <button @click="descargarExamenWord" :disabled="descargandoWord"
                    class="w-full sm:w-auto px-4 py-2 bg-white text-amber-600 hover:bg-amber-50 text-xs sm:text-sm font-bold rounded-xl transition-all duration-300 flex items-center justify-center gap-2 shadow-lg hover:-translate-y-0.5">
                    <Loader2 v-if="descargandoWord" class="w-3 h-3 sm:w-4 sm:h-4 animate-spin" />
                    <Download v-else class="w-3 h-3 sm:w-4 sm:h-4" />
                    {{ descargandoWord ? 'Generando...' : 'Descargar Word' }}
                  </button>
                </div>
              </div>

              <!-- Scrollable Content -->
              <div class="flex-1 overflow-y-auto p-4 space-y-4">

                <!-- Instrucciones -->
                <div
                  class="bg-gradient-to-r from-teal-50 to-sky-50 dark:from-teal-900/40 dark:to-slate-900 rounded-xl p-4 border-2 border-teal-100 dark:border-teal-800">
                  <p class="text-slate-700 dark:text-slate-300 text-sm">
                    <strong class="text-teal-700 dark:text-teal-400 flex items-center gap-2 mb-2">
                      <ClipboardCheck class="w-4 h-4" />
                      Instrucciones:
                    </strong>
                    {{ resultado.examen.instrucciones }}
                  </p>
                </div>

                <!-- Lectura -->
                <div
                  class="bg-gradient-to-br from-amber-50 to-orange-50 dark:from-slate-900 dark:to-slate-950 rounded-xl p-5 border-2 border-amber-100 dark:border-slate-700">
                  <h4 class="text-sm font-bold text-slate-800 dark:text-white mb-3 flex items-center gap-2">
                    <div
                      class="w-8 h-8 bg-gradient-to-br from-amber-400 to-orange-500 rounded-lg flex items-center justify-center">
                      <BookOpen class="w-4 h-4 text-white" />
                    </div>
                    Lectura
                  </h4>
                  <p
                    class="text-slate-700 dark:text-slate-300 text-sm leading-7 whitespace-pre-line bg-white/50 dark:bg-black/20 p-4 rounded-lg">
                    {{ resultado.examen.lectura }}
                  </p>
                </div>

                <!-- Preguntas -->
                <div class="space-y-4">
                  <h4 class="text-sm font-bold text-slate-800 dark:text-white flex items-center gap-2">
                    <div
                      class="w-8 h-8 bg-gradient-to-br from-violet-400 to-purple-500 rounded-lg flex items-center justify-center">
                      <HelpCircle class="w-4 h-4 text-white" />
                    </div>
                    Preguntas del Examen
                  </h4>

                  <div v-for="pregunta in resultado.examen.preguntas" :key="pregunta.numero"
                    class="bg-white dark:bg-slate-800 rounded-xl p-5 border-2 border-slate-100 dark:border-slate-700 hover:border-teal-200 dark:hover:border-teal-700 transition-all duration-300">
                    <div class="flex items-start gap-4">
                      <span
                        class="w-10 h-10 bg-gradient-to-br from-teal-500 to-sky-500 rounded-xl flex items-center justify-center text-white font-bold text-sm flex-shrink-0 shadow-lg shadow-teal-500/20">
                        {{ pregunta.numero }}
                      </span>
                      <div class="flex-1">
                        <span
                          class="inline-flex items-center gap-1 px-3 py-1 text-[10px] font-bold uppercase rounded-full mb-2"
                          :class="getNivelBadgeClass(pregunta.nivel)">
                          <BookOpen v-if="pregunta.nivel === 'LITERAL'" class="w-3 h-3" />
                          <FileSearch v-else-if="pregunta.nivel === 'INFERENCIAL'" class="w-3 h-3" />
                          <Lightbulb v-else class="w-3 h-3" />
                          {{ pregunta.nivel }}
                        </span>
                        <p class="text-slate-800 dark:text-slate-200 font-semibold mb-4">{{ pregunta.enunciado }}</p>

                        <div class="space-y-2">
                          <div v-for="opcion in pregunta.opciones" :key="opcion.letra"
                            class="flex items-center gap-3 text-sm py-3 px-4 rounded-xl border-2 transition-all duration-200"
                            :class="opcion.es_correcta
                              ? 'bg-gradient-to-r from-teal-50 to-emerald-50 dark:from-emerald-900/40 dark:to-slate-900 border-teal-300 dark:border-emerald-800 text-teal-700 dark:text-emerald-400'
                              : 'bg-gray-50 dark:bg-slate-900 border-gray-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:border-gray-300'">
                            <span class="w-8 h-8 rounded-lg flex items-center justify-center font-bold text-sm"
                              :class="opcion.es_correcta ? 'bg-teal-500 text-white' : 'bg-gray-200 dark:bg-slate-700 text-slate-600 dark:text-slate-400'">{{
                                opcion.letra }}</span>
                            <span class="flex-1">{{ opcion.texto }}</span>
                            <Check v-if="opcion.es_correcta" class="w-5 h-5 text-teal-500" />
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Answer Table -->
                <div class="bg-white dark:bg-slate-800 rounded-xl p-5 border-2 border-sky-100 dark:border-slate-700">
                  <h4 class="text-sm font-bold text-slate-800 dark:text-white mb-4 flex items-center gap-2">
                    <div
                      class="w-8 h-8 bg-gradient-to-br from-sky-400 to-blue-500 rounded-lg flex items-center justify-center">
                      <LayoutGrid class="w-4 h-4 text-white" />
                    </div>
                    Tabla de Respuestas
                  </h4>
                  <div class="overflow-x-auto rounded-xl border-2 border-gray-100 dark:border-slate-700">
                    <table class="w-full text-sm">
                      <thead>
                        <tr
                          class="bg-gradient-to-r from-slate-50 to-gray-50 dark:from-slate-900 dark:to-slate-950 border-b-2 border-gray-200 dark:border-slate-700">
                          <th class="text-left py-3 px-4 text-slate-600 dark:text-slate-400 font-bold text-xs">#</th>
                          <th class="text-left py-3 px-4 text-slate-600 dark:text-slate-400 font-bold text-xs">
                            Desempeño
                          </th>
                          <th class="text-left py-3 px-4 text-slate-600 dark:text-slate-400 font-bold text-xs">Nivel
                          </th>
                          <th class="text-center py-3 px-4 text-slate-600 dark:text-slate-400 font-bold text-xs">Rpta.
                          </th>
                        </tr>
                      </thead>
                      <tbody class="divide-y divide-gray-100 dark:divide-slate-700">
                        <tr v-for="fila in resultado.examen.tabla_respuestas" :key="fila.pregunta"
                          class="hover:bg-gray-50 dark:hover:bg-slate-800/50 transition-colors">
                          <td class="py-3 px-4 text-slate-800 dark:text-slate-200 font-bold">{{ fila.pregunta }}
                          </td>
                          <td class="py-3 px-4 text-slate-600 dark:text-slate-400 text-xs">{{ fila.desempeno }}</td>
                          <td class="py-3 px-4">
                            <span class="px-2.5 py-1 text-[10px] font-bold rounded-full inline-flex items-center gap-1"
                              :class="getNivelBadgeClass(fila.nivel)">
                              <BookOpen v-if="fila.nivel === 'LITERAL'" class="w-3 h-3" />
                              <FileSearch v-else-if="fila.nivel === 'INFERENCIAL'" class="w-3 h-3" />
                              <Lightbulb v-else class="w-3 h-3" />
                              {{ fila.nivel }}
                            </span>
                          </td>
                          <td class="py-3 px-4 text-center">
                            <span
                              class="w-8 h-8 bg-gradient-to-br from-teal-400 to-teal-600 text-white rounded-lg inline-flex items-center justify-center font-bold text-sm shadow-lg shadow-teal-500/20">
                              {{ fila.respuesta_correcta }}
                            </span>
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>

                <p
                  class="text-center text-xs text-slate-500 dark:text-slate-400 bg-gradient-to-r from-teal-50 to-amber-50 dark:from-slate-900 dark:to-slate-800 p-3 rounded-xl flex items-center justify-center gap-2">
                  <Sparkles class="w-4 h-4 text-amber-500" /> Examen generado con IA - <strong>Revisar antes de usar con
                    los
                    estudiantes</strong>
                  <GraduationCap class="w-4 h-4 text-teal-500" />
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Sistematizador Tab Content -->
      <div v-show="activeTab === 'sistematizador'">
        <Sistematizador />
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
