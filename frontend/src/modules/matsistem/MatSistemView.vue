<script setup lang="ts">
import { shallowRef, ref, onMounted, onUnmounted, watch } from 'vue';

// import Sistematizador from '../generador/components/Sistematizador.vue';
import { useMatSistemHistory } from './composables/useMatSistemHistory';
import { useMatSistem } from './composables/useMatSistem';
import { showDeleteConfirm, Toast } from '../../shared/utils/swal';
import { desempenosService, asignacionesService } from '../../shared/services/api';
import { construirFechaISO, formatFechaHora } from '../../shared/utils/dateUtils';
import type { AsignacionPayload } from '../../shared/services/api';
import {
  Brain, Sparkles, LayoutGrid, History, Trash2,
  GraduationCap, FileText, Loader2, X,
  CloudUpload, Target, Calculator, RefreshCw, Shapes, BarChart3, BookOpen, Hash,
  Eye, FileDown, Send, PanelLeft,
} from 'lucide-vue-next';

import Checkbox from '../../shared/components/Checkbox.vue';
import ComboBox from '../../shared/components/ComboBox.vue';
import MatSistemDesempenos from './components/MatSistemDesempenos.vue';
import MatSistemResults from './components/MatSistemResults.vue';
import MatSistemExamPreviewModal from './components/MatSistemExamPreviewModal.vue';
import Navbar from '../../shared/components/Navbar.vue';
import type { ExamenHistoryEntry } from '../../shared/types';
import type { GradoMatematica } from '../../shared/types/matematica';

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
  deselectAll,
  handleFileUpload,
  clearFiles,
  generarPreguntas,
  descargarExamenWord
} = useMatSistem();

const {
  history,
  loadingHistory,
  fetchError,
  fetchHistory,
  saveExam,
  getFullExam,
  removeExam,
  loadingDelete,
} = useMatSistemHistory();

// // Provide for Sistematizador linkage
// const examForSistematizador = shallowRef<{ tablaRespuestas: FilaTablaRespuestas[]; gradoId: number | null } | null>(null);
// provide('examForSistematizador', examForSistematizador);


const previewEntry = shallowRef<ExamenHistoryEntry | null>(null);
const loadingPreview = shallowRef<string | null>(null);
// const loadingLink = shallowRef<string | null>(null);
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

// Refrescar historial cada vez que el usuario cambia a esa pestaña
watch(activeTab, (tab) => {
  if (tab === 'historial') {
    fetchHistory();
  }
});

// // Vincular with sistematizador
// function vincularConSistematizador() {
//   if (resultado.value?.examen.tabla_respuestas) {
//     examForSistematizador.value = {
//       tablaRespuestas: resultado.value.examen.tabla_respuestas,
//       gradoId: selectedGradoId.value,
//     };
//     activeTab.value = 'sistematizador';
//   }
// }

// async function vincularDesdeHistorial(index: number) {
//   const summaryEntry = history.value[index];
//   if (!summaryEntry) return;
//   loadingLink.value = summaryEntry.id;
//   const fullEntry = await getFullExam(summaryEntry.id);
//   loadingLink.value = null;
//   if (fullEntry?.resultado.examen.tabla_respuestas) {
//     examForSistematizador.value = {
//       tablaRespuestas: fullEntry.resultado.examen.tabla_respuestas,
//       gradoId: fullEntry.gradoId,
//     };
//     activeTab.value = 'sistematizador';
//   }
// }

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

// function onPreviewVincular() {
//   if (previewEntry.value?.resultado.examen.tabla_respuestas) {
//     examForSistematizador.value = {
//       tablaRespuestas: previewEntry.value.resultado.examen.tabla_respuestas,
//       gradoId: previewEntry.value.gradoId,
//     };
//     previewEntry.value = null;
//     activeTab.value = 'sistematizador';
//   }
// }

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

