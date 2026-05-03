<script setup lang="ts">
import { shallowRef, ref, onMounted, watch, provide } from 'vue';
import { useRouter } from 'vue-router';

import Sistematizador from '../generador/components/Sistematizador.vue';
import { useMatSistemHistory } from './composables/useMatSistemHistory';
import { useMatSistem } from './composables/useMatSistem';
import { showDeleteConfirm, Toast } from '../../shared/utils/swal';
import { desempenosService, asignacionesService } from '../../shared/services/api';
import { construirFechaISO, formatFechaHora } from '../../shared/utils/dateUtils';
import type { AsignacionPayload } from '../../shared/services/api';
import Footer from '../../shared/components/Footer.vue';
import Header from '../../shared/components/Header.vue';
import EduBackground from '../../shared/components/EduBackground.vue';
import Checkbox from '../../shared/components/Checkbox.vue';
import MatSistemConfig from './components/MatSistemConfig.vue';
import MatSistemDesempenos from './components/MatSistemDesempenos.vue';
import MatSistemResults from './components/MatSistemResults.vue';
import MatSistemExamPreviewModal from './components/MatSistemExamPreviewModal.vue';
import type { ExamenHistoryEntry, FilaTablaRespuestas } from '../../shared/types';
import type { GradoMatematica } from '../../shared/types/matematica';
import {
  Brain,
  LayoutGrid,
  Sparkles,
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
  Users,
  X,
} from 'lucide-vue-next';

const router = useRouter();

const {
  grados,
  desempenos,
  selectedGradoId,
  selectedCompetenciaId,
  selectedDesempenoIds,
  selectedNivelDificultad,
  nivelesDificultad,
  competencias,
  cantidadPreguntas,
  useTextoBase,
  contenidoTematico,
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
  capacidadesActuales,
  loadInitialData,
  selectAllCapacidad,
  deselectAllCapacidad,
  handleFileUpload,
  clearFiles,
  generarPreguntas,
  descargarExamenWord
} = useMatSistem();

const {
  history,
  loadingHistory,
  fetchHistory,
  saveExam,
  getFullExam,
  removeExam,
  loadingDelete,
  clearHistory
} = useMatSistemHistory();

// Provide for Sistematizador linkage
const examForSistematizador = shallowRef<{ tablaRespuestas: FilaTablaRespuestas[]; gradoId: number | null } | null>(null);
provide('examForSistematizador', examForSistematizador);


const previewEntry = shallowRef<ExamenHistoryEntry | null>(null);
const loadingPreview = shallowRef<string | null>(null);
const loadingLink = shallowRef<string | null>(null);
const loadingWordDownload = shallowRef<string | null>(null);
const downloadingPreviewWord = ref(false);

// Asignar examen modal
const asignarModal = ref<{ examenId: number; gradoId: number | null } | null>(null);
const asignarForm = ref({
  seccion: '',
  duracion_minutos: '',
  fecha: '',
  hora_inicio: '',
  hora_fin: '',
  mezclar_preguntas: true,
  mezclar_alternativas: true,
});
const loadingAsignar = ref(false);

function abrirAsignar(entry: ExamenHistoryEntry) {
  asignarModal.value = { examenId: parseInt(entry.id), gradoId: entry.gradoId };
  asignarForm.value = {
    seccion: '',
    duracion_minutos: '',
    fecha: '',
    hora_inicio: '',
    hora_fin: '',
    mezclar_preguntas: true,
    mezclar_alternativas: true,
  };
}

// construirFechaISO importado de shared/utils/dateUtils

