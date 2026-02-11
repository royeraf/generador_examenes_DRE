<script setup lang="ts">
import { computed } from 'vue';
import { Target, BookOpen, FileSearch, Lightbulb, Rocket, AlertTriangle, Copy } from 'lucide-vue-next';
import ThinkingLoader from '../ThinkingLoader.vue';
import Tooltip from '../Tooltip.vue';
import Checkbox from '../Checkbox.vue';
import type { DesempenoItem } from '../../types';

const props = defineProps<{
    desempenos: DesempenoItem[];
    selectedDesempenosCount: number;
    loadingDesempenos: boolean;
    selectedGradoId: number | null;
    activeCapacidadTab: string;
    desempenosPorCapacidad: Record<string, DesempenoItem[]>;
    selectedDesempenoIds: number[];
    loading: boolean;
    error: string | null;
    promptTexto: string;
    showPromptModal: boolean;
}>();

const emit = defineEmits<{
    (e: 'update:activeCapacidadTab', value: string): void;
    (e: 'update:selectedDesempenoIds', value: number[]): void;
    (e: 'update:showPromptModal', value: boolean): void;
    (e: 'select-all-capacidad', tipo: string): void;
    (e: 'deselect-all-capacidad', tipo: string): void;
    (e: 'generar-preguntas'): void;
}>();

const localSelectedDesempenoIds = computed({
    get: () => props.selectedDesempenoIds,
    set: (val) => emit('update:selectedDesempenoIds', val)
});

const getCapacidadLabel = (tipo: string): string => {
    const labels: Record<string, string> = {
        'literal': 'LITERAL',
        'inferencial': 'INFERENCIAL',
        'critico': 'CRÍTICO'
    };
    return labels[tipo] || tipo;
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

                <!-- Tab Navigation - Niveles de Comprensión -->
                <div class="flex overflow-x-auto scrollbar-hide bg-gray-50 dark:bg-slate-900 p-1.5 gap-1 min-w-full">
                    <Tooltip v-for="tipo in ['literal', 'inferencial', 'critico']" :key="tipo"
                        :text="getCapacidadLabel(tipo)" position="bottom">
                        <button @click="emit('update:activeCapacidadTab', tipo)"
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
                            <button @click="emit('select-all-capacidad', activeCapacidadTab)"
                                class="px-2.5 py-1 rounded-full transition-colors" :class="{
                                    'text-emerald-600 hover:bg-emerald-50 dark:text-emerald-400 dark:hover:bg-emerald-900/20': activeCapacidadTab === 'literal',
                                    'text-amber-600 hover:bg-amber-50 dark:text-amber-400 dark:hover:bg-amber-900/20': activeCapacidadTab === 'inferencial',
                                    'text-purple-600 hover:bg-purple-50 dark:text-purple-400 dark:hover:bg-purple-900/20': activeCapacidadTab === 'critico'
                                }">
                                Seleccionar todos
                            </button>
                            <button @click="emit('deselect-all-capacidad', activeCapacidadTab)"
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
                            </Tooltip>
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
        <button @click="emit('generar-preguntas')"
            :disabled="loading || !selectedGradoId || selectedDesempenoIds.length === 0"
            class="w-full px-4 py-4 sm:px-6 sm:py-5 text-white font-bold rounded-2xl transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 sm:gap-3 shadow-xl hover:shadow-2xl hover:-translate-y-1 text-base sm:text-lg"
            :class="loading
                ? 'bg-slate-900 dark:bg-slate-950 shadow-slate-500/20'
                : 'bg-gradient-to-r from-teal-500 via-teal-600 to-sky-500 hover:from-teal-600 hover:via-teal-700 hover:to-sky-600 shadow-teal-500/30 hover:shadow-teal-500/40'">
            <ThinkingLoader v-if="loading" text="Generando" variant="teal" />
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
