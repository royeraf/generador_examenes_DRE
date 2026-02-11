<script setup lang="ts">
import { shallowRef, onMounted, computed } from 'vue';
import PromptModal from '../components/PromptModal.vue';
import Sistematizador from '../components/Sistematizador.vue';
import { useTheme } from '../composables/useTheme';
import {
  Brain,
  LayoutGrid,
  Sparkles,
  Award
} from 'lucide-vue-next';
import Footer from '../components/Footer.vue';
import Header from '../components/Header.vue';
import EduBackground from '../components/EduBackground.vue';
import { useMatSistem } from '../composables/useMatSistem';

// New Components
import MatSistemConfig from '../components/matsistem/MatSistemConfig.vue';
import MatSistemDesempenos from '../components/matsistem/MatSistemDesempenos.vue';
import MatSistemResults from '../components/matsistem/MatSistemResults.vue';

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
            :descargandoWord="descargandoWord" @descargarExamenWord="descargarExamenWord" />
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
