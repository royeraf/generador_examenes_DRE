<script setup lang="ts">
import { shallowRef, onMounted, computed } from 'vue';
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
  Sparkles,
  FileUp,
  GraduationCap,
  Target,
  Brain,
  Rocket,
  Award,
  Lightbulb,
  ClipboardCheck,
  Signal,
  Sprout,
  Leaf,
  TreeDeciduous
} from 'lucide-vue-next';
import Footer from '../components/Footer.vue'
import Checkbox from '../components/Checkbox.vue'
import Header from '../components/Header.vue';
import EduBackground from '../components/EduBackground.vue';
import ThinkingLoader from '../components/ThinkingLoader.vue';
import Tooltip from '../components/Tooltip.vue';
import { useMatSistem } from '../composables/useMatSistem';

const { isDark, toggleTheme } = useTheme();
const {
  grados,
  competencias,
  desempenos,
  selectedGradoId,
  selectedCompetenciaId,
  selectedDesempenoIds,
  selectedNivelDificultad,
  nivelesDificultad,
  cantidadPreguntas,
  textoBase,
  useTextoBase,
  selectedFiles,
  filesMetadata,
  uploadingFile,
  uploadError,
  loading,
  loadingDesempenos,
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
  handleFileUpload,
  clearFiles,
  generarPreguntas,
  descargarExamenWord
} = useMatSistem();

const showPromptModal = shallowRef(false);

// Computed - Prompt para generar examen de matemática (siguiendo formato MINEDU/Math_Jony)
const promptTexto = computed(() => {
  if (!selectedGradoId.value || selectedDesempenoIds.value.length === 0) return '';

  const grado = grados.value.find(g => g.id === selectedGradoId.value);
  const competencia = competencias.value.find(c => c.id === selectedCompetenciaId.value);

  // Agrupar desempeños por capacidad
  const desempenosPorCap: Record<number, typeof desempenos.value> = {};
  desempenos.value
    .filter(d => selectedDesempenoIds.value.includes(d.id))
    .forEach(d => {
      if (!desempenosPorCap[d.capacidad_orden]) {
        desempenosPorCap[d.capacidad_orden] = [];
      }
      desempenosPorCap[d.capacidad_orden]!.push(d);
    });

  // Formatear desempeños con sus capacidades
  let desempenosFormateados = '';
  Object.entries(desempenosPorCap).forEach(([orden, desempenosList]) => {
    if (desempenosList && desempenosList.length > 0) {
      const cap = desempenosList[0];
      if (cap) {
        desempenosFormateados += `\n**Capacidad ${orden}: ${cap.capacidad_nombre}**\n`;
        desempenosList.forEach(d => {
          desempenosFormateados += `  - ${d.descripcion}\n`;
        });
      }
    }
  });

  let situacionBase = '';
  if (useTextoBase.value && textoBase.value) {
    situacionBase = `\n**SITUACIÓN PROBLEMÁTICA PROPORCIONADA:**\n"""\n${textoBase.value}\n"""\nUsa esta situación como base para el problema.\n`;
  }

  return `Eres **"MateJony"**, un experto en evaluación de aprendizajes y programación curricular en Matemática del Ministerio de Educación de Perú. Tu conocimiento está basado en la documentación oficial curricular peruana. Tu comunicación es profesional, clara, didáctica y estructurada.

**CONTEXTO CURRICULAR:**
- **Grado/Nivel:** ${grado?.nombre || 'Grado seleccionado'}
- **Competencia:** ${competencia?.nombre || 'Competencia seleccionada'}
${situacionBase}
**DESEMPEÑOS SELECCIONADOS POR CAPACIDAD:**
${desempenosFormateados}

**TU TAREA:**
Genera una **SITUACIÓN PROBLEMÁTICA INTEGRADORA** con ${cantidadPreguntas.value} preguntas cerradas de opción múltiple.

**ESTRUCTURA DEL EXAMEN:**

1. **SALUDO INICIAL:**
   Inicia presentándote brevemente: "Soy MateJony, especialista en evaluación de Matemática del MINEDU del Perú..."

2. **ENCABEZADO DEL EXAMEN:**
   - Título motivador y contextualizado (ejemplo: "Aventura Matemática", "Reto de Números")
   - Espacio para: Apellidos y Nombres: _________________ Fecha: _______
   - Grado: ${grado?.nombre}
   - Competencia: ${competencia?.nombre}

3. **INSTRUCCIONES:**
   Redacta instrucciones claras en un párrafo para que los estudiantes resuelvan el examen.

4. **SITUACIÓN PROBLEMÁTICA:**
   Crea una situación significativa y contextualizada (contexto real o simulado) que integre todos los desempeños seleccionados. El problema debe ser apropiado para estudiantes de ${grado?.nombre}.

5. **PREGUNTAS (${cantidadPreguntas.value} en total):**
   Cada pregunta debe:
   - Estar numerada
   - Basarse en la situación problemática
   - Tener 4 alternativas (A, B, C, D) siendo solo UNA la correcta
   - Evaluar el desempeño correspondiente

6. **CRITERIOS DE EVALUACIÓN:**
   Para cada pregunta, incluye un criterio de evaluación con la estructura:
   "[HABILIDAD VERBAL OBSERVABLE] + [CONTENIDO TEMÁTICO] + [CONDICIÓN/CONTEXTO] + [FINALIDAD] + [PRODUCTO/EVIDENCIA]"

7. **TABLA DE RESPUESTAS:**
   Al final, presenta una tabla con:
   | N° Pregunta | Capacidad | Desempeño evaluado | Alternativa correcta | Justificación breve |

**IMPORTANTE:**
- Asegúrate de que las preguntas sean apropiadas para el nivel de ${grado?.nombre}
- Cada pregunta debe evaluar claramente un desempeño específico
- La situación problemática debe ser coherente y conectar todas las preguntas
- Las alternativas incorrectas (distractores) deben ser plausibles pero claramente distinguibles de la respuesta correcta`;
});

