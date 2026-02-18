<script setup lang="ts">
import { computed } from 'vue';
import {
    Target,
    BookOpen,
    Calculator,
    Sigma,
    Shapes,
    Rocket,
    AlertTriangle,
    Copy
} from 'lucide-vue-next';
import ThinkingLoader from '../ThinkingLoader.vue';
import Tooltip from '../Tooltip.vue';
import Checkbox from '../Checkbox.vue';
import type { DesempenoMatCompleto, CapacidadMatConCompetencia } from '../../types/matematica';

const props = defineProps<{
    desempenos: DesempenoMatCompleto[];
    selectedDesempenosCount: number;
    loadingDesempenos: boolean;
    selectedGradoId: number | null;
    activeCapacidadTab: number;
    desempenosPorCapacidad: Record<number, DesempenoMatCompleto[]>;
    selectedDesempenoIds: number[];
    loading: boolean;
    error: string | null;
    promptTexto: string;
    showPromptModal: boolean;
    capacidadesActuales: CapacidadMatConCompetencia[];
}>();

const emit = defineEmits<{
    (e: 'update:activeCapacidadTab', value: number): void;
    (e: 'update:selectedDesempenoIds', value: number[]): void;
    (e: 'update:showPromptModal', value: boolean): void;
    (e: 'selectAllCapacidad', orden: number): void;
    (e: 'deselectAllCapacidad', orden: number): void;
    (e: 'generarPreguntas'): void;
}>();

const localSelectedDesempenoIds = computed({
    get: () => props.selectedDesempenoIds,
    set: (val) => emit('update:selectedDesempenoIds', val)
});

// Helper - Obtener nombre corto de capacidad
const getCapacidadLabel = (orden: number): string => {
    const cap = props.capacidadesActuales.find(c => c.orden === orden);
    if (!cap) return `Cap. ${orden}`;
    // Extraer primeras 2-3 palabras
    const palabras = cap.nombre.split(' ').slice(0, 3).join(' ');
    return palabras.length > 25 ? palabras.substring(0, 25) + '...' : palabras;
};

// Helper - Obtener nombre completo de capacidad (para tooltips)
const getCapacidadFullName = (orden: number): string => {
    const cap = props.capacidadesActuales.find(c => c.orden === orden);
    return cap?.nombre || `Capacidad ${orden}`;
};

// Helper - Obtener color por orden de capacidad
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
                        <button @click="emit('update:activeCapacidadTab', orden)"
                            class="flex-1 min-w-[80px] relative px-2 sm:px-4 py-2 sm:py-2.5 text-[10px] sm:text-xs font-bold transition-all duration-300 rounded-lg whitespace-nowrap"
                            :class="activeCapacidadTab === orden
                                ? `${getCapacidadColor(orden).bg} text-white shadow-lg`
                                : 'text-slate-500 dark:text-slate-400 hover:bg-white dark:hover:bg-slate-800'">
                            <div class="flex items-center justify-center gap-1.5 sm:gap-2">
                                <Calculator v-if="orden === 1" class="w-3 h-3 sm:w-4 h-4" />
                                <Sigma v-else-if="orden === 2" class="w-3 h-3 sm:w-4 h-4" />
                                <Shapes v-else-if="orden === 3" class="w-3 h-3 sm:w-4 h-4" />
                                <Target v-else class="w-3 h-3 sm:w-4 h-4" />
                                <span class="hidden sm:inline truncate max-w-[80px]">{{ getCapacidadLabel(orden)
                                }}</span>
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
                            <button @click="emit('selectAllCapacidad', activeCapacidadTab)"
                                class="px-2.5 py-1 rounded-full transition-colors"
                                :class="getCapacidadColor(activeCapacidadTab).text + ' hover:bg-gray-100 dark:hover:bg-slate-800'">
                                Seleccionar todos
                            </button>
                            <button @click="emit('deselectAllCapacidad', activeCapacidadTab)"
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
                                <Checkbox v-model="localSelectedDesempenoIds" :value="des.id"
                                    class="group flex items-start gap-3 p-3 rounded-xl cursor-pointer transition-all duration-150 border"
                                    :class="localSelectedDesempenoIds.includes(des.id)
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
        <button @click="emit('generarPreguntas')"
            :disabled="loading || !selectedGradoId || selectedDesempenoIds.length === 0"
            class="w-full px-4 py-4 sm:px-6 sm:py-5 font-bold rounded-2xl transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 sm:gap-3 shadow-xl hover:shadow-2xl hover:-translate-y-1 text-base sm:text-lg"
            :class="loading
                ? 'bg-white dark:bg-slate-900 border-2 border-slate-200 dark:border-slate-700 shadow-lg cursor-wait'
                : 'bg-gradient-to-r from-indigo-500 via-indigo-600 to-purple-500 hover:from-indigo-600 hover:via-indigo-700 hover:to-purple-600 shadow-indigo-500/30 hover:shadow-indigo-500/40 text-white'">
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
        <button v-if="promptTexto" @click="emit('update:showPromptModal', true)"
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
</template>