async function onGenerarPreguntas() {
  if (!isDesktop.value) {
    mobileTab.value = 'results';
  }
  await generarPreguntas();
}

async function confirmarLimpiarHistorial() {
  const confirmed = await showDeleteConfirm('¿Limpiar todo el historial?', 'Se eliminarán todos los exámenes guardados');
  if (!confirmed) return;
  const ids = history.value.map(e => e.id);
  await Promise.allSettled(ids.map(id => removeExam(id)));
  await fetchHistory();
  Toast.fire({ icon: 'success', title: 'Historial limpiado' });
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

// Icons and Visuals for Competencias
const COMP_ICONS: Record<number, typeof Calculator> = {
    1: Calculator,
    2: RefreshCw,
    3: Shapes,
    4: BarChart3
};
const COMP_VISUAL: Record<number, { shortName: string; badge: string }> = {
    1: { shortName: 'Cantidad', badge: 'bg-teal-500' },
    2: { shortName: 'Regularidad', badge: 'bg-amber-500' },
    3: { shortName: 'Forma y loc.', badge: 'bg-violet-500' },
    4: { shortName: 'Gestión datos', badge: 'bg-rose-500' }
};
const DEFAULT_COMP_VISUAL = COMP_VISUAL[1]!;
const getCompVisual = (codigo: number) => COMP_VISUAL[codigo] ?? DEFAULT_COMP_VISUAL;

// Resizing logic
const isDesktop = ref(window.innerWidth >= 1024);
const col1Width = ref(320);
const col3Width = ref(350);
const mobileTab = ref<'config' | 'results' | 'desempenos'>('config');
const configCollapsed = shallowRef(false);
const desempenosCollapsed = shallowRef(false);

const isDraggingCol1 = ref(false);
const isDraggingCol3 = ref(false);

const onMouseDownCol1 = () => {
  isDraggingCol1.value = true;
  document.body.style.cursor = 'col-resize';
  window.addEventListener('mousemove', onMouseMove);
  window.addEventListener('mouseup', onMouseUp);
};

const onMouseDownCol3 = () => {
  isDraggingCol3.value = true;
  document.body.style.cursor = 'col-resize';
  window.addEventListener('mousemove', onMouseMove);
  window.addEventListener('mouseup', onMouseUp);
};

const onMouseMove = (e: MouseEvent) => {
  if (isDraggingCol1.value) {
    let newWidth = e.clientX - 16;
    if (newWidth < 250) newWidth = 250;
    if (newWidth > 600) newWidth = 600;
    col1Width.value = newWidth;
  }
  if (isDraggingCol3.value) {
    let newWidth = window.innerWidth - e.clientX - 16;
    if (newWidth < 250) newWidth = 250;
    if (newWidth > 700) newWidth = 700;
    col3Width.value = newWidth;
  }
};

const onMouseUp = () => {
  isDraggingCol1.value = false;
  isDraggingCol3.value = false;
  document.body.style.cursor = '';
  window.removeEventListener('mousemove', onMouseMove);
  window.removeEventListener('mouseup', onMouseUp);
};

onUnmounted(() => {
  const onResizeWindow = () => { isDesktop.value = window.innerWidth >= 1024; };
  window.addEventListener('resize', onResizeWindow);
  window.removeEventListener('mousemove', onMouseMove);
  window.removeEventListener('mouseup', onMouseUp);
});

onMounted(async () => {
  window.addEventListener('resize', () => isDesktop.value = window.innerWidth >= 1024);
  await loadInitialData();
  await fetchHistory();
});
</script>

<template>
  <div class="h-screen flex flex-col overflow-hidden bg-slate-50 dark:bg-slate-950 text-slate-700 dark:text-slate-200 font-sans">
    
    <!-- Header unificado -->
    <Navbar title="MatSistem" subtitle="Matemática práctica con IA" :show-home="true">
      <template #center>
        <div class="flex items-center bg-white dark:bg-slate-800 rounded-full p-1 border border-slate-200 dark:border-slate-700 shadow-sm overflow-x-auto flex-nowrap [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
          <button @click="activeTab = 'generador'" class="shrink-0 px-3 sm:px-4 py-1.5 rounded-full text-xs font-medium transition-all" :class="activeTab === 'generador' ? 'bg-indigo-500 text-white shadow' : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-white'">Generador</button>
          <button @click="activeTab = 'historial'" class="shrink-0 px-3 sm:px-4 py-1.5 rounded-full text-xs font-medium transition-all flex items-center gap-1.5" :class="activeTab === 'historial' ? 'bg-indigo-500 text-white shadow' : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-white'">Historial <span v-if="history.length" class="text-[10px] bg-slate-200 dark:bg-slate-700 text-slate-800 dark:text-white px-1.5 rounded-full">{{ history.length }}</span></button>
          <!-- <button @click="activeTab = 'sistematizador'" class="shrink-0 px-3 sm:px-4 py-1.5 rounded-full text-xs font-medium transition-all" :class="activeTab === 'sistematizador' ? 'bg-indigo-500 text-white shadow' : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-white'">Sistematizador</button> -->
        </div>
      </template>
    </Navbar>

    <!-- Content wrapper -->
    <div class="flex-1 min-h-0 flex flex-col p-2 sm:p-4 pt-0 gap-2">
      
      <!-- ══════════════════════════════════════════
           GENERADOR TAB
      ══════════════════════════════════════════ -->
      <div v-show="activeTab === 'generador'" class="flex-1 min-h-0 flex flex-col lg:flex-row gap-2">
        
        <!-- COLUMN 1: Configuración -->
        <aside v-show="isDesktop || mobileTab === 'config'" class="flex-1 lg:flex-none shrink-0 bg-white dark:bg-slate-800 rounded-xl flex flex-col overflow-hidden border border-slate-200 dark:border-slate-700 relative transition-all duration-200" :style="isDesktop ? { width: configCollapsed ? '88px' : col1Width + 'px' } : {}">
          <div class="h-14 px-3 border-b border-slate-200 dark:border-slate-700 flex items-center shrink-0" :class="configCollapsed ? 'justify-center' : 'justify-between'">
            <h2 v-show="!configCollapsed" class="text-sm font-medium text-slate-800 dark:text-white flex items-center gap-2 pl-1">Configuración</h2>
            <button @click="configCollapsed = !configCollapsed" class="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors shrink-0" :title="configCollapsed ? 'Expandir' : 'Colapsar'">
              <PanelLeft class="w-4 h-4" />
            </button>
          </div>
          <!-- Resumen colapsado -->
          <div v-if="configCollapsed && isDesktop" class="flex-1 flex flex-col items-center gap-3 py-4 overflow-hidden">
            <template v-if="selectedGradoId">
              <div class="flex flex-col items-center gap-1 w-full px-2">
                <GraduationCap class="w-3.5 h-3.5 text-slate-400 shrink-0" />
                <span class="text-[9px] text-slate-600 dark:text-slate-300 text-center leading-tight w-full truncate">
                  {{ gradoOptions.find((g: any) => g.id === selectedGradoId)?.label ?? '—' }}
                </span>
              </div>
              <div class="w-8 h-px bg-slate-200 dark:bg-slate-700 shrink-0" />
            </template>
            <template v-if="selectedCompetenciaId">
              <div class="flex flex-col items-center gap-1 w-full px-2">
                <Brain class="w-3.5 h-3.5 text-slate-400 shrink-0" />
                <span class="text-[9px] font-bold text-indigo-500 text-center">
                  C{{ competencias.find((c: any) => c.id === selectedCompetenciaId)?.codigo ?? '' }}
                </span>
              </div>
              <div class="w-8 h-px bg-slate-200 dark:bg-slate-700 shrink-0" />
            </template>
            <div class="flex flex-col items-center gap-1 shrink-0">
              <Target class="w-3.5 h-3.5 text-slate-400" />
              <span class="text-[9px] font-semibold"
                :class="selectedNivelDificultad === 'basico' ? 'text-green-500' : selectedNivelDificultad === 'avanzado' ? 'text-red-500' : 'text-amber-500'">
                {{ selectedNivelDificultad === 'basico' ? 'Bás' : selectedNivelDificultad === 'intermedio' ? 'Int' : 'Ava' }}
              </span>
            </div>
            <template v-if="selectedDesempenosCount > 0">
              <div class="w-8 h-px bg-slate-200 dark:bg-slate-700 shrink-0" />
              <div class="flex flex-col items-center gap-1 shrink-0">
                <Hash class="w-3.5 h-3.5 text-slate-400" />
                <span class="text-[11px] font-bold text-indigo-500">{{ selectedDesempenosCount }}</span>
              </div>
            </template>
          </div>

          <div v-show="!configCollapsed" class="flex-1 overflow-y-auto custom-scrollbar p-4 space-y-6">
            
            <div class="space-y-3">
              <label class="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center gap-2"><GraduationCap class="w-3.5 h-3.5"/> Público Objetivo</label>
              <div v-if="loadingGrados" class="h-10 bg-slate-50 dark:bg-slate-950 rounded-xl animate-pulse"></div>
              <ComboBox v-else v-model="selectedGradoId" :options="gradoOptions" placeholder="Seleccionar grado..." />
              
              <div class="flex p-1 bg-slate-50 dark:bg-slate-950 rounded-xl border border-slate-200 dark:border-slate-700">
                <button v-for="nivel in nivelesDificultad" :key="nivel.id" @click="selectedNivelDificultad = nivel.id"
                  class="flex-1 flex justify-center py-1.5 rounded-lg text-xs font-medium transition-all"
                  :class="selectedNivelDificultad === nivel.id ? 'bg-indigo-500 dark:bg-indigo-600 text-white shadow-sm dark:shadow-none' : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:text-slate-200'">
                  {{ nivel.nombre }}
                </button>
              </div>
            </div>

            <div class="space-y-3">
              <label class="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center gap-2"><Target class="w-3.5 h-3.5"/> Competencia</label>
              <div class="grid grid-cols-2 gap-2">
                <button
                    v-for="comp in competencias"
                    :key="comp.id"
                    @click="selectedCompetenciaId = comp.id"
                    class="p-2 rounded-xl border transition-all text-left flex flex-col gap-1"
                    :class="selectedCompetenciaId === comp.id ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-500/10' : 'border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 hover:border-slate-300'">
                    <div class="flex items-center gap-1.5">
                        <component :is="COMP_ICONS[comp.codigo]" class="w-3.5 h-3.5" :class="selectedCompetenciaId === comp.id ? 'text-indigo-600 dark:text-indigo-400' : 'text-slate-500'" />
                        <span class="text-[10px] font-bold" :class="selectedCompetenciaId === comp.id ? 'text-indigo-700 dark:text-indigo-300' : 'text-slate-600 dark:text-slate-400'">C{{ comp.codigo }}</span>
                    </div>
                    <span class="text-[10px] font-medium leading-tight" :class="selectedCompetenciaId === comp.id ? 'text-indigo-800 dark:text-indigo-200' : 'text-slate-500 dark:text-slate-400'">{{ getCompVisual(comp.codigo).shortName }}</span>
                </button>
              </div>
            </div>

            <div class="space-y-3">
              <label class="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center gap-2"><BookOpen class="w-3.5 h-3.5"/> Contexto / Problema</label>
              <input type="text" v-model="contenidoTematico" placeholder="Ej: fracciones, geometría..." class="w-full h-10 px-3 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-700 rounded-xl text-xs font-medium text-slate-600 dark:text-slate-300 focus:border-slate-300 dark:border-slate-500 outline-none" />
              
              <div class="pt-2">
                <Checkbox v-model="useTextoBase" class="flex items-center gap-2 text-slate-600 dark:text-slate-300 mb-2">
                  <span class="text-xs font-medium">Usar Problema Base (Archivo)</span>
                </Checkbox>
                
                <div v-if="useTextoBase" class="space-y-2">
                    <div v-if="selectedFiles.length === 0 && !uploadingFile" class="relative">
                        <input type="file" accept=".pdf,.docx,.doc" multiple
                            @change="(e) => handleFileUpload(e)"
                            class="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10" />
                        <div class="flex items-center justify-center py-2 px-3 bg-slate-50 dark:bg-slate-950 border border-dashed border-slate-300 dark:border-slate-600 rounded-xl hover:border-indigo-400 transition-all duration-300">
                            <span class="text-slate-500 dark:text-slate-400 text-xs font-medium flex items-center gap-1.5"><CloudUpload class="w-4 h-4"/> PDF o Word</span>
                        </div>
                    </div>

                    <div v-if="uploadingFile"
                        class="flex items-center justify-center gap-2 py-2 bg-indigo-50 dark:bg-indigo-900/20 rounded-xl">
                        <Loader2 class="w-4 h-4 text-indigo-600 animate-spin" />
                        <span class="text-indigo-600 dark:text-indigo-400 text-xs font-medium">Procesando...</span>
                    </div>

                    <div v-if="selectedFiles.length > 0 && !uploadingFile && filesMetadata" class="space-y-2">
                        <div v-for="(archivo, index) in filesMetadata.archivos" :key="index"
                            class="flex items-center gap-2 p-2 bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-200 dark:border-indigo-800 rounded-xl text-xs">
                            <FileText class="w-3.5 h-3.5 text-indigo-600 dark:text-indigo-400 flex-shrink-0" />
                            <span class="flex-1 truncate text-slate-700 dark:text-slate-200 font-medium">{{ archivo.filename }}</span>
                        </div>
                        <button @click="clearFiles"
                            class="text-[10px] text-red-500 hover:text-red-600 flex items-center gap-1 font-medium">
                            <X class="w-3 h-3" /> Quitar archivos
                        </button>
                    </div>
                </div>
              </div>
            </div>

            <div class="space-y-4">
              <label class="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center gap-2"><Hash class="w-3.5 h-3.5"/> Cantidad de Preguntas</label>
              
              <div class="flex items-center gap-3 bg-slate-50 dark:bg-slate-950 p-3 rounded-xl border border-slate-200 dark:border-slate-700">
                <input type="range" v-model.number="cantidadPreguntas" min="1" max="20" class="flex-1 h-1 bg-slate-200 dark:bg-slate-700 rounded-full appearance-none accent-indigo-500" />
                <span class="w-6 text-center text-sm font-bold text-slate-800 dark:text-white">{{ cantidadPreguntas }}</span>
              </div>
            </div>

          </div>
        </aside>

        <!-- Splitter 1 -->
        <div v-if="!configCollapsed" class="hidden lg:flex w-2 cursor-col-resize shrink-0 hover:bg-slate-100 dark:bg-slate-800/50 items-center justify-center rounded transition-colors group" @mousedown.prevent="onMouseDownCol1">
          <div class="w-1 h-6 bg-white/20 rounded-full group-hover:bg-indigo-500/50 transition-colors"></div>
        </div>

        <!-- COLUMN 2: Resultados -->
        <main v-show="isDesktop || mobileTab === 'results'" class="flex-1 min-w-0 bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 flex flex-col overflow-hidden relative">
          <MatSistemResults :resultado="resultado" :loading="loading" :show-results="showResults" :descargando-word="descargandoWord" :fill-height="true" @descargar-examen-word="descargarExamenWord" />
        </main>

        <!-- Splitter 2 -->
        <div v-if="!desempenosCollapsed" class="hidden lg:flex w-2 cursor-col-resize shrink-0 hover:bg-slate-100 dark:bg-slate-800/50 items-center justify-center rounded transition-colors group" @mousedown.prevent="onMouseDownCol3">
          <div class="w-1 h-6 bg-white/20 rounded-full group-hover:bg-indigo-500/50 transition-colors"></div>
        </div>

        <!-- COLUMN 3: Desempeños -->
        <aside v-show="isDesktop || mobileTab === 'desempenos'" class="flex-1 lg:flex-none shrink-0 bg-white dark:bg-slate-800 rounded-xl flex flex-col overflow-hidden border border-slate-200 dark:border-slate-700 relative transition-all duration-200" :style="isDesktop ? { width: desempenosCollapsed ? '88px' : col3Width + 'px' } : {}">
          <MatSistemDesempenos
            :desempenos="desempenos" :selected-desempenos-count="selectedDesempenosCount"
            :loading-desempenos="loadingDesempenos" :selected-grado-id="selectedGradoId"
            v-model:active-capacidad-tab="activeCapacidadTab"
            :desempenos-por-capacidad="desempenosPorCapacidad"
            v-model:selected-desempeno-ids="selectedDesempenoIds"
            :loading="loading" :error="error" :capacidades-actuales="capacidadesActuales"
            :fill-height="true"
            :collapsed="desempenosCollapsed"
            @select-all-capacidad="selectAllCapacidad"
            @deselect-all-capacidad="deselectAllCapacidad"
            @deselect-all="deselectAll"
            @generar-preguntas="onGenerarPreguntas"
            @toggle-collapse="desempenosCollapsed = !desempenosCollapsed" />
        </aside>
        
        <!-- Mobile Bottom Navigation (Android Style) -->
        <div v-show="!isDesktop" class="shrink-0 flex items-center justify-around bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-1 mt-auto">
          <button @click="mobileTab = 'config'" class="flex-1 py-2 flex flex-col items-center justify-center gap-1 rounded-lg transition-colors" :class="mobileTab === 'config' ? 'text-slate-800 dark:text-white bg-slate-100 dark:bg-slate-800/50' : 'text-slate-500'">
            <LayoutGrid class="w-5 h-5" />
            <span class="text-[10px] font-medium">Configuración</span>
          </button>
          <button @click="mobileTab = 'desempenos'" class="flex-1 py-2 flex flex-col items-center justify-center gap-1 rounded-lg transition-colors" :class="mobileTab === 'desempenos' ? 'text-slate-800 dark:text-white bg-slate-100 dark:bg-slate-800/50' : 'text-slate-500'">
            <Target class="w-5 h-5" />
            <span class="text-[10px] font-medium">Desempeños</span>
          </button>
          <button @click="mobileTab = 'results'" class="flex-1 py-2 flex flex-col items-center justify-center gap-1 rounded-lg transition-colors" :class="mobileTab === 'results' ? 'text-slate-800 dark:text-white bg-slate-100 dark:bg-slate-800/50' : 'text-slate-500'">
            <Sparkles class="w-5 h-5" />
            <span class="text-[10px] font-medium">Examen</span>
          </button>
        </div>
      </div>

      <!-- ══════════════════════════════════════════
           HISTORIAL TAB
      ══════════════════════════════════════════ -->
      <div v-show="activeTab === 'historial'" class="flex-1 min-h-0 bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden p-6 flex flex-col">
        <div v-if="loadingHistory" class="flex-1 flex flex-col items-center justify-center">
          <Loader2 class="w-8 h-8 text-slate-800 dark:text-white animate-spin mb-4" />
          <p class="text-slate-500 dark:text-slate-400 text-sm">Cargando historial...</p>
        </div>
        <div v-else-if="fetchError" class="flex-1 flex flex-col items-center justify-center gap-3">
          <p class="text-red-400 text-sm text-center">{{ fetchError }}</p>
          <button @click="fetchHistory()" class="text-xs px-3 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors">Reintentar</button>
        </div>
        <div v-else-if="history.length === 0" class="flex-1 flex flex-col items-center justify-center">
          <History class="w-10 h-10 text-slate-800 dark:text-white/20 mx-auto mb-4" />
          <h3 class="text-slate-800 dark:text-white font-medium mb-2">Sin exámenes guardados</h3>
          <p class="text-slate-500 dark:text-slate-400 text-sm max-w-md mx-auto text-center">Los exámenes que generes se guardarán automáticamente aquí.</p>
        </div>
        <div v-else class="flex-1 overflow-y-auto space-y-4">
          <div class="flex items-center justify-between">
            <h3 class="text-slate-800 dark:text-white font-medium flex items-center gap-2">Exámenes Generados ({{ history.length }})</h3>
            <button @click="confirmarLimpiarHistorial" class="text-xs text-red-400 hover:text-red-300 font-medium px-3 py-1.5 rounded-lg bg-red-400/10 hover:bg-red-400/20 transition-colors">Limpiar todo</button>
          </div>
          <div class="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div v-for="(entry, index) in history" :key="entry.id" class="bg-slate-50 dark:bg-slate-950 rounded-xl border border-slate-200 dark:border-slate-700 p-4 flex flex-col gap-3">
              <div>
                <h4 class="text-sm font-medium text-slate-800 dark:text-white truncate">{{ entry.resultado.examen.titulo }}</h4>
                <div class="text-[11px] text-slate-500 mt-1">{{ formatFechaHora(entry.fechaCreacion) }}</div>
              </div>
              <div class="text-[11px] text-slate-500 dark:text-slate-400">
                <div>Grado: {{ entry.gradoLabel }}</div>
                <div>Preguntas: {{ entry.resultado.total_preguntas }}</div>
              </div>
              <div class="flex gap-1 mt-auto overflow-x-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
                <button @click="cargarExamen(index)" class="shrink-0 flex items-center gap-1 px-1.5 py-1 text-[10px] font-medium text-slate-800 dark:text-white bg-slate-200 dark:bg-slate-700/50 rounded hover:bg-slate-300 dark:hover:bg-slate-600"><Eye class="w-3 h-3" />Ver</button>
                <button @click="descargarWordHistorial(index)" class="shrink-0 flex items-center gap-1 px-1.5 py-1 text-[10px] font-medium text-slate-800 dark:text-white bg-slate-200 dark:bg-slate-700/50 rounded hover:bg-slate-300 dark:hover:bg-slate-600"><FileDown class="w-3 h-3" />Word</button>
                <!-- <button @click="vincularDesdeHistorial(index)" class="shrink-0 flex items-center gap-1 px-1.5 py-1 text-[10px] font-medium text-slate-800 dark:text-white bg-slate-200 dark:bg-slate-700/50 rounded hover:bg-slate-300 dark:hover:bg-slate-600"><Link class="w-3 h-3" />Vincular</button> -->
                <button @click="abrirAsignar(entry)" class="shrink-0 flex items-center gap-1 px-1.5 py-1 text-[10px] font-medium text-slate-800 dark:text-white bg-slate-200 dark:bg-slate-700/50 rounded hover:bg-slate-300 dark:hover:bg-slate-600"><Send class="w-3 h-3" />Asignar</button>
                <button @click="confirmarEliminar(entry.id)" class="shrink-0 px-1.5 py-1 text-[10px] font-medium text-red-400 bg-red-400/10 rounded hover:bg-red-400/20"><Trash2 class="w-3 h-3"/></button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ══════════════════════════════════════════
           SISTEMATIZADOR TAB
      ══════════════════════════════════════════ -->
      <!-- <div v-show="activeTab === 'sistematizador'" class="flex-1 min-h-0 bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden">
        <Sistematizador />
      </div> -->

    </div>

    <!-- Modals go here -->
    <MatSistemExamPreviewModal :entry="previewEntry" :loading-delete="loadingDelete === previewEntry?.id" :is-loading="!!loadingPreview" :downloading-word="downloadingPreviewWord" @close="previewEntry = null" @eliminar="onPreviewEliminar" @descargar-word="descargarWordDesdePreview" />
    
    <!-- Asignar Examen Modal -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="asignarModal" class="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div class="absolute inset-0 bg-slate-50 dark:bg-slate-950/80 backdrop-blur-sm -z-10" @click="asignarModal = null"></div>
          <div class="bg-white dark:bg-slate-800 rounded-2xl w-full max-w-md shadow-2xl border border-slate-300 dark:border-slate-600 flex flex-col">
            <div class="px-5 py-4 border-b border-slate-300 dark:border-slate-600 flex items-center justify-between"><h3 class="text-slate-800 dark:text-white font-medium text-lg">Asignar Examen</h3><button @click="asignarModal = null" class="text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:text-white"><X class="w-5 h-5"/></button></div>
            <div class="p-5 space-y-4">
              <div><label class="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">Sección (opcional)</label><select v-model="asignarForm.seccion" class="w-full bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-slate-800 dark:text-white text-sm outline-none focus:border-indigo-500"><option value="">— Todas las secciones —</option><option value="A">A</option><option value="B">B</option><option value="C">C</option><option value="D">D</option><option value="E">E</option><option value="F">F</option><option value="G">G</option><option value="H">H</option><option value="I">I</option><option value="J">J</option><option value="Única">Única</option></select></div>
              <div><label class="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">Fecha Programada</label><input v-model="asignarForm.fecha" type="date" class="w-full bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-slate-800 dark:text-white text-sm outline-none focus:border-indigo-500"></div>
              <div class="grid grid-cols-2 gap-3">
                <div><label class="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">Hora Inicio</label><input v-model="asignarForm.hora_inicio" type="time" class="w-full bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-slate-800 dark:text-white text-sm outline-none focus:border-indigo-500"></div>
                <div><label class="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">Hora Fin</label><input v-model="asignarForm.hora_fin" type="time" class="w-full bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2 text-slate-800 dark:text-white text-sm outline-none focus:border-indigo-500"></div>
              </div>
              <div class="pt-2 space-y-3">
                <Checkbox v-model="asignarForm.mezclar_preguntas"><span class="text-sm text-slate-600 dark:text-slate-300">Mezclar orden de preguntas</span></Checkbox>
                <Checkbox v-model="asignarForm.mezclar_alternativas"><span class="text-sm text-slate-600 dark:text-slate-300">Mezclar alternativas</span></Checkbox>
              </div>
            </div>
            <div class="p-5 border-t border-slate-300 dark:border-slate-600 flex justify-end gap-3"><button @click="asignarModal = null" class="px-4 py-2 text-sm font-medium text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:text-white">Cancelar</button><button @click="confirmarAsignar" :disabled="loadingAsignar" class="px-5 py-2 bg-white text-black text-sm font-medium rounded-lg hover:bg-slate-200 disabled:opacity-50 flex items-center gap-2"><Loader2 v-if="loadingAsignar" class="w-4 h-4 animate-spin"/> Asignar</button></div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
@keyframes robot-float-mat {
  0%, 100% {
    transform: translateY(0) rotate(0deg) scale(1);
  }
  25% {
    transform: translateY(-2px) rotate(-8deg) scale(1.1);
  }
  75% {
    transform: translateY(-2px) rotate(8deg) scale(1.1);
  }
}

.animate-robot-mat {
  animation: robot-float-mat 4s ease-in-out infinite;
  transform-origin: center bottom;
}
</style>