async function confirmarAsignar() {
  if (!asignarModal.value) return;
  if ((asignarForm.value.fecha || asignarForm.value.hora_inicio || asignarForm.value.hora_fin)
    && (!asignarForm.value.fecha || !asignarForm.value.hora_inicio || !asignarForm.value.hora_fin)) {
    Toast.fire({ icon: 'error', title: 'Completa fecha, hora de inicio y hora de fin' });
    return;
  }
  loadingAsignar.value = true;
  try {
    const payload: AsignacionPayload = {
      tipo_examen: 'matematica',
      examen_id: asignarModal.value.examenId,
      grado_id: asignarModal.value.gradoId ?? 0,
      seccion: asignarForm.value.seccion || null,
      duracion_minutos: asignarForm.value.duracion_minutos ? parseInt(asignarForm.value.duracion_minutos) : null,
      fecha_inicio: construirFechaISO(asignarForm.value.fecha, asignarForm.value.hora_inicio),
      fecha_fin: construirFechaISO(asignarForm.value.fecha, asignarForm.value.hora_fin),
      mezclar_preguntas: asignarForm.value.mezclar_preguntas,
      mezclar_alternativas: asignarForm.value.mezclar_alternativas,
    };
    await asignacionesService.asignar(payload);
    asignarModal.value = null;
    Toast.fire({ icon: 'success', title: 'Examen asignado correctamente' });
  } catch (e: any) {
    Toast.fire({ icon: 'error', title: e.response?.data?.detail ?? 'Error al asignar' });
  } finally {
    loadingAsignar.value = false;
  }
}

