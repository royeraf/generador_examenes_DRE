<script setup lang="ts">
import { shallowRef, ref, onMounted, watch, provide } from 'vue';
import { useRouter } from 'vue-router';

import Sistematizador from '../components/Sistematizador.vue';
import Footer from '../components/Footer.vue';
import { useLectoSistem } from '../composables/useLectoSistem';
import { useExamHistory } from '../composables/useExamHistory';
import { showDeleteConfirm, Toast } from '../utils/swal';
import { desempenosService } from '../services/api';
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
  Loader2,
  Download,
} from 'lucide-vue-next';

const router = useRouter();
import Header from '../components/Header.vue';
import EduBackground from '../components/EduBackground.vue';
import LectoSistemConfig from '../components/lectosistem/LectoSistemConfig.vue';
import LectoSistemDesempenos from '../components/lectosistem/LectoSistemDesempenos.vue';
import LectoSistemResults from '../components/lectosistem/LectoSistemResults.vue';
import ExamPreviewModal from '../components/lectosistem/ExamPreviewModal.vue';
import type { ExamenHistoryEntry, FilaTablaRespuestas } from '../types';


const {
  grados,
  desempenos,
  selectedGradoId,
  selectedDesempenoIds,
  selectedNivelDificultad,
  nivelesDificultad,
  cantidadPreguntas,
  useTextoBase,
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

const {
  history,
  loadingHistory,
  fetchHistory,
  saveExam,
  getFullExam,
  removeExam,
  loadingDelete,
  clearHistory
} = useExamHistory();

// Provide for Sistematizador linkage
const examForSistematizador = shallowRef<{ tablaRespuestas: FilaTablaRespuestas[]; gradoId: number | null } | null>(null);
provide('examForSistematizador', examForSistematizador);


const previewEntry = shallowRef<ExamenHistoryEntry | null>(null);
const loadingPreview = shallowRef<string | null>(null);
const loadingLink = shallowRef<string | null>(null);
const loadingWordDownload = shallowRef<string | null>(null);
const downloadingPreviewWord = ref(false);

// Auto-save exams to history
watch(resultado, async (newVal) => {
  if (newVal) {
    const grado = grados.value.find(g => g.id === selectedGradoId.value);
    await saveExam(newVal, grado?.nombre || newVal.grado, {
      grado_id: selectedGradoId.value,
      nivel_dificultad: selectedNivelDificultad.value,
      modelo: 'gemini' // Or whatever is being used
    });
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

async function vincularDesdeHistorial(index: number) {
  const summaryEntry = history.value[index];
  if (!summaryEntry) return;

  loadingLink.value = summaryEntry.id;
  const fullEntry = await getFullExam(summaryEntry.id);
  loadingLink.value = null;

  if (fullEntry?.resultado.examen.tabla_respuestas) {
    examForSistematizador.value = {
      tablaRespuestas: fullEntry.resultado.examen.tabla_respuestas,
      gradoId: fullEntry.gradoId,
    };
    activeTab.value = 'sistematizador';
  }
}

async function cargarExamen(index: number) {
  const summaryEntry = history.value[index];
  if (!summaryEntry) return;

  // Set partial entry to open modal immediately
  previewEntry.value = summaryEntry;
  loadingPreview.value = summaryEntry.id;

  const fullEntry = await getFullExam(summaryEntry.id);
  loadingPreview.value = null;

  if (fullEntry) {
    previewEntry.value = fullEntry;
  }
}

function onPreviewVincular() {
  if (previewEntry.value?.resultado.examen.tabla_respuestas) {
    examForSistematizador.value = {
      tablaRespuestas: previewEntry.value.resultado.examen.tabla_respuestas,
      gradoId: previewEntry.value.gradoId,
    };
    previewEntry.value = null;
    activeTab.value = 'sistematizador';
  }
}

async function onPreviewEliminar() {
  if (!previewEntry.value) return;
  const confirmed = await showDeleteConfirm('¿Eliminar este examen?', 'Se eliminará de la base de datos');
  if (confirmed) {
    await removeExam(previewEntry.value.id);
    previewEntry.value = null;
    Toast.fire({ icon: 'success', title: 'Examen eliminado' });
  }
}

async function confirmarEliminar(id: string) {
  const confirmed = await showDeleteConfirm('¿Eliminar este examen?', 'Se eliminará de la base de datos');
  if (confirmed) {
    await removeExam(id);
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

async function descargarWordHistorial(index: number) {
  const summaryEntry = history.value[index];
  if (!summaryEntry) return;

  loadingWordDownload.value = summaryEntry.id;
  try {
    const fullEntry = await getFullExam(summaryEntry.id);
    if (fullEntry?.resultado.examen) {
      await desempenosService.descargarWord(fullEntry.resultado.examen, fullEntry.resultado.grado);
    }
  } catch (e) {
    Toast.fire({ icon: 'error', title: 'Error al descargar Word' });
    console.error('Error descarga Word historial:', e);
  } finally {
    loadingWordDownload.value = null;
  }
}

async function descargarWordDesdePreview() {
  if (!previewEntry.value) return;

  downloadingPreviewWord.value = true;
  try {
    let entry = previewEntry.value;
    // Si no tiene preguntas cargadas, fetch full
    if (!entry.resultado.examen.preguntas?.length) {
      const fullEntry = await getFullExam(entry.id);
      if (fullEntry) entry = fullEntry;
    }
    await desempenosService.descargarWord(entry.resultado.examen, entry.resultado.grado);
  } catch (e) {
    Toast.fire({ icon: 'error', title: 'Error al descargar Word' });
    console.error('Error descarga Word preview:', e);
  } finally {
    downloadingPreviewWord.value = false;
  }
}



onMounted(async () => {
  await loadInitialData();
  await fetchHistory();
});
</script>

<template>
  <div
    class="min-h-screen flex flex-col bg-gradient-to-br from-teal-50/50 via-amber-50/30 to-sky-50/50 dark:from-slate-950 dark:via-slate-900 dark:to-teal-950/30 transition-colors edu-pattern-bg">

    <!-- Decorative Background Elements -->
    <EduBackground variant="teal" />

    <Header title="LectoSistem" subtitle="Lectura inteligente" :has-resultado="!!resultado"
      :loading="loading" :show-results="showResults" :active-tab="activeTab"
      @toggle-results="showResults = !showResults">
      <template #actions-before>
        <button @click="router.push('/')"
          class="p-2.5 rounded-xl bg-white/20 text-white border border-white/30 hover:bg-white/30 dark:bg-slate-700 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-600 transition-all duration-300"
          title="Inicio">
          <Home class="w-5 h-5" />
        </button>
      </template>
    </Header>

    <main class="flex-1 max-w-7xl mx-auto px-4 sm:px-6 py-4 sm:py-6 w-full">

      <!-- Tabs Navigation -->
      <div class="mb-6 pb-2">
        <div
          class="bg-white dark:bg-slate-800 rounded-2xl p-1 sm:p-2 shadow-lg border border-gray-100 dark:border-slate-700 grid grid-cols-3 sm:flex sm:inline-flex gap-1 sm:gap-2 w-full sm:w-auto">
          <button @click="activeTab = 'generador'"
            class="flex flex-col sm:flex-row items-center justify-center gap-1 sm:gap-2 p-2 sm:px-5 sm:py-3 rounded-xl font-semibold text-[10px] sm:text-sm leading-tight sm:leading-normal transition-all duration-300 text-center"
            :class="activeTab === 'generador'
              ? 'bg-gradient-to-r from-teal-500 to-teal-600 text-white shadow-md shadow-teal-500/30'
              : 'text-slate-600 dark:text-slate-400 hover:bg-teal-50 dark:hover:bg-slate-700'">
            <Brain class="w-4 h-4 sm:w-5 sm:h-5" />
            <span class="flex items-center justify-center gap-1">Generador <Sparkles v-if="activeTab === 'generador'" class="hidden sm:inline w-3 h-3 text-amber-300" /></span>
          </button>

          <button @click="activeTab = 'historial'"
            class="flex flex-col sm:flex-row items-center justify-center gap-1 sm:gap-2 p-2 sm:px-5 sm:py-3 rounded-xl font-semibold text-[10px] sm:text-sm leading-tight sm:leading-normal transition-all duration-300 text-center"
            :class="activeTab === 'historial'
              ? 'bg-gradient-to-r from-sky-500 to-blue-600 text-white shadow-md shadow-sky-500/30'
              : 'text-slate-600 dark:text-slate-400 hover:bg-sky-50 dark:hover:bg-slate-700'">
            <div class="relative flex items-center justify-center">
                <History class="w-4 h-4 sm:w-5 sm:h-5" />
                <span v-if="history.length > 0" class="absolute -top-1.5 -right-2 sm:static sm:ml-1 px-1 py-0.5 text-[8px] sm:text-[10px] font-bold rounded-full"
                  :class="activeTab === 'historial' ? 'bg-white/20 text-white' : 'bg-sky-100 text-sky-600 dark:bg-sky-900/30 dark:text-sky-400'">
                  {{ history.length }}
                </span>
            </div>
            <span>Historial</span>
          </button>

          <button @click="activeTab = 'sistematizador'"
            class="flex flex-col sm:flex-row items-center justify-center gap-1 sm:gap-2 p-2 sm:px-5 sm:py-3 rounded-xl font-semibold text-[10px] sm:text-sm leading-tight sm:leading-normal transition-all duration-300 text-center"
            :class="activeTab === 'sistematizador'
              ? 'bg-gradient-to-r from-amber-500 to-orange-500 text-white shadow-md shadow-amber-500/30'
              : 'text-slate-600 dark:text-slate-400 hover:bg-amber-50 dark:hover:bg-slate-700'">
            <LayoutGrid class="w-4 h-4 sm:w-5 sm:h-5" />
            <span class="flex items-center justify-center gap-1">Sistematizador <Award v-if="activeTab === 'sistematizador'" class="hidden sm:inline w-3 h-3 text-yellow-300" /></span>
          </button>
        </div>
      </div>

      <!-- Generator Tab Content -->
      <div v-show="activeTab === 'generador'">

        <!-- Configuration Row -->
        <LectoSistemConfig :niveles-dificultad="nivelesDificultad"
          v-model:modelo-nivel-dificultad="selectedNivelDificultad" :grado-options="gradoOptions"
          v-model:modelo-grado-id="selectedGradoId" :loading-grados="loadingGrados"
          v-model:modelo-cantidad-preguntas="cantidadPreguntas" v-model:modelo-use-texto-base="useTextoBase"
          :selected-files="selectedFiles" :files-metadata="filesMetadata" :uploading-file="uploadingFile"
          :upload-error="uploadError" @file-upload="handleFileUpload" @clear-files="clearFiles"
          :tipo-textual-options="tipoTextualOptions" v-model:modelo-tipo-textual="selectedTipoTextual"
          :formato-textual-options="formatoTextualOptions" v-model:modelo-formato-textual="selectedFormatoTextual"
          v-model:modelo-cantidad-literal="cantidadLiteral" v-model:modelo-cantidad-inferencial="cantidadInferencial"
          v-model:modelo-cantidad-critico="cantidadCritico" :is-breakdown-valid="isBreakdownValid"
          :total-breakdown="totalBreakdown" />

        <!-- Main Content -->
        <div class="grid lg:grid-cols-2 gap-4 sm:gap-6">

          <!-- Left: Desempeños -->
          <LectoSistemDesempenos :desempenos="desempenos" :selected-desempenos-count="selectedDesempenosCount"
            :loading-desempenos="loadingDesempenos" :selected-grado-id="selectedGradoId"
            v-model:active-capacidad-tab="activeCapacidadTab" :desempenos-por-capacidad="desempenosPorCapacidad"
            v-model:selected-desempeno-ids="selectedDesempenoIds" :loading="loading" :error="error"
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
        <!-- History Loading -->
        <div v-if="loadingHistory"
          class="flex flex-col items-center justify-center py-20 bg-white dark:bg-slate-800 rounded-2xl border border-gray-100 dark:border-slate-700 shadow-sm">
          <Loader2 class="w-10 h-10 text-sky-500 animate-spin mb-4" />
          <p class="text-slate-500 dark:text-slate-400 font-medium">Cargando historial...</p>
        </div>

        <!-- Empty History -->
        <div v-else-if="history.length === 0"
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
                <button @click="descargarWordHistorial(index)" :disabled="!!loadingWordDownload"
                  class="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-semibold text-teal-600 dark:text-teal-400 bg-teal-50 dark:bg-teal-900/20 hover:bg-teal-100 dark:hover:bg-teal-900/40 rounded-lg transition-colors disabled:opacity-50">
                  <Loader2 v-if="loadingWordDownload === entry.id" class="w-3.5 h-3.5 animate-spin" />
                  <Download v-else class="w-3.5 h-3.5" />
                  Word
                </button>
                <button @click="vincularDesdeHistorial(index)" :disabled="!!loadingLink"
                  class="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-semibold text-orange-600 dark:text-orange-400 bg-orange-50 dark:bg-orange-900/20 hover:bg-orange-100 dark:hover:bg-orange-900/40 rounded-lg transition-colors disabled:opacity-50">
                  <Loader2 v-if="loadingLink === entry.id" class="w-3.5 h-3.5 animate-spin" />
                  <Link v-else class="w-3.5 h-3.5" />
                  Vincular
                </button>
                <button @click="confirmarEliminar(entry.id)" :disabled="!!loadingDelete"
                  class="flex items-center justify-center px-2 py-2 text-xs text-red-500 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors disabled:opacity-50">
                  <Loader2 v-if="loadingDelete === entry.id" class="w-3.5 h-3.5 animate-spin" />
                  <Trash2 v-else class="w-3.5 h-3.5" />
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



    <!-- Exam Preview Modal -->
    <ExamPreviewModal :entry="previewEntry" :loading-delete="loadingDelete === previewEntry?.id"
      :is-loading="!!loadingPreview" :downloading-word="downloadingPreviewWord" @close="previewEntry = null"
      @vincular="onPreviewVincular" @eliminar="onPreviewEliminar" @descargar-word="descargarWordDesdePreview" />
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
