<script setup lang="ts">
import { shallowRef, onMounted, computed, watch, provide } from 'vue';
import { useRouter } from 'vue-router';
import PromptModal from '../components/PromptModal.vue';
import Sistematizador from '../components/Sistematizador.vue';
import Footer from '../components/Footer.vue';
import { useTheme } from '../composables/useTheme';
import { useLectoSistem } from '../composables/useLectoSistem';
import { useExamHistory } from '../composables/useExamHistory';
import { showDeleteConfirm, Toast } from '../utils/swal';
import {
  Brain,
  Sparkles,
  LayoutGrid,
  Award,
  History,
  Trash2,
  Eye,
  Link,
  Clock,
  GraduationCap,
  FileText,
  Home,
} from 'lucide-vue-next';

const router = useRouter();
import Header from '../components/Header.vue';
import EduBackground from '../components/EduBackground.vue';
import LectoSistemConfig from '../components/lectosistem/LectoSistemConfig.vue';
import LectoSistemDesempenos from '../components/lectosistem/LectoSistemDesempenos.vue';
import LectoSistemResults from '../components/lectosistem/LectoSistemResults.vue';
import ExamPreviewModal from '../components/lectosistem/ExamPreviewModal.vue';
import type { ExamenHistoryEntry, FilaTablaRespuestas } from '../types';


const { isDark, toggleTheme } = useTheme();
const {
  grados,
  desempenos,
  selectedGradoId,
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
  activeTab,
  selectedDesempenosCount,
  gradoOptions,
  loadInitialData,
  handleFileUpload,
  clearFiles,
  generarPreguntas,
  descargarExamenWord,
  selectAllCapacidad,
  deselectAllCapacidad,
  activeCapacidadTab,
  desempenosPorCapacidad,
  selectedTipoTextual,
  selectedFormatoTextual,
  tipoTextualOptions,
  formatoTextualOptions,
  cantidadLiteral,
  cantidadInferencial,
  cantidadCritico,
  isBreakdownValid,
  totalBreakdown
} = useLectoSistem();

const { history, saveExam, removeExam, clearHistory } = useExamHistory();

// Provide for Sistematizador linkage
const examForSistematizador = shallowRef<{ tablaRespuestas: FilaTablaRespuestas[]; gradoId: number | null } | null>(null);
provide('examForSistematizador', examForSistematizador);

const showPromptModal = shallowRef(false);
const previewEntry = shallowRef<ExamenHistoryEntry | null>(null);

// Auto-save exams to history
watch(resultado, (newVal) => {
  if (newVal) {
    const grado = grados.value.find(g => g.id === selectedGradoId.value);
    saveExam(newVal, grado?.nombre || newVal.grado);
  }
});

// Vincular with sistematizador
function vincularConSistematizador() {
  if (resultado.value?.examen.tabla_respuestas) {
    examForSistematizador.value = {
      tablaRespuestas: resultado.value.examen.tabla_respuestas,
      gradoId: selectedGradoId.value,
    };
    activeTab.value = 'sistematizador';
  }
}

function vincularDesdeHistorial(index: number) {
  const entry = history.value[index];
  if (entry?.resultado.examen.tabla_respuestas) {
    examForSistematizador.value = {
      tablaRespuestas: entry.resultado.examen.tabla_respuestas,
      gradoId: null,
    };
    activeTab.value = 'sistematizador';
  }
}

function cargarExamen(index: number) {
  const entry = history.value[index];
  if (entry) {
    previewEntry.value = entry;
  }
}

function onPreviewVincular() {
  if (previewEntry.value?.resultado.examen.tabla_respuestas) {
    examForSistematizador.value = {
      tablaRespuestas: previewEntry.value.resultado.examen.tabla_respuestas,
      gradoId: null,
    };
    previewEntry.value = null;
    activeTab.value = 'sistematizador';
  }
}

async function onPreviewEliminar() {
  if (!previewEntry.value) return;
  const confirmed = await showDeleteConfirm('¿Eliminar este examen?', 'Se eliminará del historial');
  if (confirmed) {
    removeExam(previewEntry.value.id);
    previewEntry.value = null;
    Toast.fire({ icon: 'success', title: 'Examen eliminado' });
  }
}

