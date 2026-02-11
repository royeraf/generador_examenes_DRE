<script setup lang="ts">
import { shallowRef, onMounted, computed, watch, provide } from 'vue';
import PromptModal from '../components/PromptModal.vue';
import Sistematizador from '../components/Sistematizador.vue';
import { useTheme } from '../composables/useTheme';
import { useMatSistemHistory } from '../composables/useMatSistemHistory';
import { useMatSistem } from '../composables/useMatSistem';
import { showDeleteConfirm, Toast } from '../utils/swal';
import Footer from '../components/Footer.vue';
import Header from '../components/Header.vue';
import EduBackground from '../components/EduBackground.vue';
import MatSistemConfig from '../components/matsistem/MatSistemConfig.vue';
import MatSistemDesempenos from '../components/matsistem/MatSistemDesempenos.vue';
import MatSistemResults from '../components/matsistem/MatSistemResults.vue';
import MatSistemExamPreviewModal from '../components/matsistem/MatSistemExamPreviewModal.vue';
import type { ExamenHistoryEntry, FilaTablaRespuestas } from '../types';
import type { GradoMatematica, CompetenciaMatematica, DesempenoMatCompleto } from '../types/matematica';
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
  FileText
} from 'lucide-vue-next';

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

const { history, saveExam, removeExam, clearHistory } = useMatSistemHistory();

// Provide for Sistematizador linkage
const examForSistematizador = shallowRef<{ tablaRespuestas: FilaTablaRespuestas[]; gradoId: number | null } | null>(null);
provide('examForSistematizador', examForSistematizador);

const showPromptModal = shallowRef(false);
const previewEntry = shallowRef<ExamenHistoryEntry | null>(null);

// Auto-save exams to history
watch(resultado, (newVal) => {
  if (newVal) {
    const grado = (grados.value as GradoMatematica[]).find((g: GradoMatematica) => g.id === selectedGradoId.value);
    saveExam(newVal, grado ? `Grado ${grado.numero} - ${grado.nivel}` : newVal.grado);
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

// Computed - Prompt para generar examen de matemática (siguiendo formato MINEDU/Math_Jony)
const promptTexto = computed(() => {
  if (!selectedGradoId.value || selectedDesempenoIds.value.length === 0) return '';

  const grado = (grados.value as GradoMatematica[]).find((g: GradoMatematica) => g.id === selectedGradoId.value);
  const competencia = (competencias.value as CompetenciaMatematica[]).find((c: CompetenciaMatematica) => c.id === selectedCompetenciaId.value);

  // Agrupar desempeños por capacidad
  const desempenosPorCap: Record<number, DesempenoMatCompleto[]> = {};
  (desempenos.value as DesempenoMatCompleto[])
    .filter((d: DesempenoMatCompleto) => selectedDesempenoIds.value.includes(d.id))
    .forEach((d: DesempenoMatCompleto) => {
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

        <!-- MatSistemConfig -->
        <MatSistemConfig v-model:selectedNivelDificultad="selectedNivelDificultad"
          :nivelesDificultad="nivelesDificultad" v-model:selectedGradoId="selectedGradoId" :gradoOptions="gradoOptions"
          v-model:selectedCompetenciaId="selectedCompetenciaId" :competenciaOptions="competenciaOptions"
          v-model:cantidadPreguntas="cantidadPreguntas" v-model:useTextoBase="useTextoBase"
          :selectedFiles="selectedFiles" :filesMetadata="filesMetadata" :uploadingFile="uploadingFile"
          :uploadError="uploadError" @handleFileUpload="handleFileUpload" @clearFiles="clearFiles" />

        <!-- Main Content -->
        <div class="grid lg:grid-cols-2 gap-4 sm:gap-6">

          <!-- Left: Desempeños -->
          <MatSistemDesempenos :desempenos="desempenos" :selectedDesempenosCount="selectedDesempenosCount"
            :loadingDesempenos="loadingDesempenos" :selectedGradoId="selectedGradoId"
            v-model:activeCapacidadTab="activeCapacidadTab" :desempenosPorCapacidad="desempenosPorCapacidad"
            v-model:selectedDesempenoIds="selectedDesempenoIds" :loading="loading" :error="error"
            :promptTexto="promptTexto" v-model:showPromptModal="showPromptModal"
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
    <MatSistemExamPreviewModal :entry="previewEntry" @close="previewEntry = null" @vincular="onPreviewVincular"
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
