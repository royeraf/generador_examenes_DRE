<script setup lang="ts">
import { computed } from 'vue';
import {
    Target,
    BookOpen,
    Rocket,
    AlertTriangle,
    CircleDot,
    PanelRight
} from 'lucide-vue-next';
import Checkbox from '../../../shared/components/Checkbox.vue';
import BaseButton from '../../../shared/components/BaseButton.vue';
import type { DesempenoMatCompleto, CapacidadMatConCompetencia } from '../../../shared/types/matematica';

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
    capacidadesActuales: CapacidadMatConCompetencia[];
    fillHeight?: boolean;
    collapsed?: boolean;
}>();

const emit = defineEmits<{
    (e: 'update:activeCapacidadTab', value: number): void;
    (e: 'update:selectedDesempenoIds', value: number[]): void;
    (e: 'select-all-capacidad', orden: number): void;
    (e: 'deselect-all-capacidad', orden: number): void;
    (e: 'deselect-all'): void;
    (e: 'generar-preguntas'): void;
    (e: 'toggle-collapse'): void;
}>();

const localSelectedDesempenoIds = computed({
    get: () => props.selectedDesempenoIds,
    set: (val) => emit('update:selectedDesempenoIds', val)
});

// Selected count per capacidad tab
const selectedCountPerCap = computed(() => {
    const counts: Record<number, number> = {};
    for (const orden of [1, 2, 3, 4]) {
        const ids = props.desempenosPorCapacidad[orden]?.map(d => d.id) || [];
        counts[orden] = ids.filter(id => props.selectedDesempenoIds.includes(id)).length;
    }
    return counts;
});

// Total desempeños per capacidad
const totalPerCap = computed(() => {
    const counts: Record<number, number> = {};
    for (const orden of [1, 2, 3, 4]) {
        counts[orden] = props.desempenosPorCapacidad[orden]?.length || 0;
    }
    return counts;
});

// Get capacidad display info
const getCapInfo = (orden: number) => {
    const cap = props.capacidadesActuales.find(c => c.orden === orden);
    return {
        nombre: cap?.nombre || `Capacidad ${orden}`,
        hasDesempenos: (totalPerCap.value[orden] ?? 0) > 0
    };
};

// Colors per capacidad
const CAP_COLORS: Record<number, { bg: string; bgActive: string; bgHover: string; text: string; textActive: string; border: string; ring: string; bgSelected: string; checkboxClass: string; dot: string }> = {
    1: {
        bg: 'bg-teal-50 dark:bg-teal-900/15',
        bgActive: 'bg-teal-500 dark:bg-teal-600',
        bgHover: 'hover:bg-teal-100/70 dark:hover:bg-teal-900/30 hover:text-teal-700 dark:hover:text-teal-300 hover:shadow-sm',
        text: 'text-teal-600 dark:text-teal-400',
        textActive: 'text-white',
        border: 'border-teal-200 dark:border-teal-800',
        ring: 'ring-teal-300 dark:ring-teal-700',
        bgSelected: 'bg-teal-50 dark:bg-teal-900/20',
        checkboxClass: 'checked:bg-teal-600 checked:border-teal-600 dark:checked:bg-teal-500 dark:checked:border-teal-500 focus:ring-teal-500/50',
        dot: 'text-teal-500'
    },
    2: {
        bg: 'bg-amber-50 dark:bg-amber-900/15',
        bgActive: 'bg-amber-500 dark:bg-amber-600',
        bgHover: 'hover:bg-amber-100/70 dark:hover:bg-amber-900/30 hover:text-amber-700 dark:hover:text-amber-300 hover:shadow-sm',
        text: 'text-amber-600 dark:text-amber-400',
        textActive: 'text-white',
        border: 'border-amber-200 dark:border-amber-800',
        ring: 'ring-amber-300 dark:ring-amber-700',
        bgSelected: 'bg-amber-50 dark:bg-amber-900/20',
        checkboxClass: 'checked:bg-amber-600 checked:border-amber-600 dark:checked:bg-amber-500 dark:checked:border-amber-500 focus:ring-amber-500/50',
        dot: 'text-amber-500'
    },
    3: {
        bg: 'bg-violet-50 dark:bg-violet-900/15',
        bgActive: 'bg-violet-500 dark:bg-violet-600',
        bgHover: 'hover:bg-violet-100/70 dark:hover:bg-violet-900/30 hover:text-violet-700 dark:hover:text-violet-300 hover:shadow-sm',
        text: 'text-violet-600 dark:text-violet-400',
        textActive: 'text-white',
        border: 'border-violet-200 dark:border-violet-800',
        ring: 'ring-violet-300 dark:ring-violet-700',
        bgSelected: 'bg-violet-50 dark:bg-violet-900/20',
        checkboxClass: 'checked:bg-violet-600 checked:border-violet-600 dark:checked:bg-violet-500 dark:checked:border-violet-500 focus:ring-violet-500/50',
        dot: 'text-violet-500'
    },
    4: {
        bg: 'bg-rose-50 dark:bg-rose-900/15',
        bgActive: 'bg-rose-500 dark:bg-rose-600',
        bgHover: 'hover:bg-rose-100/70 dark:hover:bg-rose-900/30 hover:text-rose-700 dark:hover:text-rose-300 hover:shadow-sm',
        text: 'text-rose-600 dark:text-rose-400',
        textActive: 'text-white',
        border: 'border-rose-200 dark:border-rose-800',
        ring: 'ring-rose-300 dark:ring-rose-700',
        bgSelected: 'bg-rose-50 dark:bg-rose-900/20',
        checkboxClass: 'checked:bg-rose-600 checked:border-rose-600 dark:checked:bg-rose-500 dark:checked:border-rose-500 focus:ring-rose-500/50',
        dot: 'text-rose-500'
    }
};