// Auto-save exams to history
watch(resultado, async (newVal) => {
  if (newVal) {
    const grado = (grados.value as GradoMatematica[]).find((g: GradoMatematica) => g.id === selectedGradoId.value);
    await saveExam(newVal, grado ? `Grado ${grado.numero} - ${grado.nivel}` : newVal.grado, {
      grado_id: selectedGradoId.value,
      competencia_id: selectedCompetenciaId.value,
      nivel_dificultad: selectedNivelDificultad.value,
      modelo: 'gemini'
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

// formatFechaHora importado de shared/utils/dateUtils

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
    class="min-h-screen flex flex-col bg-gradient-to-br from-indigo-50/50 via-purple-50/30 to-sky-50/50 dark:from-slate-950 dark:via-slate-900 dark:to-indigo-950/30 transition-colors edu-pattern-bg">

    <!-- Decorative Background Elements -->
    <EduBackground variant="indigo" />

    <Header title="MatSistem" subtitle="Matemática práctica" :has-resultado="!!resultado"
      :loading="loading" :show-results="showResults" :active-tab="activeTab"
      gradient-class="from-indigo-600 via-indigo-500 to-purple-500 shadow-indigo-500/20"
      version-badge-class="bg-purple-400 text-purple-900" subtitle-class="text-indigo-100 dark:text-slate-400"
      mascota-bubble-class="border-purple-300 dark:border-purple-500"
      mascota-text-class="text-purple-600 dark:text-purple-400"
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

      <!-- Tabs Navigation - Estilo Educativo -->
      <div class="mb-6 pb-2">
        <div
          class="bg-white dark:bg-slate-800 rounded-2xl p-1 sm:p-2 shadow-lg border border-gray-100 dark:border-slate-700 grid grid-cols-3 sm:flex sm:inline-flex gap-1 sm:gap-2 w-full sm:w-auto">
          <button @click="activeTab = 'generador'"
            class="flex flex-col sm:flex-row items-center justify-center gap-1 sm:gap-2 p-2 sm:px-5 sm:py-3 rounded-xl font-semibold text-[10px] sm:text-sm leading-tight sm:leading-normal transition-all duration-300 text-center"
            :class="activeTab === 'generador'
              ? 'bg-gradient-to-r from-indigo-500 to-indigo-600 text-white shadow-md shadow-indigo-500/30'
              : 'text-slate-600 dark:text-slate-400 hover:bg-indigo-50 dark:hover:bg-slate-700'">
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

        <!-- MatSistemConfig -->
        <MatSistemConfig v-model:selectedNivelDificultad="selectedNivelDificultad"
          :nivelesDificultad="nivelesDificultad"
          v-model:selectedGradoId="selectedGradoId" :gradoOptions="gradoOptions"
          :loading-grados="loadingGrados" v-model:selectedCompetenciaId="selectedCompetenciaId"
          :competencias="competencias" v-model:cantidadPreguntas="cantidadPreguntas"
          v-model:useTextoBase="useTextoBase" v-model:contenidoTematico="contenidoTematico"
          :selectedFiles="selectedFiles" :filesMetadata="filesMetadata"
          :uploadingFile="uploadingFile" :uploadError="uploadError" @handleFileUpload="handleFileUpload"
          @clearFiles="clearFiles" />

        <!-- Main Content -->
        <div class="grid lg:grid-cols-2 gap-4 sm:gap-6">

          <!-- Left: Desempeños -->
          <MatSistemDesempenos :desempenos="desempenos" :selectedDesempenosCount="selectedDesempenosCount"
            :loadingDesempenos="loadingDesempenos" :selectedGradoId="selectedGradoId"
            v-model:activeCapacidadTab="activeCapacidadTab" :desempenosPorCapacidad="desempenosPorCapacidad"
            v-model:selectedDesempenoIds="selectedDesempenoIds" :loading="loading" :error="error"
            :capacidadesActuales="capacidadesActuales" @selectAllCapacidad="selectAllCapacidad"
            @deselectAllCapacidad="deselectAllCapacidad" @generarPreguntas="generarPreguntas" />

          <!-- Right: Results -->
          <MatSistemResults :resultado="resultado" :loading="loading" :showResults="showResults"
            :descargandoWord="descargandoWord" @descargarExamenWord="descargarExamenWord"
            @vincularSistematizador="vincularConSistematizador" />
        </div>
      </div>

      <!-- History Tab Content (Copied and adapted from LectoSistem) -->
      <div v-show="activeTab === 'historial'">
        <!-- History Loading -->
        <div v-if="loadingHistory"
          class="flex flex-col items-center justify-center py-12 sm:py-20 bg-white dark:bg-slate-800 rounded-2xl border border-gray-100 dark:border-slate-700 shadow-sm">
          <Loader2 class="w-10 h-10 text-indigo-500 animate-spin mb-4" />
          <p class="text-slate-500 dark:text-slate-400 font-medium">Cargando historial...</p>
        </div>

        <!-- Empty History -->
        <div v-else-if="history.length === 0"
          class="bg-white dark:bg-slate-800 rounded-2xl border border-gray-200 dark:border-slate-700 shadow-sm p-6 sm:p-8 md:p-12 text-center">
          <History class="w-10 h-10 sm:w-12 sm:h-12 text-gray-300 dark:text-slate-600 mx-auto mb-4" />
          <h3 class="text-base sm:text-lg font-semibold text-slate-800 dark:text-white mb-2">Sin exámenes guardados</h3>
          <p class="text-slate-500 dark:text-slate-400 text-xs sm:text-sm max-w-sm sm:max-w-md mx-auto">
            Los exámenes que generes se guardarán automáticamente aquí para que puedas consultarlos o vincularlos con el
            sistematizador.
          </p>
        </div>

        <!-- History List -->
        <div v-else class="space-y-4">
          <!-- Header -->
          <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 sm:gap-0">
            <h3 class="text-base sm:text-lg font-bold text-slate-800 dark:text-white flex items-center gap-2">
              <History class="w-5 h-5 text-sky-500" />
              Exámenes Generados
              <span class="text-xs sm:text-sm font-normal text-slate-500 dark:text-slate-400">({{ history.length }})</span>
            </h3>
            <button v-if="history.length > 1" @click="confirmarLimpiarHistorial"
              class="text-xs text-red-500 hover:text-red-600 dark:text-red-400 dark:hover:text-red-300 font-medium flex items-center gap-1 px-3 py-1.5 rounded-xl hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors">
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
                  {{ formatFechaHora(entry.fechaCreacion) }}
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
              <div class="px-3 sm:px-4 py-2.5 sm:py-3 border-t border-gray-100 dark:border-slate-700 flex gap-1.5 sm:gap-2 flex-wrap">
                <button @click="cargarExamen(index)"
                  class="flex-1 flex items-center justify-center gap-1 sm:gap-1.5 px-2 sm:px-3 py-1.5 sm:py-2 text-[10px] sm:text-xs font-semibold text-sky-600 dark:text-sky-400 bg-sky-50 dark:bg-sky-900/20 hover:bg-sky-100 dark:hover:bg-sky-900/40 rounded-xl transition-colors">
                  <Eye class="w-3 h-3 sm:w-3.5 sm:h-3.5" />
                  Ver
                </button>
                <button @click="descargarWordHistorial(index)" :disabled="!!loadingWordDownload"
                  class="flex-1 flex items-center justify-center gap-1 sm:gap-1.5 px-2 sm:px-3 py-1.5 sm:py-2 text-[10px] sm:text-xs font-semibold text-teal-600 dark:text-teal-400 bg-teal-50 dark:bg-teal-900/20 hover:bg-teal-100 dark:hover:bg-teal-900/40 rounded-xl transition-colors disabled:opacity-50">
                  <Loader2 v-if="loadingWordDownload === entry.id" class="w-3 h-3 sm:w-3.5 sm:h-3.5 animate-spin" />
                  <Download v-else class="w-3 h-3 sm:w-3.5 sm:h-3.5" />
                  Word
                </button>
                <button @click="vincularDesdeHistorial(index)" :disabled="!!loadingLink"
                  class="flex-1 flex items-center justify-center gap-1 sm:gap-1.5 px-2 sm:px-3 py-1.5 sm:py-2 text-[10px] sm:text-xs font-semibold text-orange-600 dark:text-orange-400 bg-orange-50 dark:bg-orange-900/20 hover:bg-orange-100 dark:hover:bg-orange-900/40 rounded-xl transition-colors disabled:opacity-50">
                  <Loader2 v-if="loadingLink === entry.id" class="w-3 h-3 sm:w-3.5 sm:h-3.5 animate-spin" />
                  <Link v-else class="w-3 h-3 sm:w-3.5 sm:h-3.5" />
                  <span class="hidden sm:inline">Vincular</span>
                  <span class="sm:hidden">Vinc.</span>
                </button>
                <button @click="abrirAsignar(entry)"
                  class="flex items-center justify-center px-1.5 sm:px-2 py-1.5 sm:py-2 text-xs text-violet-500 dark:text-violet-400 hover:bg-violet-50 dark:hover:bg-violet-900/20 rounded-xl transition-colors"
                  title="Asignar a estudiantes">
                  <Users class="w-3 h-3 sm:w-3.5 sm:h-3.5" />
                </button>
                <button @click="confirmarEliminar(entry.id)" :disabled="!!loadingDelete"
                  class="flex items-center justify-center px-1.5 sm:px-2 py-1.5 sm:py-2 text-xs text-red-500 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-xl transition-colors disabled:opacity-50">
                  <Loader2 v-if="loadingDelete === entry.id" class="w-3 h-3 sm:w-3.5 sm:h-3.5 animate-spin" />
                  <Trash2 v-else class="w-3 h-3 sm:w-3.5 sm:h-3.5" />
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
    <MatSistemExamPreviewModal :entry="previewEntry" :loading-delete="loadingDelete === previewEntry?.id"
      :is-loading="!!loadingPreview" :downloading-word="downloadingPreviewWord" @close="previewEntry = null"
      @vincular="onPreviewVincular" @eliminar="onPreviewEliminar" @descargar-word="descargarWordDesdePreview" />

    <!-- Asignar Examen Modal -->
    <Teleport to="body">
      <div v-if="asignarModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
        <div class="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl w-full max-w-sm border border-slate-200 dark:border-slate-700">
          <div class="flex items-center justify-between px-5 py-4 border-b border-slate-100 dark:border-slate-700">
            <div class="flex items-center gap-2">
              <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-400 to-purple-500 flex items-center justify-center">
                <Users class="w-4 h-4 text-white" />
              </div>
              <h3 class="font-bold text-slate-800 dark:text-white text-sm">Asignar a estudiantes</h3>
            </div>
            <button @click="asignarModal = null" class="p-1.5 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-400">
              <X class="w-4 h-4" />
            </button>
          </div>
          <div class="px-5 py-4 space-y-4">
            <div>
              <label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">Sección (opcional)</label>
              <select v-model="asignarForm.seccion"
                class="w-full px-3 py-2 text-sm border border-slate-300 dark:border-slate-600 rounded-xl bg-white dark:bg-slate-700 text-slate-800 dark:text-white focus:ring-2 focus:ring-violet-400 focus:border-violet-400 outline-none">
                <option value="">— Todas las secciones —</option>
                <option value="A">A</option>
                <option value="B">B</option>
                <option value="C">C</option>
                <option value="D">D</option>
                <option value="E">E</option>
                <option value="F">F</option>
                <option value="G">G</option>
                <option value="H">H</option>
                <option value="I">I</option>
                <option value="J">J</option>
                <option value="Única">Única</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">Duración (minutos, opcional)</label>
              <input v-model="asignarForm.duracion_minutos" type="number" min="5" max="180" placeholder="Sin límite de tiempo"
                class="w-full px-3 py-2 text-sm border border-slate-300 dark:border-slate-600 rounded-xl bg-white dark:bg-slate-700 text-slate-800 dark:text-white focus:ring-2 focus:ring-violet-400 focus:border-violet-400 outline-none" />
            </div>
            <div class="space-y-3 rounded-2xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-900/40">
              <div>
                <label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">Día de aplicación</label>
                <input v-model="asignarForm.fecha" type="date"
                  class="w-full px-3 py-2 text-sm border border-slate-300 dark:border-slate-600 rounded-xl bg-white dark:bg-slate-700 text-slate-800 dark:text-white focus:ring-2 focus:ring-violet-400 focus:border-violet-400 outline-none" />
              </div>
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">Hora inicio</label>
                  <input v-model="asignarForm.hora_inicio" type="time"
                    class="w-full px-3 py-2 text-sm border border-slate-300 dark:border-slate-600 rounded-xl bg-white dark:bg-slate-700 text-slate-800 dark:text-white focus:ring-2 focus:ring-violet-400 focus:border-violet-400 outline-none" />
                </div>
                <div>
                  <label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">Hora fin</label>
                  <input v-model="asignarForm.hora_fin" type="time"
                    class="w-full px-3 py-2 text-sm border border-slate-300 dark:border-slate-600 rounded-xl bg-white dark:bg-slate-700 text-slate-800 dark:text-white focus:ring-2 focus:ring-violet-400 focus:border-violet-400 outline-none" />
                </div>
              </div>
              <p class="text-[11px] text-slate-500 dark:text-slate-400">Si defines horario, el examen solo estará disponible ese día dentro de ese rango de horas.</p>
            </div>
            <div class="space-y-2 rounded-2xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-900/40">
              <Checkbox v-model="asignarForm.mezclar_preguntas"
                class="group flex items-start gap-3 rounded-xl border border-slate-200 bg-white p-3 transition-all duration-150 dark:border-slate-700 dark:bg-slate-800/80"
                color="checked:bg-violet-600 checked:border-violet-600 dark:checked:bg-violet-500 dark:checked:border-violet-500 focus:ring-violet-500/50">
                <span>
                  <strong class="block text-sm font-bold text-slate-700 dark:text-slate-200">Aleatorizar preguntas</strong>
                  <span class="text-xs text-slate-500 dark:text-slate-400">El estudiante verá las preguntas en orden aleatorio.</span>
                </span>
              </Checkbox>
              <Checkbox v-model="asignarForm.mezclar_alternativas"
                class="group flex items-start gap-3 rounded-xl border border-slate-200 bg-white p-3 transition-all duration-150 dark:border-slate-700 dark:bg-slate-800/80"
                color="checked:bg-violet-600 checked:border-violet-600 dark:checked:bg-violet-500 dark:checked:border-violet-500 focus:ring-violet-500/50">
                <span>
                  <strong class="block text-sm font-bold text-slate-700 dark:text-slate-200">Aleatorizar alternativas</strong>
                  <span class="text-xs text-slate-500 dark:text-slate-400">Las opciones A, B, C y D se mezclarán en cada pregunta.</span>
                </span>
              </Checkbox>
            </div>
          </div>
          <div class="px-5 py-4 border-t border-slate-100 dark:border-slate-700 flex gap-3">
            <button @click="asignarModal = null"
              class="flex-1 py-2.5 rounded-xl border border-slate-300 dark:border-slate-600 text-sm font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors">
              Cancelar
            </button>
            <button @click="confirmarAsignar" :disabled="loadingAsignar"
              class="flex-1 py-2.5 rounded-xl bg-gradient-to-r from-violet-500 to-purple-600 text-white text-sm font-bold hover:from-violet-600 hover:to-purple-700 transition-all disabled:opacity-60 flex items-center justify-center gap-2">
              <Loader2 v-if="loadingAsignar" class="w-4 h-4 animate-spin" />
              Asignar
            </button>
          </div>
        </div>
      </div>
    </Teleport>
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
