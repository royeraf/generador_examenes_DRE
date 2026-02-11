<script setup lang="ts">
import { Target, GraduationCap, BookOpen, Key, Plus, X } from 'lucide-vue-next';
import ComboBox from '../ComboBox.vue';
import { computed } from 'vue';
import type { NivelConfig } from '../../types';

// Define Props
interface Props {
    selectedGradoId: number | null;
    competencia: string;
    gradoOptions: { id: number; label: string; group: string }[];
    niveles: Record<string, NivelConfig>;
    desempenoOptions: { id: number; label: string; group: string }[];
}

const props = defineProps<Props>();

// Define Emits for v-models and actions
const emit = defineEmits<{
    (e: 'update:selectedGradoId', value: number | null): void;
    (e: 'update:competencia', value: string): void;
    (e: 'onDesempenoSelect', nivelKey: string, index: number, id: number | null): void;
    (e: 'addPregunta', nivelKey: string): void;
    (e: 'removePregunta', nivelKey: string, index: number): void;
}>();

// Proxy for v-models
const localSelectedGradoId = computed({
    get: () => props.selectedGradoId,
    set: (val) => emit('update:selectedGradoId', val)
});

const localCompetencia = computed({
    get: () => props.competencia,
    set: (val) => emit('update:competencia', val)
});
</script>

<template>
    <div class="animate-fadeIn">
        <div class="flex flex-wrap justify-between items-start mb-8 gap-4">
            <div>
                <h2 class="text-2xl font-bold text-teal-700 dark:text-teal-400 flex items-center gap-3">
                    <Target class="w-8 h-8" /> Configuración de Desempeños
                </h2>
                <p class="text-slate-500 dark:text-slate-400 mt-1">Define la competencia y los desempeños a evaluar por
                    cada nivel de logro</p>
            </div>
            <!-- Grade Selector -->
            <div class="w-full md:w-72">
                <label class="text-sm font-bold text-slate-600 dark:text-slate-400 mb-2 block flex items-center gap-2">
                    <GraduationCap class="w-4 h-4" /> Grado Escolar
                </label>
                <ComboBox v-model="localSelectedGradoId" :options="gradoOptions"
                    placeholder="Seleccionar Grado para cargar desempeños..." />
            </div>
        </div>

        <!-- Competencia Card - Educativo -->
        <div
            class="bg-white dark:bg-slate-800 rounded-2xl border-2 border-teal-100 dark:border-slate-700 shadow-lg mb-8 overflow-hidden">
            <div class="bg-gradient-to-r from-teal-500 to-sky-500 p-4">
                <div class="flex items-center gap-4">
                    <div
                        class="w-14 h-14 rounded-2xl bg-white/20 backdrop-blur-sm flex items-center justify-center shadow-lg">
                        <BookOpen class="w-7 h-7 text-white" />
                    </div>
                    <div>
                        <h3 class="text-lg font-bold text-white">
                            Competencia a Evaluar
                        </h3>
                        <p class="text-sm text-teal-100">Ingrese la competencia del área curricular</p>
                    </div>
                </div>
            </div>
            <div class="p-5">
                <input v-model="localCompetencia" type="text"
                    class="w-full p-4 bg-gradient-to-br from-teal-50 to-sky-50 dark:from-slate-900 dark:to-slate-950 border-2 border-teal-200 dark:border-slate-700 rounded-xl focus:ring-2 focus:ring-teal-500 focus:border-teal-500 outline-none transition-all font-medium text-slate-700 dark:text-slate-300" />
            </div>
        </div>

        <!-- Niveles Container - Educativo -->
        <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            <div v-for="(nivel, key) in niveles" :key="key"
                class="bg-white dark:bg-slate-800 rounded-2xl border-2 transition-all duration-300 hover:shadow-xl overflow-hidden"
                :style="{ borderColor: nivel.color + '40', borderTopWidth: '4px', borderTopColor: nivel.color }">
                <div class="p-6">
                    <div class="flex items-center gap-2 mb-4 flex-wrap">
                        <span class="px-3 py-1.5 rounded-full text-xs font-bold tracking-wider uppercase shadow-sm"
                            :style="{ backgroundColor: nivel.bg, color: nivel.color }">
                            {{ nivel.nombre }}
                        </span>
                        <span class="text-xs text-slate-500 dark:text-slate-400">{{ nivel.descripcion }}</span>
                    </div>

                    <div class="space-y-3 mb-4">
                        <div v-for="(pregunta, idx) in nivel.preguntas" :key="idx"
                            class="group relative bg-gradient-to-br from-slate-50 to-gray-50 dark:from-slate-900 dark:to-slate-950 p-4 rounded-xl border-2 border-slate-100 dark:border-slate-700 hover:border-teal-200 dark:hover:border-teal-700 transition-all duration-300">
                            <span
                                class="absolute -left-2 -top-2 flex items-center justify-center w-7 h-7 rounded-full text-white text-xs font-bold shadow-lg ring-2 ring-white dark:ring-slate-800"
                                :style="{ backgroundColor: nivel.color }">
                                {{ idx + 1 }}
                            </span>

                            <div class="mb-3 pl-3">
                                <!-- Use ComboBox to select Desempeño from DB -->
                                <ComboBox :model-value="pregunta.desempenoId"
                                    @update:model-value="(val) => emit('onDesempenoSelect', String(key), idx, val as number | null)"
                                    :options="desempenoOptions" placeholder="Seleccionar Desempeño..." />
                            </div>

                            <!-- Fallback or Full Text Edit -->
                            <textarea v-model="pregunta.descripcion" placeholder="Descripción del desempeño..." rows="2"
                                class="w-full text-sm p-3 bg-white dark:bg-slate-800 border-2 border-slate-100 dark:border-slate-700 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500 text-slate-700 dark:text-slate-300 resize-none transition-all"></textarea>

                            <div
                                class="flex items-center justify-between mt-3 pt-3 border-t-2 border-slate-100 dark:border-slate-700">
                                <div class="flex items-center gap-2">
                                    <span class="text-xs font-bold text-slate-500 flex items-center gap-1">
                                        <Key class="w-3 h-3" /> Clave:
                                    </span>
                                    <select v-model="pregunta.clave"
                                        class="text-sm bg-white dark:bg-slate-800 border-2 border-slate-200 dark:border-slate-600 rounded-lg px-3 py-1.5 font-bold focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20 transition-all text-slate-700 dark:text-slate-200">
                                        <option value="">-</option>
                                        <option value="A">A</option>
                                        <option value="B">B</option>
                                        <option value="C">C</option>
                                        <option value="D">D</option>
                                    </select>
                                </div>

                                <button @click="emit('removePregunta', String(key), idx)"
                                    class="text-red-400 hover:text-red-600 p-2 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition-all duration-300">
                                    <X class="w-4 h-4" />
                                </button>
                            </div>
                        </div>
                    </div>

                    <button @click="emit('addPregunta', String(key))"
                        class="w-full py-4 border-2 border-dashed rounded-xl text-slate-500 hover:text-teal-600 hover:border-teal-400 hover:bg-teal-50 dark:hover:bg-teal-900/10 transition-all duration-300 flex items-center justify-center gap-2 text-sm font-bold"
                        :style="{ borderColor: nivel.color + '50' }">
                        <Plus class="w-5 h-5" />
                        Agregar Pregunta
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>
