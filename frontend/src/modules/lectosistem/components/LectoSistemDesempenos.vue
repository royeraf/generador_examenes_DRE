<script setup lang="ts">
import { computed } from 'vue';
import { Target, BookOpen, FileSearch, Lightbulb, Rocket, AlertTriangle, PanelRight } from 'lucide-vue-next';
import ThinkingLoader from '../../../shared/components/ThinkingLoader.vue';
import Checkbox from '../../../shared/components/Checkbox.vue';
import type { DesempenoItem } from '../../../shared/types';

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
    isBreakdownValid?: boolean;
    fillHeight?: boolean;
    collapsed?: boolean;
}>();

const emit = defineEmits<{
    (e: 'update:activeCapacidadTab', value: string): void;
    (e: 'update:selectedDesempenoIds', value: number[]): void;
    (e: 'select-all-capacidad', tipo: string): void;
    (e: 'deselect-all-capacidad', tipo: string): void;
    (e: 'generar-preguntas'): void;
    (e: 'toggle-collapse'): void;
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
    <div class="flex flex-col h-full bg-transparent">
        
        <!-- Header -->
        <div class="h-14 px-3 border-b border-slate-200 dark:border-slate-700 flex items-center shrink-0" :class="collapsed ? 'justify-center' : 'justify-between'">
            <div v-show="!collapsed" class="flex items-center gap-2 min-w-0">
                <h2 class="text-sm font-medium text-slate-800 dark:text-white flex items-center gap-2 pl-1"><Target class="w-4 h-4 text-slate-500 dark:text-slate-400 shrink-0"/> Desempeños</h2>
                <span v-if="selectedDesempenosCount > 0" class="shrink-0 px-2 py-0.5 rounded text-[10px] bg-slate-200 dark:bg-slate-700/50 text-slate-800 dark:text-white font-medium">
                    {{ selectedDesempenosCount }}
                </span>
            </div>
            <button @click="emit('toggle-collapse')" class="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors shrink-0" :title="collapsed ? 'Expandir' : 'Colapsar'">
                <PanelRight class="w-4 h-4" />
            </button>
        </div>

        <!-- Resumen colapsado -->
        <div v-if="collapsed" class="flex-1 flex flex-col items-center gap-3 py-4 overflow-hidden">
            <div class="flex flex-col items-center gap-1">
                <Target class="w-3.5 h-3.5 text-slate-400" />
                <span class="text-[11px] font-bold text-teal-500">{{ selectedDesempenosCount }}</span>
                <span class="text-[9px] text-slate-400 text-center">selecc.</span>
            </div>
        </div>

        <!-- Loading Skeleton -->
        <div v-else-if="loadingDesempenos" class="flex-1 p-4 space-y-4">
            <div class="h-10 bg-slate-50 dark:bg-slate-950 rounded-lg animate-pulse"></div>
            <div class="space-y-3">
                <div v-for="i in 4" :key="i" class="h-20 bg-slate-50 dark:bg-slate-950 rounded-xl animate-pulse"></div>
            </div>
        </div>

        <!-- Content -->
        <div v-else-if="desempenos.length > 0" class="flex-1 flex flex-col min-h-0">
            
            <!-- Tabs L/I/C -->
            <div class="flex p-2 gap-1 border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950/30 shrink-0">
                <div v-for="tipo in ['literal', 'inferencial', 'critico']" :key="tipo" class="flex-1">
                    <button @click="emit('update:activeCapacidadTab', tipo)"
                        class="w-full py-1.5 text-[10px] sm:text-xs font-medium rounded-lg transition-all flex items-center justify-center gap-1.5"
                        :class="activeCapacidadTab === tipo ? 'bg-teal-500 dark:bg-teal-600 text-slate-800 dark:text-white shadow-sm dark:shadow-none' : 'text-slate-500 hover:text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:bg-slate-800/50'">
                        <BookOpen v-if="tipo === 'literal'" class="w-3.5 h-3.5" />
                        <FileSearch v-else-if="tipo === 'inferencial'" class="w-3.5 h-3.5" />
                        <Lightbulb v-else class="w-3.5 h-3.5" />
                        <span class="hidden sm:inline">{{ getCapacidadLabel(tipo) }}</span>
                        <span class="sm:hidden">{{ tipo.charAt(0).toUpperCase() }}</span>
                    </button>
                </div>
            </div>

            <!-- List -->
            <div class="flex-1 overflow-y-auto custom-scrollbar p-3 flex flex-col gap-2">
                <div class="flex justify-between items-center px-1 mb-1">
                   <span class="text-[10px] text-slate-500">Seleccionar desempeños</span>
                   <div class="flex gap-2">
                       <button @click="emit('select-all-capacidad', activeCapacidadTab)" class="text-[10px] text-sky-400 hover:text-sky-300">Todos</button>
                       <button @click="emit('deselect-all-capacidad', activeCapacidadTab)" class="text-[10px] text-slate-500 hover:text-slate-500 dark:text-slate-400">Ninguno</button>
                   </div>
                </div>

                <template v-if="desempenosPorCapacidad[activeCapacidadTab]?.length">
                    <Checkbox v-for="des in desempenosPorCapacidad[activeCapacidadTab]" :key="des.id"
                        v-model="localSelectedDesempenoIds" :value="des.id"
                        class="p-3 rounded-xl border transition-colors"
                        :class="localSelectedDesempenoIds.includes(des.id) ? 'bg-teal-500 dark:bg-teal-600 border-slate-300 dark:border-slate-600' : 'bg-slate-50 dark:bg-slate-950 border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:border-slate-600'"
                        color="checked:bg-sky-500 checked:border-sky-500 focus:ring-sky-500/50">
                        <div class="mb-1">
                            <span class="text-[9px] px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800/50 text-slate-500 dark:text-slate-400 font-mono">{{ des.codigo }}</span>
                        </div>
                        <p class="text-[11px] text-slate-600 dark:text-slate-300 leading-relaxed">{{ des.descripcion }}</p>
                    </Checkbox>
                </template>
                <div v-else class="py-8 text-center text-xs text-slate-500">No hay desempeños disponibles.</div>
            </div>

        </div>

        <div v-else class="flex-1 flex flex-col items-center justify-center p-6 text-center">
            <BookOpen class="w-8 h-8 text-slate-600 mb-3" />
            <p class="text-xs text-slate-500">Selecciona un grado para ver desempeños</p>
        </div>

        <!-- Generate Button fixed at bottom -->
        <div v-if="!collapsed" class="p-4 border-t border-slate-200 dark:border-slate-700 shrink-0 bg-white dark:bg-slate-800">
            <button @click="emit('generar-preguntas')"
                :disabled="loading || !selectedGradoId || selectedDesempenoIds.length === 0 || isBreakdownValid === false"
                class="w-full py-2.5 rounded-full font-medium transition-all flex items-center justify-center gap-2 text-sm"
                :class="loading ? 'bg-teal-500 dark:bg-teal-600 text-slate-500 dark:text-slate-400 cursor-wait' : (isBreakdownValid === false || !selectedGradoId || selectedDesempenoIds.length === 0 ? 'bg-slate-100 dark:bg-slate-800/50 text-slate-500 cursor-not-allowed' : 'bg-white text-black hover:bg-slate-200 shadow-lg')">
                <ThinkingLoader v-if="loading" text="Generando..." variant="teal" />
                <template v-else>
                    <Rocket class="w-4 h-4" /> Generar Examen
                </template>
            </button>
            <div v-if="error" class="mt-3 p-2 bg-red-500/10 border border-red-500/20 rounded-lg text-[10px] text-red-400 flex items-start gap-2">
                <AlertTriangle class="w-3.5 h-3.5 shrink-0 mt-0.5" />
                <p>{{ error }}</p>
            </div>
        </div>

    </div>
</template>
