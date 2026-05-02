<script setup lang="ts">
import { computed } from 'vue';
import { Signal, Sprout, Leaf, TreeDeciduous, Check, GraduationCap, Hash, FileUp, FileText, BookOpen, LayoutGrid } from 'lucide-vue-next';
import ComboBox from '../../../shared/components/ComboBox.vue';
import Checkbox from '../../../shared/components/Checkbox.vue';
import type { NivelDificultadOption, TextoBaseItem } from '../composables/useLectoSistem';

const props = defineProps<{
    nivelesDificultad: NivelDificultadOption[];
    modeloNivelDificultad: string;
    gradoOptions: { id: number; label: string; group: string }[];
    modeloGradoId: number | null;
    loadingGrados?: boolean;
    modeloCantidadPreguntas: number;
    modeloUseTextoBase: boolean;
    textosBase: TextoBaseItem[];
    tipoTextualOptions?: { id: string; label: string }[];
    modeloTipoTextual?: string | null;
    formatoTextualOptions?: { id: string; label: string }[];
    modeloFormatoTextual?: string | null;
    modeloCantidadLiteral: number;
    modeloCantidadInferencial: number;
    modeloCantidadCritico: number;
    isBreakdownValid: boolean;
    totalBreakdown: number;
}>();

const emit = defineEmits<{
    (e: 'update:modeloNivelDificultad', value: string): void;
    (e: 'update:modeloGradoId', value: number | null): void;
    (e: 'update:modeloCantidadPreguntas', value: number): void;
    (e: 'update:modeloUseTextoBase', value: boolean): void;
    (e: 'update:modeloTipoTextual', value: string | null): void;
    (e: 'update:modeloFormatoTextual', value: string | null): void;
    (e: 'update:modeloCantidadLiteral', value: number): void;
    (e: 'update:modeloCantidadInferencial', value: number): void;
    (e: 'update:modeloCantidadCritico', value: number): void;
    (e: 'open-textos-modal'): void;
}>();

const selectedNivelDificultad = computed({
    get: () => props.modeloNivelDificultad,
    set: (val) => emit('update:modeloNivelDificultad', val)
});
const selectedGradoId = computed({
    get: () => props.modeloGradoId,
    set: (val) => emit('update:modeloGradoId', val)
});
const quantity = computed({
    get: () => props.modeloCantidadPreguntas,
    set: (val) => emit('update:modeloCantidadPreguntas', val)
});
const useTextoBase = computed({
    get: () => props.modeloUseTextoBase,
    set: (val) => emit('update:modeloUseTextoBase', val)
});
const selectedTipoTextual = computed({
    get: () => props.modeloTipoTextual ?? null,
    set: (val) => emit('update:modeloTipoTextual', val)
});
const selectedFormatoTextual = computed({
    get: () => props.modeloFormatoTextual ?? null,
    set: (val) => emit('update:modeloFormatoTextual', val)
});
const qLiteral = computed({
    get: () => props.modeloCantidadLiteral,
    set: (val) => emit('update:modeloCantidadLiteral', val)
});
const qInferencial = computed({
    get: () => props.modeloCantidadInferencial,
    set: (val) => emit('update:modeloCantidadInferencial', val)
});
const qCritico = computed({
    get: () => props.modeloCantidadCritico,
    set: (val) => emit('update:modeloCantidadCritico', val)
});
</script>