async function confirmarEliminar(id: string) {
  const confirmed = await showDeleteConfirm('¿Eliminar este examen?', 'Se eliminará del historial');
  if (confirmed) {
    removeExam(id);
    Toast.fire({ icon: 'success', title: 'Examen eliminado' });
  }
}

async function confirmarLimpiarHistorial() {
  const confirmed = await showDeleteConfirm('¿Limpiar todo el historial?', 'Se eliminarán todos los exámenes guardados');
  if (confirmed) {
    clearHistory();
    Toast.fire({ icon: 'success', title: 'Historial limpiado' });
  }
}

function formatFecha(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString('es-PE', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}

const promptTexto = computed(() => {
  if (!selectedGradoId.value || selectedDesempenoIds.value.length === 0) return '';

  const grado = grados.value.find(g => g.id === selectedGradoId.value);
  const desempenosText = desempenos.value
    .filter(d => selectedDesempenoIds.value.includes(d.id))
    .map(d => `- ${d.descripcion}`)
    .join('\n');

  let situacionBase = '';
  if (useTextoBase.value && textoBase.value) {
    situacionBase = `\n**TEXTO BASE PROPORCIONADO:**\n"""\n${textoBase.value}\n"""\nUsa este texto como base para la lectura.\n`;
  }

  return `Eres **"Especialista MINEDU"**, un experto en comprensión lectora y el Currículo Nacional de Educación Básica de Perú. Tu conocimiento está basado en la documentación oficial del Ministerio de Educación (MINEDU). Tu comunicación es profesional, clara, didáctica y estructurada.

**CONTEXTO:**
- **Grado:** ${grado?.nombre || 'Grado seleccionado'}
${situacionBase}
**DESEMPEÑOS A EVALUAR:**
${desempenosText}

**TU TAREA:**
Genera un examen de comprensión lectora con una lectura original y ${cantidadPreguntas.value} preguntas cerradas de opción múltiple.

**ESTRUCTURA DEL EXAMEN:**

1. **SALUDO INICIAL:**
   Inicia presentándote brevemente: "Soy Especialista MINEDU, experto en evaluación de comprensión lectora del Ministerio de Educación del Perú..."

2. **ENCABEZADO DEL EXAMEN:**
   - Título motivador y contextualizado
   - Espacio para: Apellidos y Nombres: _________________ Fecha: _______
   - Grado: ${grado?.nombre}

3. **INSTRUCCIONES:**
   Redacta instrucciones claras en un párrafo.

4. **LECTURA:**
   Crea una lectura (cuento, noticia, artículo, etc.) coherente y apropiada para estudiantes de ${grado?.nombre}.

5. **PREGUNTAS (${cantidadPreguntas.value} en total):**
   Cada pregunta debe:
   - Estar numerada
   - Tener 4 alternativas (A, B, C, D) siendo solo UNA la correcta
   - Evaluar el desempeño correspondiente

6. **CRITERIOS DE EVALUACIÓN:**
   Para cada pregunta, incluye un criterio de evaluación con la estructura:
   "[HABILIDAD VERBAL OBSERVABLE] + [CONTENIDO TEMÁTICO] + [CONDICIÓN/CONTEXTO] + [FINALIDAD] + [PRODUCTO/EVIDENCIA]"

7. **TABLA DE RESPUESTAS:**
   Al final, presenta una tabla con:
   | N° Pregunta | Desempeño evaluado | Alternativa correcta | Justificación breve |

**IMPORTANTE:**
- Asegúrate de que las preguntas sean apropiadas para el nivel de ${grado?.nombre}
- Cada pregunta debe evaluar claramente un desempeño específico
- La lectura debe ser coherente y de una extensión moderada`;
});

onMounted(loadInitialData);
</script>

<template>
  <div
    class="min-h-screen flex flex-col bg-gradient-to-br from-teal-50/50 via-amber-50/30 to-sky-50/50 dark:from-slate-950 dark:via-slate-900 dark:to-teal-950/30 transition-colors edu-pattern-bg">

    <!-- Decorative Background Elements -->
    <EduBackground variant="teal" />

    <Header title="LectoSistem" subtitle="Lectura inteligente" :is-dark="isDark" :has-resultado="!!resultado"
      :loading="loading" :show-results="showResults" :active-tab="activeTab" @toggle-theme="toggleTheme"
      @toggle-results="showResults = !showResults">
      <template #actions-before>
        <button @click="router.push('/')"
          class="p-2.5 rounded-xl bg-white/20 backdrop-blur-sm text-white border border-white/30 hover:bg-white/30 dark:bg-slate-700 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-600 transition-all duration-300"
          title="Inicio">
          <Home class="w-5 h-5" />
        </button>
      </template>
    </Header>

    <main class="flex-1 max-w-7xl mx-auto px-4 sm:px-6 py-4 sm:py-6 w-full">

      <!-- Tabs Navigation -->
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

          <button @click="activeTab = 'historial'"
            class="flex items-center gap-2 px-3 py-2 sm:px-5 sm:py-3 rounded-lg sm:rounded-xl font-semibold text-xs sm:text-sm transition-all duration-300 whitespace-nowrap"
            :class="activeTab === 'historial'
              ? 'bg-gradient-to-r from-sky-500 to-blue-600 text-white shadow-lg shadow-sky-500/30'
              : 'text-slate-600 dark:text-slate-400 hover:bg-sky-50 dark:hover:bg-slate-700'">
            <History class="w-4 h-4 sm:w-5 sm:h-5" />
            <span>Historial</span>
            <span v-if="history.length > 0" class="ml-1 px-1.5 py-0.5 text-[10px] font-bold rounded-full"
              :class="activeTab === 'historial' ? 'bg-white/20 text-white' : 'bg-sky-100 text-sky-600 dark:bg-sky-900/30 dark:text-sky-400'">
              {{ history.length }}
            </span>
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

        <!-- Configuration Row -->
        <LectoSistemConfig :niveles-dificultad="nivelesDificultad"
          v-model:modelo-nivel-dificultad="selectedNivelDificultad" :grado-options="gradoOptions"
          v-model:modelo-grado-id="selectedGradoId" v-model:modelo-cantidad-preguntas="cantidadPreguntas"
          v-model:modelo-use-texto-base="useTextoBase" :selected-files="selectedFiles" :files-metadata="filesMetadata"
          :uploading-file="uploadingFile" :upload-error="uploadError" @file-upload="handleFileUpload"
          @clear-files="clearFiles" :tipo-textual-options="tipoTextualOptions"
          v-model:modelo-tipo-textual="selectedTipoTextual" :formato-textual-options="formatoTextualOptions"
          v-model:modelo-formato-textual="selectedFormatoTextual" v-model:modelo-cantidad-literal="cantidadLiteral"
          v-model:modelo-cantidad-inferencial="cantidadInferencial" v-model:modelo-cantidad-critico="cantidadCritico"
          :is-breakdown-valid="isBreakdownValid" :total-breakdown="totalBreakdown" />

        <!-- Main Content -->
        <div class="grid lg:grid-cols-2 gap-4 sm:gap-6">

          <!-- Left: Desempeños -->
          <LectoSistemDesempenos :desempenos="desempenos" :selected-desempenos-count="selectedDesempenosCount"
            :loading-desempenos="loadingDesempenos" :selected-grado-id="selectedGradoId"
            v-model:active-capacidad-tab="activeCapacidadTab" :desempenos-por-capacidad="desempenosPorCapacidad"
            v-model:selected-desempeno-ids="selectedDesempenoIds" :loading="loading" :error="error"
            :prompt-texto="promptTexto" v-model:show-prompt-modal="showPromptModal"
            @select-all-capacidad="selectAllCapacidad" @deselect-all-capacidad="deselectAllCapacidad"
            @generar-preguntas="generarPreguntas" :is-breakdown-valid="isBreakdownValid" />

          <!-- Right: Results -->
          <LectoSistemResults :resultado="resultado" :loading="loading" :show-results="showResults"
            :descargando-word="descargandoWord" @descargar-word="descargarExamenWord"
            @vincular-sistematizador="vincularConSistematizador" />
        </div>
      </div>

      <!-- History Tab Content -->
      <div v-show="activeTab === 'historial'">
        <!-- Empty History -->
        <div v-if="history.length === 0"
          class="bg-white dark:bg-slate-800 rounded-2xl border border-gray-200 dark:border-slate-700 shadow-sm p-12 text-center">
          <History class="w-12 h-12 text-gray-300 dark:text-slate-600 mx-auto mb-4" />
          <h3 class="text-lg font-semibold text-slate-800 dark:text-white mb-2">Sin exámenes guardados</h3>
          <p class="text-slate-500 dark:text-slate-400 text-sm max-w-md mx-auto">
            Los exámenes que generes se guardarán automáticamente aquí para que puedas consultarlos o vincularlos con el
            sistematizador.
          </p>
        </div>

        <!-- History List -->
        <div v-else class="space-y-4">
          <!-- Header -->
          <div class="flex items-center justify-between">
            <h3 class="text-lg font-bold text-slate-800 dark:text-white flex items-center gap-2">
              <History class="w-5 h-5 text-sky-500" />
              Exámenes Generados
              <span class="text-sm font-normal text-slate-500 dark:text-slate-400">({{ history.length }})</span>
            </h3>
            <button v-if="history.length > 1" @click="confirmarLimpiarHistorial"
              class="text-xs text-red-500 hover:text-red-600 dark:text-red-400 dark:hover:text-red-300 font-medium flex items-center gap-1 px-3 py-1.5 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors">
              <Trash2 class="w-3.5 h-3.5" />
              Limpiar todo
            </button>
          </div>

          <!-- Exam Cards -->
          <div class="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <div v-for="(entry, index) in history" :key="entry.id"
              class="bg-white dark:bg-slate-800 rounded-xl border border-gray-200 dark:border-slate-700 shadow-sm hover:shadow-md transition-all duration-300 overflow-hidden group">
              <!-- Card Header -->
              <div
                class="bg-gradient-to-r from-sky-50 to-teal-50 dark:from-sky-900/20 dark:to-teal-900/20 px-4 py-3 border-b border-gray-100 dark:border-slate-700">
                <h4 class="text-sm font-bold text-slate-800 dark:text-white truncate">
                  {{ entry.resultado.examen.titulo }}
                </h4>
                <div class="flex items-center gap-2 mt-1 text-[11px] text-slate-500 dark:text-slate-400">
                  <Clock class="w-3 h-3" />
                  {{ formatFecha(entry.fechaCreacion) }}
                </div>
              </div>

              <!-- Card Body -->
              <div class="px-4 py-3 space-y-2">
                <div class="flex items-center gap-2 text-xs text-slate-600 dark:text-slate-300">
                  <GraduationCap class="w-3.5 h-3.5 text-teal-500" />
                  <span>{{ entry.gradoLabel }}</span>
                </div>
                <div class="flex items-center gap-2 text-xs text-slate-600 dark:text-slate-300">
                  <FileText class="w-3.5 h-3.5 text-amber-500" />
                  <span>{{ entry.resultado.total_preguntas }} preguntas</span>
                </div>
              </div>

              <!-- Card Actions -->
              <div class="px-4 py-3 border-t border-gray-100 dark:border-slate-700 flex gap-2">
                <button @click="cargarExamen(index)"
                  class="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-semibold text-sky-600 dark:text-sky-400 bg-sky-50 dark:bg-sky-900/20 hover:bg-sky-100 dark:hover:bg-sky-900/40 rounded-lg transition-colors">
                  <Eye class="w-3.5 h-3.5" />
                  Ver
                </button>
                <button @click="vincularDesdeHistorial(index)"
                  class="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-semibold text-orange-600 dark:text-orange-400 bg-orange-50 dark:bg-orange-900/20 hover:bg-orange-100 dark:hover:bg-orange-900/40 rounded-lg transition-colors">
                  <Link class="w-3.5 h-3.5" />
                  Vincular
                </button>
                <button @click="confirmarEliminar(entry.id)"
                  class="flex items-center justify-center px-2 py-2 text-xs text-red-500 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors">
                  <Trash2 class="w-3.5 h-3.5" />
                </button>
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

    <!-- Exam Preview Modal -->
    <ExamPreviewModal :entry="previewEntry" @close="previewEntry = null" @vincular="onPreviewVincular"
      @eliminar="onPreviewEliminar" />
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