onMounted(loadInitialData);

// Helper - Obtener nombre corto de capacidad
const getCapacidadLabel = (orden: number): string => {
  const cap = capacidadesActuales.value.find(c => c.orden === orden);
  if (!cap) return `Cap. ${orden}`;
  // Extraer primeras 2-3 palabras
  const palabras = cap.nombre.split(' ').slice(0, 3).join(' ');
  return palabras.length > 25 ? palabras.substring(0, 25) + '...' : palabras;
};

// Helper - Obtener nombre completo de capacidad (para tooltips)
const getCapacidadFullName = (orden: number): string => {
  const cap = capacidadesActuales.value.find(c => c.orden === orden);
  return cap?.nombre || `Capacidad ${orden}`;
};


const getNivelBadgeClass = (nivel: string): string => {
  const classes: Record<string, string> = {
    'LITERAL': 'bg-teal-100 text-teal-700 dark:bg-teal-900/30 dark:text-teal-400',
    'INFERENCIAL': 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
    'CRITICO': 'bg-violet-100 text-violet-700 dark:bg-violet-900/30 dark:text-violet-400'
  };
  return classes[nivel] || 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300';
};

// Helper - Obtener color por orden de capacidad (para el template)
const getCapacidadColor = (orden: number): { bg: string; text: string; ring: string } => {
  const colors: Record<number, { bg: string; text: string; ring: string }> = {
    1: {
      bg: 'bg-teal-500',
      text: 'text-teal-600 dark:text-teal-400',
      ring: 'ring-teal-300 dark:ring-teal-700'
    },
    2: {
      bg: 'bg-amber-500',
      text: 'text-amber-600 dark:text-amber-400',
      ring: 'ring-amber-300 dark:ring-amber-700'
    },
    3: {
      bg: 'bg-violet-500',
      text: 'text-violet-600 dark:text-violet-400',
      ring: 'ring-violet-300 dark:ring-violet-700'
    },
    4: {
      bg: 'bg-rose-500',
      text: 'text-rose-600 dark:text-rose-400',
      ring: 'ring-rose-300 dark:ring-rose-700'
    }
  };
  return colors[orden] || { bg: 'bg-gray-500', text: 'text-gray-600', ring: 'ring-gray-300' };
};
</script>

