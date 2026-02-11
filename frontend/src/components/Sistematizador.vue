<script setup lang="ts">
import { onMounted, inject, watch, type Ref } from 'vue';
import {
    Settings,
    ClipboardList,
    BarChart3
} from 'lucide-vue-next';
import { useSistematizador } from '../composables/useSistematizador';
import { mapExamToNiveles } from '../composables/useExamHistory';
import { showConfirm } from '../utils/swal';
import SistematizadorConfig from './sistematizador/SistematizadorConfig.vue';
import SistematizadorRegistro from './sistematizador/SistematizadorRegistro.vue';
import SistematizadorResultados from './sistematizador/SistematizadorResultados.vue';
import type { FilaTablaRespuestas } from '../types';

const {
    selectedGradoId,
    activeTab,
    niveles,
    competencia,
    estudiantes,
    availableDesempenos,
    gradoOptions,
    desempenoOptions,
    stats,
    loadGrados,
    loadDesempenos,
    addPregunta,
    removePregunta,
    onDesempenoSelect,
    addEstudiante,
    removeEstudiante,
    calcularResultados,
    exportarExcel,
    descargarPlantillaExcel,
    importarExcel
} = useSistematizador();

// Inject exam data from LectoSistemView
const examForSistematizador = inject<Ref<{ tablaRespuestas: FilaTablaRespuestas[]; gradoId: number | null } | null>>('examForSistematizador');

watch(() => examForSistematizador?.value, async (data) => {
    if (!data) return;

    // Check if there are existing questions
    const hasExisting = Object.values(niveles).some(n => n.preguntas.length > 0);
    if (hasExisting) {
        const confirmed = await showConfirm(
            '¿Reemplazar configuración?',
            'Esto reemplazará la configuración actual del Sistematizador.'
        );
        if (!confirmed) {
            if (examForSistematizador) examForSistematizador.value = null;
            return;
        }
    }

    // Set grade if provided
    if (data.gradoId && data.gradoId !== selectedGradoId.value) {
        selectedGradoId.value = data.gradoId;
        // Wait for desempeños to load
        await loadDesempenos();
    }

    // Map exam answers to niveles
    const mapped = mapExamToNiveles(data.tablaRespuestas, availableDesempenos.value);
    for (const [key, preguntas] of Object.entries(mapped)) {
        if (niveles[key]) {
            niveles[key].preguntas = preguntas;
        }
    }

    activeTab.value = 'config';

    // Clear the signal
    if (examForSistematizador) examForSistematizador.value = null;
}, { deep: true });

// Lifecycle
onMounted(() => {
    loadGrados();
    const saved = localStorage.getItem('lectoSistemData');
    if (saved) {
        try {
            const data = JSON.parse(saved);
            if (data.competencia) competencia.value = data.competencia;
            if (data.estudiantes) estudiantes.value = data.estudiantes;
        } catch (e) {
            console.error("Local Storage Error", e);
        }
    }
});
</script>

<template>
    <div class="lectosistem-theme">
        <!-- Header Nav within Component - Educativo -->
        <div class="mb-6 overflow-x-auto pb-2 scrollbar-hide">
            <div
                class="flex gap-1 sm:gap-2 p-1.5 sm:p-2 bg-white dark:bg-slate-800 rounded-2xl shadow-lg border border-gray-100 dark:border-slate-700 w-fit min-w-max">
                <button @click="activeTab = 'config'"
                    class="flex items-center gap-2 px-3 py-2 sm:px-5 sm:py-3 rounded-xl text-xs sm:text-sm font-bold transition-all duration-300 whitespace-nowrap"
                    :class="activeTab === 'config' ? 'bg-gradient-to-r from-teal-500 to-sky-500 text-white shadow-lg shadow-teal-500/30' : 'text-slate-600 dark:text-slate-400 hover:bg-teal-50 dark:hover:bg-slate-700'">
                    <Settings class="w-4 h-4 sm:w-5 sm:h-5" />
                    <span>Configuración</span>
                </button>
                <button @click="activeTab = 'registro'"
                    class="flex items-center gap-2 px-3 py-2 sm:px-5 sm:py-3 rounded-xl text-xs sm:text-sm font-bold transition-all duration-300 whitespace-nowrap"
                    :class="activeTab === 'registro' ? 'bg-gradient-to-r from-amber-500 to-orange-500 text-white shadow-lg shadow-amber-500/30' : 'text-slate-600 dark:text-slate-400 hover:bg-amber-50 dark:hover:bg-slate-700'">
                    <ClipboardList class="w-4 h-4 sm:w-5 sm:h-5" />
                    <span>Registro</span>
                </button>
                <button @click="activeTab = 'resultados'"
                    class="flex items-center gap-2 px-3 py-2 sm:px-5 sm:py-3 rounded-xl text-xs sm:text-sm font-bold transition-all duration-300 whitespace-nowrap"
                    :class="activeTab === 'resultados' ? 'bg-gradient-to-r from-violet-500 to-purple-500 text-white shadow-lg shadow-violet-500/30' : 'text-slate-600 dark:text-slate-400 hover:bg-violet-50 dark:hover:bg-slate-700'">
                    <BarChart3 class="w-4 h-4 sm:w-5 sm:h-5" />
                    <span>Resultados</span>
                </button>
            </div>
        </div>

        <!-- Active Content -->
        <div class="tab-content transition-all duration-300">
            <!-- Tab 1: Config -->
            <SistematizadorConfig v-show="activeTab === 'config'" v-model:selectedGradoId="selectedGradoId"
                v-model:competencia="competencia" :gradoOptions="gradoOptions" :niveles="niveles"
                :desempenoOptions="desempenoOptions" @onDesempenoSelect="onDesempenoSelect" @addPregunta="addPregunta"
                @removePregunta="removePregunta" />

            <!-- Tab 2: Registro -->
            <SistematizadorRegistro v-show="activeTab === 'registro'" :estudiantes="estudiantes" :niveles="niveles"
                @addEstudiante="addEstudiante" @calcularResultados="calcularResultados"
                @removeEstudiante="removeEstudiante" @descargarPlantilla="descargarPlantillaExcel"
                @importarExcel="importarExcel" />

            <!-- Tab 3: Resultados -->
            <SistematizadorResultados v-show="activeTab === 'resultados'" :stats="stats" :estudiantes="estudiantes"
                @exportarExcel="exportarExcel" />
        </div>
    </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* Add some custom animations */
@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(10px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.animate-fadeIn {
    animation: fadeIn 0.3s ease-out forwards;
}
</style>