const DEFAULT_CAP_COLOR = CAP_COLORS[1]!;
const getCapColor = (orden: number) => CAP_COLORS[orden] ?? DEFAULT_CAP_COLOR;

// Are all desempeños in active tab selected?
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
                <h2 class="text-sm font-medium text-slate-800 dark:text-white flex items-center gap-2 pl-1">
                    <Target class="w-4 h-4 text-slate-500 dark:text-slate-400 shrink-0"/> Desempeños
                </h2>
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
                <span class="text-[11px] font-bold text-indigo-500">{{ selectedDesempenosCount }}</span>
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
        <div v-else-if="desempenos.length > 0" class="flex-1 flex flex-col min-h-0 overflow-hidden">

            <!-- Capacidad Tabs (fixed height to prevent card resize) -->
            <div class="bg-slate-100 dark:bg-slate-900/80 p-1.5 sm:p-2 border-b border-slate-300/60 dark:border-slate-700/60 flex-shrink-0 h-[56px] sm:h-[68px]">
                <div class="flex gap-1 sm:gap-1.5 h-full">
                    <button
                        v-for="orden in [1, 2, 3, 4]"
                        :key="orden"
                        @click="getCapInfo(orden).hasDesempenos && emit('update:activeCapacidadTab', orden)"
                        class="relative min-w-0 rounded-lg transition-all duration-300 text-left overflow-hidden"
                        :class="[
                            !getCapInfo(orden).hasDesempenos
                                ? 'opacity-40 cursor-not-allowed flex-1 px-3'
                                : activeCapacidadTab === orden
                                    ? `${getCapColor(orden).bgActive} shadow-lg flex-[2.5] px-3`
                                    : `${getCapColor(orden).bgHover} cursor-pointer flex-1 px-2`
                        ]"
                        :disabled="!getCapInfo(orden).hasDesempenos">

                        <div class="flex items-center gap-1 sm:gap-2 h-full">
                            <!-- Capacidad number badge -->
                            <span class="w-5 h-5 sm:w-6 sm:h-6 rounded-md flex items-center justify-center text-[10px] sm:text-xs font-black flex-shrink-0"
                                :class="activeCapacidadTab === orden
                                    ? 'bg-white/25 text-white'
                                    : `${getCapColor(orden).bg} ${getCapColor(orden).text}`">
                                {{ orden }}
                            </span>

                            <!-- Capacidad name: active wraps up to 2 lines, inactive truncates -->
                            <span class="text-[9px] sm:text-[11px] font-semibold leading-snug"
                                :class="activeCapacidadTab === orden
                                    ? 'text-white line-clamp-2'
                                    : 'text-slate-600 dark:text-slate-300 truncate'">
                                {{ getCapInfo(orden).nombre }}
                            </span>
                        </div>

                        <!-- Selected count badge -->
                        <span v-if="(selectedCountPerCap[orden] ?? 0) > 0"
                            class="absolute -top-1 -right-1 w-5 h-5 rounded-full text-[10px] font-bold flex items-center justify-center shadow-sm"
                            :class="activeCapacidadTab === orden
                                ? 'bg-red-500 text-white'
                                : `${getCapColor(orden).bgActive} text-white`">
                            {{ selectedCountPerCap[orden] }}
                        </span>
                    </button>
                </div>
            </div>

            <!-- Active Capacidad Info -->
            <div class="px-3 pt-3 pb-2 shrink-0">
                <div class="flex items-start gap-2 p-2.5 rounded-lg" :class="getCapColor(activeCapacidadTab).bg">
                    <CircleDot class="w-4 h-4 flex-shrink-0 mt-0.5" :class="getCapColor(activeCapacidadTab).text" />
                    <div class="flex-1 min-w-0">
                        <p class="text-xs font-bold" :class="getCapColor(activeCapacidadTab).text">
                            Capacidad {{ activeCapacidadTab }}:
                        </p>
                        <p class="text-[11px] text-slate-600 dark:text-slate-400 leading-snug mt-0.5">
                            {{ getCapInfo(activeCapacidadTab).nombre }}
                        </p>
                    </div>
                    <!-- Select all / none -->
                    <div class="flex gap-1 flex-shrink-0">
                        <button
                            v-if="!allSelectedInTab"
                            @click="emit('select-all-capacidad', activeCapacidadTab)"
                            class="text-[10px] font-semibold px-2 py-1 rounded-md transition-colors cursor-pointer"
                            :class="getCapColor(activeCapacidadTab).text + ' hover:bg-white/50 dark:hover:bg-slate-800/50'">
                            Todos
                        </button>
                        <button
                            v-else
                            @click="emit('deselect-all-capacidad', activeCapacidadTab)"
                            class="text-[10px] font-semibold px-2 py-1 rounded-md text-slate-500 hover:bg-white/50 dark:hover:bg-slate-800/50 transition-colors cursor-pointer">
                            Ninguno
                        </button>
                    </div>
                </div>
            </div>

            <!-- Desempeños List -->
            <div class="flex-1 overflow-y-auto custom-scrollbar p-3 space-y-1.5">
                <template v-if="desempenosPorCapacidad[activeCapacidadTab]?.length">
                    <Checkbox
                        v-for="des in desempenosPorCapacidad[activeCapacidadTab]"
                        :key="des.id"
                        v-model="localSelectedDesempenoIds"
                        :value="des.id"
                        class="group flex items-start gap-3 p-3 rounded-xl cursor-pointer transition-all duration-150 border"
                        :class="localSelectedDesempenoIds.includes(des.id)
                            ? `${getCapColor(activeCapacidadTab).bgSelected} ${getCapColor(activeCapacidadTab).border} ring-1 ${getCapColor(activeCapacidadTab).ring}`
                            : 'border-slate-300 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-800/50'"
                        :color="getCapColor(activeCapacidadTab).checkboxClass">
                        <div class="flex-1 min-w-0">
                            <div class="mb-1">
                                <span class="text-[9px] px-1.5 py-0.5 rounded font-mono bg-slate-100 dark:bg-slate-800/50 text-slate-500 dark:text-slate-400">
                                    {{ des.codigo }}
                                </span>
                            </div>
                            <p class="text-[11px] text-slate-700 dark:text-slate-300 leading-relaxed">
                                {{ des.descripcion }}
                            </p>
                        </div>
                    </Checkbox>
                </template>

                <!-- Empty Tab -->
                <div v-else class="py-8 text-center">
                    <p class="text-slate-400 dark:text-slate-500 text-sm">
                        No hay desempeños para esta capacidad en el grado seleccionado
                    </p>
                </div>
            </div>

        </div>

        <div v-else class="flex-1 flex flex-col items-center justify-center p-6 text-center">
            <BookOpen class="w-8 h-8 text-slate-600 dark:text-slate-400 mb-3" />
            <p class="text-xs text-slate-500 dark:text-slate-400">Selecciona un grado y una competencia para ver desempeños</p>
        </div>

        <!-- Generate Button fixed at bottom -->
        <div v-if="!collapsed" class="p-4 border-t border-slate-300 dark:border-slate-700 shrink-0 bg-white dark:bg-slate-800">
            <BaseButton variant="primary" block
                :disabled="loading || !selectedGradoId || selectedDesempenoIds.length === 0"
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