<template>
    <div class="mb-6">
        <!-- Nivel de Dificultad -->
        <div class="mb-4 sm:mb-6 bg-white dark:bg-slate-800 rounded-2xl p-4 sm:p-5 border-2 border-violet-100 dark:border-slate-700 shadow-sm hover:shadow-md hover:border-violet-200 transition-all duration-300">
            <label class="flex items-center gap-2 text-sm font-bold text-slate-700 dark:text-slate-300 mb-3">
                <div class="w-8 h-8 bg-gradient-to-br from-violet-500 to-purple-600 rounded-lg flex items-center justify-center">
                    <Signal class="w-4 h-4 text-white" />
                </div>
                Nivel de Dificultad
            </label>
            <div class="grid grid-cols-3 gap-2 sm:gap-3">
                <button v-for="nivel in nivelesDificultad" :key="nivel.id" @click="selectedNivelDificultad = nivel.id"
                    class="relative p-2.5 sm:p-3 md:p-4 rounded-xl border-2 transition-all duration-300 text-center"
                    :class="selectedNivelDificultad === nivel.id
                        ? nivel.id === 'basico'
                            ? 'bg-gradient-to-br from-emerald-50 to-green-50 dark:from-emerald-900/30 dark:to-green-900/20 border-emerald-400 dark:border-emerald-600 ring-2 ring-emerald-200 dark:ring-emerald-800'
                            : nivel.id === 'intermedio'
                                ? 'bg-gradient-to-br from-amber-50 to-orange-50 dark:from-amber-900/30 dark:to-orange-900/20 border-amber-400 dark:border-amber-600 ring-2 ring-amber-200 dark:ring-amber-800'
                                : 'bg-gradient-to-br from-red-50 to-rose-50 dark:from-red-900/30 dark:to-rose-900/20 border-red-400 dark:border-red-600 ring-2 ring-red-200 dark:ring-red-800'
                        : 'bg-gray-50 dark:bg-slate-900 border-gray-200 dark:border-slate-700 hover:border-gray-300 dark:hover:border-slate-600'
                        ">
                    <div class="mb-1.5 flex justify-center">
                        <Sprout v-if="nivel.icono === 'Sprout'" class="w-5 h-5 sm:w-7 sm:h-7 transition-all duration-500"
                            :class="selectedNivelDificultad === nivel.id ? 'text-emerald-500 animate-bounce-gentle' : 'text-slate-400'" />
                        <Leaf v-else-if="nivel.icono === 'Leaf'" class="w-5 h-5 sm:w-7 sm:h-7 transition-all duration-500"
                            :class="selectedNivelDificultad === nivel.id ? 'text-amber-500 animate-bounce-gentle' : 'text-slate-400'" />
                        <TreeDeciduous v-else class="w-5 h-5 sm:w-7 sm:h-7 transition-all duration-500"
                            :class="selectedNivelDificultad === nivel.id ? 'text-red-500 animate-bounce-gentle' : 'text-slate-400'" />
                    </div>
                    <span class="font-bold text-xs sm:text-sm block" :class="selectedNivelDificultad === nivel.id
                        ? nivel.id === 'basico'
                            ? 'text-emerald-700 dark:text-emerald-400'
                            : nivel.id === 'intermedio'
                                ? 'text-amber-700 dark:text-amber-400'
                                : 'text-red-700 dark:text-red-400'
                        : 'text-slate-600 dark:text-slate-400'
                        ">
                        {{ nivel.nombre }}
                    </span>
                    <span class="text-[10px] sm:text-[11px] text-slate-500 dark:text-slate-500 mt-0.5 block hidden sm:block">
                        {{ nivel.descripcion }}
                    </span>
                    <div v-if="selectedNivelDificultad === nivel.id"
                        class="absolute top-1.5 right-1.5 sm:top-2 sm:right-2 w-4 h-4 rounded-full flex items-center justify-center" :class="nivel.id === 'basico'
                            ? 'bg-emerald-500'
                            : nivel.id === 'intermedio'
                                ? 'bg-amber-500'
                                : 'bg-red-500'
                            ">
                        <Check class="w-2.5 h-2.5 text-white" />
                    </div>
                </button>
            </div>
        </div>



        <!-- Textual Diversity Selector -->
        <div class="grid md:grid-cols-2 gap-4 mb-6" v-if="tipoTextualOptions && formatoTextualOptions">
            <!-- Tipo Textual -->
            <div
                class="bg-white dark:bg-slate-800 rounded-2xl p-5 border-2 border-indigo-100 dark:border-slate-700 shadow-sm hover:shadow-md hover:border-indigo-200 transition-all duration-300">
                <label class="flex items-center gap-2 text-sm font-bold text-slate-700 dark:text-slate-300 mb-3">
                    <div
                        class="w-8 h-8 bg-gradient-to-br from-indigo-400 to-indigo-600 rounded-lg flex items-center justify-center">
                        <FileText class="w-4 h-4 text-white" />
                    </div>
                    Tipo Textual
                    <span class="text-xs font-normal text-slate-400 ml-auto">(Opcional)</span>
                </label>
                <ComboBox v-model="selectedTipoTextual" :options="tipoTextualOptions"
                    placeholder="Seleccionar tipo..." />
            </div>

            <!-- Formato Textual -->
            <div
                class="bg-white dark:bg-slate-800 rounded-2xl p-5 border-2 border-pink-100 dark:border-slate-700 shadow-sm hover:shadow-md hover:border-pink-200 transition-all duration-300">
                <label class="flex items-center gap-2 text-sm font-bold text-slate-700 dark:text-slate-300 mb-3">
                    <div
                        class="w-8 h-8 bg-gradient-to-br from-pink-400 to-pink-600 rounded-lg flex items-center justify-center">
                        <LayoutGrid class="w-4 h-4 text-white" />
                    </div>
                    Formato Textual
                    <span class="text-xs font-normal text-slate-400 ml-auto">(Opcional)</span>
                </label>
                <ComboBox v-model="selectedFormatoTextual" :options="formatoTextualOptions"
                    placeholder="Seleccionar formato..." />
            </div>
        </div>

        <div class="grid md:grid-cols-3 gap-4 mb-6">
            <!-- Grade Selection -->
            <div
                class="bg-white dark:bg-slate-800 rounded-2xl p-5 border-2 border-teal-100 dark:border-slate-700 shadow-sm hover:shadow-md hover:border-teal-200 transition-all duration-300">
                <label class="flex items-center gap-2 text-sm font-bold text-slate-700 dark:text-slate-300 mb-3">
                    <div
                        class="w-8 h-8 bg-gradient-to-br from-teal-400 to-teal-600 rounded-lg flex items-center justify-center">
                        <GraduationCap class="w-4 h-4 text-white" />
                    </div>
                    Grado Escolar
                </label>
                <div v-if="loadingGrados" class="w-full h-[46px] bg-slate-50 dark:bg-slate-900/50 rounded-xl animate-pulse flex items-center px-4 border-2 border-slate-200/60 dark:border-slate-700/60 transition-all duration-300">
                    <div class="h-4 w-1/3 bg-slate-200 dark:bg-slate-700 rounded"></div>
                    <div class="ml-auto w-4 h-4 bg-slate-200 dark:bg-slate-700 rounded-sm"></div>
                </div>
                <ComboBox v-else v-model="selectedGradoId" :options="gradoOptions" placeholder="Seleccionar grado..." />
            </div>

            <!-- Quantity -->
            <div
                class="bg-white dark:bg-slate-800 rounded-2xl p-5 border-2 border-amber-100 dark:border-slate-700 shadow-sm hover:shadow-md hover:border-amber-200 transition-all duration-300">
                <label class="flex items-center gap-2 text-sm font-bold text-slate-700 dark:text-slate-300 mb-3">
                    <div
                        class="w-8 h-8 bg-gradient-to-br from-amber-400 to-amber-600 rounded-lg flex items-center justify-center">
                        <Hash class="w-4 h-4 text-white" />
                    </div>
                    Cantidad de Preguntas
                </label>
                <div class="flex items-center gap-4 mb-4">
                    <input type="range" v-model.number="quantity" min="3" max="10"
                        class="flex-1 h-3 bg-gradient-to-r from-teal-100 to-amber-100 dark:bg-slate-700 rounded-full appearance-none cursor-pointer accent-teal-600" />
                    <span
                        class="w-12 h-12 rounded-xl bg-gradient-to-br from-teal-500 to-teal-600 flex items-center justify-center text-xl font-bold text-white shadow-lg shadow-teal-500/30">
                        {{ quantity }}
                    </span>
                </div>

                <!-- Breakdown -->
                <div class="space-y-3 pt-3 border-t border-slate-100 dark:border-slate-700">
                    <p class="text-xs font-semibold text-slate-500 dark:text-slate-400 mb-2">Distribución por Nivel:</p>

                    <div class="grid grid-cols-3 gap-2">
                        <!-- Literal -->
                        <div class="flex flex-col gap-1.5">
                            <label
                                class="text-[10px] uppercase font-bold text-teal-600 dark:text-teal-400 text-center tracking-wide">Literal</label>
                            <div
                                class="flex items-center rounded-xl border-2 border-teal-200 dark:border-teal-700 bg-teal-50 dark:bg-teal-900/20 overflow-hidden">
                                <button type="button" @click="qLiteral = Math.max(0, qLiteral - 1)"
                                    :disabled="qLiteral <= 0"
                                    class="flex items-center justify-center w-8 h-9 text-teal-600 dark:text-teal-400 hover:bg-teal-100 dark:hover:bg-teal-800/50 disabled:opacity-30 disabled:cursor-not-allowed transition-colors text-lg font-bold leading-none select-none shrink-0">
                                    −
                                </button>
                                <span
                                    class="flex-1 text-center text-sm font-extrabold text-teal-700 dark:text-teal-300 tabular-nums">{{
                                    qLiteral }}</span>
                                <button type="button" @click="qLiteral = Math.min(quantity, qLiteral + 1)"
                                    :disabled="qLiteral >= quantity"
                                    class="flex items-center justify-center w-8 h-9 text-teal-600 dark:text-teal-400 hover:bg-teal-100 dark:hover:bg-teal-800/50 disabled:opacity-30 disabled:cursor-not-allowed transition-colors text-lg font-bold leading-none select-none shrink-0">
                                    +
                                </button>
                            </div>
                        </div>

                        <!-- Inferencial -->
                        <div class="flex flex-col gap-1.5">
                            <label
                                class="text-[10px] uppercase font-bold text-amber-600 dark:text-amber-400 text-center tracking-wide">Inferencial</label>
                            <div
                                class="flex items-center rounded-xl border-2 border-amber-200 dark:border-amber-700 bg-amber-50 dark:bg-amber-900/20 overflow-hidden">
                                <button type="button" @click="qInferencial = Math.max(0, qInferencial - 1)"
                                    :disabled="qInferencial <= 0"
                                    class="flex items-center justify-center w-8 h-9 text-amber-600 dark:text-amber-400 hover:bg-amber-100 dark:hover:bg-amber-800/50 disabled:opacity-30 disabled:cursor-not-allowed transition-colors text-lg font-bold leading-none select-none shrink-0">
                                    −
                                </button>
                                <span
                                    class="flex-1 text-center text-sm font-extrabold text-amber-700 dark:text-amber-300 tabular-nums">{{
                                    qInferencial }}</span>
                                <button type="button" @click="qInferencial = Math.min(quantity, qInferencial + 1)"
                                    :disabled="qInferencial >= quantity"
                                    class="flex items-center justify-center w-8 h-9 text-amber-600 dark:text-amber-400 hover:bg-amber-100 dark:hover:bg-amber-800/50 disabled:opacity-30 disabled:cursor-not-allowed transition-colors text-lg font-bold leading-none select-none shrink-0">
                                    +
                                </button>
                            </div>
                        </div>

                        <!-- Crítico -->
                        <div class="flex flex-col gap-1.5">
                            <label
                                class="text-[10px] uppercase font-bold text-violet-600 dark:text-violet-400 text-center tracking-wide">Crítico</label>
                            <div
                                class="flex items-center rounded-xl border-2 border-violet-200 dark:border-violet-700 bg-violet-50 dark:bg-violet-900/20 overflow-hidden">
                                <button type="button" @click="qCritico = Math.max(0, qCritico - 1)"
                                    :disabled="qCritico <= 0"
                                    class="flex items-center justify-center w-8 h-9 text-violet-600 dark:text-violet-400 hover:bg-violet-100 dark:hover:bg-violet-800/50 disabled:opacity-30 disabled:cursor-not-allowed transition-colors text-lg font-bold leading-none select-none shrink-0">
                                    −
                                </button>
                                <span
                                    class="flex-1 text-center text-sm font-extrabold text-violet-700 dark:text-violet-300 tabular-nums">{{
                                    qCritico }}</span>
                                <button type="button" @click="qCritico = Math.min(quantity, qCritico + 1)"
                                    :disabled="qCritico >= quantity"
                                    class="flex items-center justify-center w-8 h-9 text-violet-600 dark:text-violet-400 hover:bg-violet-100 dark:hover:bg-violet-800/50 disabled:opacity-30 disabled:cursor-not-allowed transition-colors text-lg font-bold leading-none select-none shrink-0">
                                    +
                                </button>
                            </div>
                        </div>
                    </div>

                    <!-- Validation Message -->
                    <div v-if="!isBreakdownValid"
                        class="flex items-center gap-1.5 text-xs text-red-500 font-medium animate-pulse">
                        <AlertTriangle class="w-3 h-3" />
                        <span>Suma actual: {{ totalBreakdown }} (Debe ser {{ quantity }})</span>
                    </div>
                    <div v-else class="flex items-center gap-1.5 text-xs text-emerald-500 font-medium">
                        <Check class="w-3 h-3" />
                        <span>Distribución correcta: {{ totalBreakdown }} de {{ quantity }}</span>
                    </div>
                </div>
            </div>

            <!-- Textos base — botón compacto que abre el modal -->
            <div class="bg-white dark:bg-slate-800 rounded-2xl p-5 border-2 border-sky-100 dark:border-slate-700 shadow-sm hover:shadow-md hover:border-sky-200 transition-all duration-300">
                <Checkbox v-model="useTextoBase" class="items-center mb-3">
                    <div class="flex items-center gap-2">
                        <div class="w-8 h-8 bg-gradient-to-br from-sky-400 to-sky-600 rounded-lg flex items-center justify-center">
                            <FileUp class="w-4 h-4 text-white" />
                        </div>
                        <span class="text-sm font-bold text-slate-700 dark:text-slate-300">Usar Textos Base</span>
                    </div>
                </Checkbox>

                <template v-if="useTextoBase">
                    <!-- Resumen de textos cargados -->
                    <div class="flex flex-wrap gap-1.5 mb-3">
                        <span v-for="(item, idx) in textosBase" :key="item.id"
                            :class="item.texto
                                ? 'bg-teal-50 dark:bg-teal-900/20 border-teal-200 dark:border-teal-800 text-teal-700 dark:text-teal-400'
                                : 'bg-slate-50 dark:bg-slate-700 border-slate-200 dark:border-slate-600 text-slate-500 dark:text-slate-400'"
                            class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-xs font-medium">
                            <FileText class="w-3 h-3" />
                            {{ item.titulo || `Texto ${idx + 1}` }}
                            <span v-if="item.texto" class="text-[10px] opacity-70">
                                ({{ item.texto.split(' ').length }}p)
                            </span>
                        </span>
                    </div>
                    <button @click="emit('open-textos-modal')"
                        class="w-full flex items-center justify-center gap-2 py-2 rounded-xl border border-sky-300 dark:border-slate-600 bg-sky-50 dark:bg-slate-700/50 text-sky-700 dark:text-sky-400 hover:bg-sky-100 dark:hover:bg-slate-700 text-xs font-semibold transition-all">
                        <LayoutGrid class="w-3.5 h-3.5" /> Gestionar textos
                    </button>
                </template>

                <p v-else class="text-slate-400 dark:text-slate-500 text-xs mt-2 flex items-center gap-1">
                    <BookOpen class="w-3 h-3" /> Activa para usar lecturas personalizadas
                </p>
            </div>
        </div>
    </div>
</template>

<style scoped>
@keyframes bounce-gentle {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-4px);
  }
}

.animate-bounce-gentle {
  animation: bounce-gentle 1.5s ease-in-out infinite;
}
</style>
