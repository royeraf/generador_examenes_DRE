<script setup lang="ts">
import { computed } from 'vue';
import { Target, BookOpen, FileSearch, Lightbulb, Rocket, AlertTriangle, PanelRight } from 'lucide-vue-next';
import Checkbox from '../../../shared/components/Checkbox.vue';
import BaseButton from '../../../shared/components/BaseButton.vue';
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

interface CapColor {
    bg: string;
    bgActive: string;
    text: string;
    border: string;
    ring: string;
    bgSelected: string;
    checkboxClass: string;
}

const CAP_COLORS: Record<string, CapColor> = {
    literal: {
        bg: 'bg-teal-50 dark:bg-teal-900/15',
        bgActive: 'bg-teal-500 dark:bg-teal-600',
        text: 'text-teal-600 dark:text-teal-400',
        border: 'border-teal-200 dark:border-teal-800',
        ring: 'ring-teal-300 dark:ring-teal-700',
        bgSelected: 'bg-teal-50 dark:bg-teal-900/20',
        checkboxClass: 'checked:bg-teal-600 checked:border-teal-600 dark:checked:bg-teal-500 dark:checked:border-teal-500 focus:ring-teal-500/50'
    },
    inferencial: {
        bg: 'bg-amber-50 dark:bg-amber-900/15',
        bgActive: 'bg-amber-500 dark:bg-amber-600',
        text: 'text-amber-600 dark:text-amber-400',
        border: 'border-amber-200 dark:border-amber-800',
        ring: 'ring-amber-300 dark:ring-amber-700',
        bgSelected: 'bg-amber-50 dark:bg-amber-900/20',
        checkboxClass: 'checked:bg-amber-600 checked:border-amber-600 dark:checked:bg-amber-500 dark:checked:border-amber-500 focus:ring-amber-500/50'
    },
    critico: {
        bg: 'bg-violet-50 dark:bg-violet-900/15',
        bgActive: 'bg-violet-500 dark:bg-violet-600',
        text: 'text-violet-600 dark:text-violet-400',
        border: 'border-violet-200 dark:border-violet-800',
        ring: 'ring-violet-300 dark:ring-violet-700',
        bgSelected: 'bg-violet-50 dark:bg-violet-900/20',
        checkboxClass: 'checked:bg-violet-600 checked:border-violet-600 dark:checked:bg-violet-500 dark:checked:border-violet-500 focus:ring-violet-500/50'
    }
};

const DEFAULT_CAP_COLOR = CAP_COLORS['literal']!;
const getCapColor = (tipo: string): CapColor => CAP_COLORS[tipo] ?? DEFAULT_CAP_COLOR;

const allSelectedInTab = computed(() => {
    const ids = props.desempenosPorCapacidad[props.activeCapacidadTab]?.map(d => d.id) || [];
    return ids.length > 0 && ids.every(id => props.selectedDesempenoIds.includes(id));
});
</script>

<template>
    <div class="flex flex-col h-full bg-transparent">
        
        <!-- Header -->
        <div class="h-14 px-3 border-b border-slate-300 dark:border-slate-700 flex items-center shrink-0" :class="collapsed ? 'justify-center' : 'justify-between'">
            <div v-show="!collapsed" class="flex items-center gap-2 min-w-0">
                <h2 class="text-sm font-medium text-slate-800 dark:text-white flex items-center gap-2 pl-1"><Target class="w-4 h-4 text-slate-500 dark:text-slate-400 shrink-0"/> Desempeños</h2>
                <span v-if="selectedDesempenosCount > 0" class="shrink-0 px-2 py-0.5 rounded-full text-[10px] bg-red-500 dark:bg-red-600 text-white font-bold shadow-sm">
                    {{ selectedDesempenosCount }}
                </span>
            </div>
            <button @click="emit('toggle-collapse')" class="hidden lg:inline-flex p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors shrink-0 cursor-pointer" :title="collapsed ? 'Expandir' : 'Colapsar'">
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
            <div class="flex p-2 gap-1 border-b border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-950/30 shrink-0">
                <div v-for="tipo in ['literal', 'inferencial', 'critico']" :key="tipo" class="flex-1">
                    <button @click="emit('update:activeCapacidadTab', tipo)"
                        class="w-full py-1.5 text-[10px] sm:text-xs font-medium rounded-lg transition-all flex items-center justify-center gap-1.5 cursor-pointer"
                        :class="activeCapacidadTab === tipo ? `${getCapColor(tipo).bgActive} text-white shadow-sm dark:shadow-none` : 'text-slate-500 hover:text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:bg-slate-800/50'">
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
                       <button v-if="!allSelectedInTab" @click="emit('select-all-capacidad', activeCapacidadTab)" class="text-[10px] font-semibold cursor-pointer" :class="getCapColor(activeCapacidadTab).text">Todos</button>
                       <button v-else @click="emit('deselect-all-capacidad', activeCapacidadTab)" class="text-[10px] text-slate-500 hover:text-slate-600 dark:text-slate-400 cursor-pointer">Ninguno</button>
                   </div>
                </div>

                <template v-if="desempenosPorCapacidad[activeCapacidadTab]?.length">
                    <Checkbox v-for="des in desempenosPorCapacidad[activeCapacidadTab]" :key="des.id"
                        v-model="localSelectedDesempenoIds" :value="des.id"
                        class="p-3 rounded-xl border cursor-pointer transition-all duration-150"
                        :class="localSelectedDesempenoIds.includes(des.id) ? `${getCapColor(activeCapacidadTab).bgSelected} ${getCapColor(activeCapacidadTab).border} ring-1 ${getCapColor(activeCapacidadTab).ring}` : 'bg-slate-50 dark:bg-slate-950 border-slate-300 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-800/50'"
                        :color="getCapColor(activeCapacidadTab).checkboxClass">
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
        <div v-if="!collapsed" class="p-4 border-t border-slate-300 dark:border-slate-700 shrink-0 bg-white dark:bg-slate-800">
            <BaseButton variant="primary" block
                :disabled="loading || !selectedGradoId || selectedDesempenoIds.length === 0 || isBreakdownValid === false"
                :loading="loading" @click="emit('generar-preguntas')">
                <template #icon><Rocket class="w-4 h-4" /></template>
                {{ loading ? 'Generando...' : 'Generar Examen' }}
            </BaseButton>
            <div v-if="error" class="mt-3 p-2 bg-red-500/10 border border-red-500/20 rounded-lg text-[10px] text-red-400 flex items-start gap-2">
                <AlertTriangle class="w-3.5 h-3.5 shrink-0 mt-0.5" />
                <p>{{ error }}</p>
            </div>
        </div>

    </div>
</template>