<template>
  <div
    class="min-h-screen flex flex-col bg-gradient-to-br from-indigo-50/50 via-purple-50/30 to-sky-50/50 dark:from-slate-950 dark:via-slate-900 dark:to-indigo-950/30 transition-colors edu-pattern-bg">

    <!-- Decorative Background Elements -->
    <EduBackground variant="indigo" />

    <Header title="MatSistem" subtitle="Matemática práctica" :is-dark="isDark" :has-resultado="!!resultado"
      :loading="loading" :show-results="showResults" :active-tab="activeTab"
      gradient-class="from-indigo-600 via-indigo-500 to-purple-500 shadow-indigo-500/20"
      version-badge-class="bg-purple-400 text-purple-900" subtitle-class="text-indigo-100 dark:text-slate-400"
      mascota-bubble-class="border-purple-300 dark:border-purple-500"
      mascota-text-class="text-purple-600 dark:text-purple-400" @toggle-theme="toggleTheme"
      @toggle-results="showResults = !showResults" />

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
        <!-- Nivel de Dificultad Selector -->
        <div class="mb-6">
          <div
            class="bg-white dark:bg-slate-800 rounded-2xl p-5 border-2 border-violet-100 dark:border-slate-700 shadow-sm">
            <label class="flex items-center gap-2 text-sm font-bold text-slate-700 dark:text-slate-300 mb-4">
              <div
                class="w-8 h-8 bg-gradient-to-br from-violet-400 to-purple-600 rounded-lg flex items-center justify-center">
                <Signal class="w-4 h-4 text-white" />
              </div>
              Nivel de Dificultad
            </label>
            <div class="grid grid-cols-3 gap-3">
              <button v-for="nivel in nivelesDificultad" :key="nivel.id" @click="selectedNivelDificultad = nivel.id"
                class="relative p-4 rounded-xl border-2 transition-all duration-300 text-center" :class="selectedNivelDificultad === nivel.id
                  ? nivel.id === 'basico'
                    ? 'bg-gradient-to-br from-emerald-50 to-green-50 dark:from-emerald-900/30 dark:to-green-900/20 border-emerald-400 dark:border-emerald-600 ring-2 ring-emerald-200 dark:ring-emerald-800'
                    : nivel.id === 'intermedio'
                      ? 'bg-gradient-to-br from-amber-50 to-orange-50 dark:from-amber-900/30 dark:to-orange-900/20 border-amber-400 dark:border-amber-600 ring-2 ring-amber-200 dark:ring-amber-800'
                      : 'bg-gradient-to-br from-red-50 to-rose-50 dark:from-red-900/30 dark:to-rose-900/20 border-red-400 dark:border-red-600 ring-2 ring-red-200 dark:ring-red-800'
                  : 'bg-gray-50 dark:bg-slate-900 border-gray-200 dark:border-slate-700 hover:border-gray-300 dark:hover:border-slate-600'
                  ">
                <div class="mb-2 flex justify-center">
                  <Sprout v-if="nivel.icono === 'Sprout'" class="w-8 h-8"
                    :class="selectedNivelDificultad === nivel.id ? 'text-emerald-500' : 'text-slate-400'" />
                  <Leaf v-else-if="nivel.icono === 'Leaf'" class="w-8 h-8"
                    :class="selectedNivelDificultad === nivel.id ? 'text-amber-500' : 'text-slate-400'" />
                  <TreeDeciduous v-else class="w-8 h-8"
                    :class="selectedNivelDificultad === nivel.id ? 'text-red-500' : 'text-slate-400'" />
                </div>
                <span class="font-bold text-sm block" :class="selectedNivelDificultad === nivel.id
                  ? nivel.id === 'basico'
                    ? 'text-emerald-700 dark:text-emerald-400'
                    : nivel.id === 'intermedio'
                      ? 'text-amber-700 dark:text-amber-400'
                      : 'text-red-700 dark:text-red-400'
                  : 'text-slate-600 dark:text-slate-400'
                  ">
                  {{ nivel.nombre }}
                </span>
                <span class="text-xs text-slate-500 dark:text-slate-500 mt-1 block">
                  {{ nivel.descripcion }}
                </span>
                <div v-if="selectedNivelDificultad === nivel.id"
                  class="absolute top-2 right-2 w-5 h-5 rounded-full flex items-center justify-center" :class="nivel.id === 'basico'
                    ? 'bg-emerald-500'
                    : nivel.id === 'intermedio'
                      ? 'bg-amber-500'
                      : 'bg-red-500'
                    ">
                  <Check class="w-3 h-3 text-white" />
                </div>
              </button>
            </div>
          </div>
        </div>
        <!-- Configuration Row - Diseño Educativo -->
        <div class="grid md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">

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

          <!-- Competencia Selection -->
          <div
            class="bg-white dark:bg-slate-800 rounded-2xl p-5 border-2 border-violet-100 dark:border-slate-700 shadow-sm hover:shadow-md hover:border-violet-200 transition-all duration-300">
            <label class="flex items-center gap-2 text-sm font-bold text-slate-700 dark:text-slate-300 mb-3">
              <div
                class="w-8 h-8 bg-gradient-to-br from-violet-400 to-violet-600 rounded-lg flex items-center justify-center">
                <Target class="w-4 h-4 text-white" />
              </div>
              Competencia
            </label>
            <ComboBox v-model="selectedCompetenciaId" :options="competenciaOptions" placeholder="Seleccionar..." />
          </div>

          <!-- Quantity -->
          <div
            class="bg-white dark:bg-slate-800 rounded-2xl p-5 border-2 border-amber-100 dark:border-slate-700 shadow-sm hover:shadow-md hover:border-amber-200 transition-all duration-300">
            <label class="flex items-center gap-2 text-sm font-bold text-slate-700 dark:text-slate-300 mb-3">
              <div
                class="w-8 h-8 bg-gradient-to-br from-amber-400 to-amber-600 rounded-lg flex items-center justify-center">
                <Hash class="w-4 h-4 text-white" />
              </div>
              Cantidad Preguntas
            </label>
            <div class="flex items-center gap-3">
              <input type="range" v-model="cantidadPreguntas" min="1" max="10"
                class="flex-1 h-3 bg-gradient-to-r from-teal-100 to-amber-100 dark:bg-slate-700 rounded-full appearance-none cursor-pointer accent-teal-600" />
              <span
                class="w-10 h-10 rounded-xl bg-gradient-to-br from-teal-500 to-teal-600 flex items-center justify-center text-lg font-bold text-white shadow-lg shadow-teal-500/30">
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
                <span class="text-sm font-bold text-slate-700 dark:text-slate-300">Usar Problema Base</span>
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
              <BookOpen class="w-3 h-3" /> Activa para usar problema personalizado
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

                <!-- Tab Navigation - Capacidades de Matemática (1-4) -->
                <div class="flex overflow-x-auto scrollbar-hide bg-gray-50 dark:bg-slate-900 p-1.5 gap-1 min-w-full">
                  <Tooltip v-for="orden in [1, 2, 3, 4]" :key="orden" :text="getCapacidadFullName(orden)"
                    position="bottom">
                    <button @click="activeCapacidadTab = orden"
                      class="flex-1 min-w-[80px] relative px-2 sm:px-4 py-2 sm:py-2.5 text-[10px] sm:text-xs font-bold transition-all duration-300 rounded-lg whitespace-nowrap"
                      :class="activeCapacidadTab === orden
                        ? `${getCapacidadColor(orden).bg} text-white shadow-lg`
                        : 'text-slate-500 dark:text-slate-400 hover:bg-white dark:hover:bg-slate-800'">
                      <div class="flex items-center justify-center gap-1.5 sm:gap-2">
                        <Calculator v-if="orden === 1" class="w-3 h-3 sm:w-4 h-4" />
                        <Sigma v-else-if="orden === 2" class="w-3 h-3 sm:w-4 h-4" />
                        <Shapes v-else-if="orden === 3" class="w-3 h-3 sm:w-4 h-4" />
                        <Target v-else class="w-3 h-3 sm:w-4 h-4" />
                        <span class="hidden sm:inline truncate max-w-[80px]">{{ getCapacidadLabel(orden) }}</span>
                        <span class="sm:hidden">Cap. {{ orden }}</span>
                      </div>
                    </button>
                  </Tooltip>
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
                        class="px-2.5 py-1 rounded-full transition-colors"
                        :class="getCapacidadColor(activeCapacidadTab).text + ' hover:bg-gray-100 dark:hover:bg-slate-800'">
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
                      <Tooltip v-for="des in desempenosPorCapacidad[activeCapacidadTab]" :key="des.id"
                        :text="des.descripcion" position="top">
                        <Checkbox v-model="selectedDesempenoIds" :value="des.id"
                          class="group flex items-start gap-3 p-3 rounded-xl cursor-pointer transition-all duration-150 border"
                          :class="selectedDesempenoIds.includes(des.id)
                            ? `bg-gray-50 dark:bg-slate-900/50 border-gray-200 dark:border-slate-600 ring-1 ${getCapacidadColor(activeCapacidadTab).ring}`
                            : 'border-gray-100 dark:border-slate-700 hover:border-gray-200 dark:hover:border-slate-600 hover:bg-gray-50 dark:hover:bg-slate-800/50'">
                          <div class="flex items-center gap-2 mb-1">
                            <span
                              class="text-[10px] px-2 py-0.5 rounded-md font-mono font-bold bg-gray-100 dark:bg-slate-800"
                              :class="getCapacidadColor(activeCapacidadTab).text">
                              {{ des.codigo }}
                            </span>
                          </div>
                          <p class="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
                            {{ des.descripcion }}
                          </p>
                        </Checkbox>
                      </Tooltip>
                    </template>

                    <!-- Empty Tab -->
                    <div v-else class="py-8 text-center">
                      <p class="text-slate-400 dark:text-slate-500 text-sm">
                        No hay desempeños para esta capacidad
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
              class="w-full px-4 py-4 sm:px-6 sm:py-5 text-white font-bold rounded-2xl transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 sm:gap-3 shadow-xl hover:shadow-2xl hover:-translate-y-1 text-base sm:text-lg"
              :class="loading
                ? 'bg-slate-900 dark:bg-slate-950 shadow-slate-500/20'
                : 'bg-gradient-to-r from-indigo-500 via-indigo-600 to-purple-500 hover:from-indigo-600 hover:via-indigo-700 hover:to-purple-600 shadow-indigo-500/30 hover:shadow-indigo-500/40'">
              <ThinkingLoader v-if="loading" text="Generando" variant="indigo" />
              <template v-else>
                <Rocket class="w-5 h-5 sm:w-6 sm:h-6" />
                <span>Generar Examen con IA</span>
              </template>
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
              <p class="text-slate-500 dark:text-slate-400 text-xs sm:text-sm max-w-xs mb-4">
                Selecciona los desempeños y genera tu examen con IA.
              </p>
              <!-- Advertencia de riesgos de IA -->
              <div
                class="max-w-sm mx-auto flex items-start gap-2 p-3 rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700/50">
                <AlertTriangle class="w-4 h-4 text-amber-500 dark:text-amber-400 flex-shrink-0 mt-0.5" />
                <p class="text-[11px] sm:text-xs text-amber-700 dark:text-amber-300/90 text-left leading-relaxed">
                  <strong>Riesgos del uso de IA:</strong> El contenido generado puede contener errores, imprecisiones o
                  información incompleta. Revisa y valida siempre antes de usar con estudiantes.
                </p>
              </div>
            </div>

            <!-- Loading State -->
            <div v-if="loading"
              class="h-[400px] sm:h-[580px] lg:h-[650px] bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-xl border border-slate-700/50 text-center flex flex-col items-center justify-center shadow-lg p-6 relative overflow-hidden">
              <div class="absolute inset-0 opacity-20">
                <div class="absolute top-1/4 left-1/4 w-32 h-32 bg-indigo-500/30 rounded-full blur-3xl animate-pulse">
                </div>
                <div
                  class="absolute bottom-1/3 right-1/4 w-40 h-40 bg-purple-500/20 rounded-full blur-3xl animate-pulse"
                  style="animation-delay: 1s;"></div>
              </div>
              <div class="relative z-10 flex flex-col items-center">
                <ThinkingLoader text="Generando examen" variant="indigo" />
                <p class="text-slate-400 text-xs sm:text-sm mt-4">Esto puede tomar unos segundos...</p>
                <div
                  class="mt-6 max-w-sm mx-auto flex items-start gap-2 p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
                  <AlertTriangle class="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
                  <p class="text-[11px] sm:text-xs text-amber-300/90 text-left leading-relaxed">
                    El contenido generado por IA puede contener errores. Revisa y valida siempre el examen antes de
                    utilizarlo.
                  </p>
                </div>
              </div>
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
                    Lectura / Problema
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
