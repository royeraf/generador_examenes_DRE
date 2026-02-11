<script setup lang="ts">
import { shallowRef } from 'vue';
import { ClipboardList, UserPlus, Calculator, Users, Trophy, GraduationCap, Trash2, Download, Upload } from 'lucide-vue-next';
import type { Estudiante, NivelConfig } from '../../types';

// Define Props
interface Props {
    estudiantes: Estudiante[];
    niveles: Record<string, NivelConfig>;
}

const props = defineProps<Props>();

// Define Emits
const emit = defineEmits<{
    (e: 'addEstudiante'): void;
    (e: 'calcularResultados'): void;
    (e: 'removeEstudiante', index: number): void;
    (e: 'descargarPlantilla'): void;
    (e: 'importarExcel', file: File): void;
}>();

const fileInput = shallowRef<HTMLInputElement | null>(null);

function onFileChange(event: Event) {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (file) {
        emit('importarExcel', file);
        input.value = '';
    }
}

const hasPreguntas = () => {
    return Object.values(props.niveles).some(n => n.preguntas.length > 0);
};
</script>

<template>
    <div class="animate-fadeIn">
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">
            <div>
                <h2 class="text-xl sm:text-2xl font-bold text-amber-600 dark:text-amber-400 flex items-center gap-3">
                    <ClipboardList class="w-6 h-6 sm:w-8 sm:h-8" /> Registro
                </h2>
                <p class="text-xs sm:text-sm text-slate-500 mt-1">Ingresa datos y respuestas</p>
            </div>
            <div class="flex flex-wrap gap-2 sm:gap-3 w-full sm:w-auto">
                <button @click="emit('addEstudiante')"
                    class="flex-1 sm:flex-none px-3 py-2 sm:px-5 sm:py-3 bg-white dark:bg-slate-800 border-2 border-teal-200 dark:border-slate-700 rounded-xl text-teal-700 dark:text-slate-300 hover:bg-teal-50 dark:hover:bg-slate-700 text-xs sm:text-base font-bold flex items-center justify-center gap-2 transition-all duration-300">
                    <UserPlus class="w-4 h-4 sm:w-5 sm:h-5" />
                    <span class="whitespace-nowrap">Estudiante</span>
                </button>
                <button v-if="hasPreguntas()" @click="emit('descargarPlantilla')"
                    class="flex-1 sm:flex-none px-3 py-2 sm:px-5 sm:py-3 bg-white dark:bg-slate-800 border-2 border-sky-200 dark:border-slate-700 rounded-xl text-sky-700 dark:text-slate-300 hover:bg-sky-50 dark:hover:bg-slate-700 text-xs sm:text-base font-bold flex items-center justify-center gap-2 transition-all duration-300">
                    <Download class="w-4 h-4 sm:w-5 sm:h-5" />
                    <span class="whitespace-nowrap">Plantilla</span>
                </button>
                <button v-if="hasPreguntas()" @click="fileInput?.click()"
                    class="flex-1 sm:flex-none px-3 py-2 sm:px-5 sm:py-3 bg-white dark:bg-slate-800 border-2 border-violet-200 dark:border-slate-700 rounded-xl text-violet-700 dark:text-slate-300 hover:bg-violet-50 dark:hover:bg-slate-700 text-xs sm:text-base font-bold flex items-center justify-center gap-2 transition-all duration-300">
                    <Upload class="w-4 h-4 sm:w-5 sm:h-5" />
                    <span class="whitespace-nowrap">Importar</span>
                </button>
                <input ref="fileInput" type="file" accept=".xlsx,.xls" class="hidden" @change="onFileChange" />
                <button @click="emit('calcularResultados')"
                    class="flex-1 sm:flex-none px-3 py-2 sm:px-5 sm:py-3 bg-gradient-to-r from-amber-500 to-orange-500 text-white rounded-xl hover:from-amber-600 hover:to-orange-600 text-xs sm:text-base font-bold shadow-lg shadow-amber-500/30 flex items-center justify-center gap-2 transition-all duration-300 hover:-translate-y-0.5">
                    <Calculator class="w-4 h-4 sm:w-5 sm:h-5" />
                    <span class="whitespace-nowrap">Calcular</span>
                </button>
            </div>
        </div>

        <div
            class="overflow-x-auto rounded-2xl border-2 border-amber-100 dark:border-slate-700 shadow-lg bg-white dark:bg-slate-800">
            <table class="w-full text-sm">
                <thead>
                    <tr>
                        <th rowspan="2"
                            class="p-4 bg-gradient-to-br from-amber-50 to-orange-50 dark:from-slate-900 dark:to-slate-950 border-b-2 border-r-2 border-amber-100 dark:border-slate-700 text-left font-bold text-amber-700 dark:text-slate-300 w-12">
                            #</th>
                        <th rowspan="2"
                            class="p-4 bg-gradient-to-br from-amber-50 to-orange-50 dark:from-slate-900 dark:to-slate-950 border-b-2 border-r-2 border-amber-100 dark:border-slate-700 text-left font-bold text-amber-700 dark:text-slate-300 min-w-[200px]">
                            <Users class="w-4 h-4 inline" /> Apellidos y Nombres
                        </th>

                        <template v-for="(nivel, key) in niveles" :key="key">
                            <th v-if="nivel.preguntas.length" :colspan="nivel.preguntas.length"
                                class="p-3 border-b-2 border-r-2 border-slate-200 dark:border-slate-700 text-center font-bold text-xs uppercase tracking-wider"
                                :style="{ backgroundColor: nivel.bg, color: nivel.color }">
                                {{ nivel.nombre }}
                            </th>
                        </template>

                        <th rowspan="2"
                            class="p-4 bg-gradient-to-br from-violet-50 to-purple-50 dark:from-slate-900 dark:to-slate-950 border-b-2 text-center font-bold text-violet-700 dark:text-slate-300 min-w-[140px]">
                            <Trophy class="w-4 h-4 inline" /> Nivel Final
                        </th>
                        <th rowspan="2" class="p-3 bg-slate-50 dark:bg-slate-900 border-b-2 text-center w-12">
                        </th>
                    </tr>
                    <tr>
                        <template v-for="(nivel, key) in niveles" :key="key + '-sub'">
                            <th v-for="(preg, idx) in nivel.preguntas" :key="idx"
                                class="p-2 border-b border-r border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-xs text-center text-slate-500 dark:text-slate-400"
                                :title="preg.descripcion">
                                <div class="flex flex-col items-center">
                                    <span>P{{ idx + 1 }}</span>
                                    <span v-if="preg.clave" class="text-[10px] font-bold px-1 rounded mt-0.5"
                                        :style="{ backgroundColor: nivel.bg, color: nivel.color }">
                                        {{ preg.clave }}
                                    </span>
                                </div>
                            </th>
                        </template>
                    </tr>
                </thead>
                <tbody class="divide-y divide-slate-100 dark:divide-slate-700">
                    <tr v-for="(est, i) in estudiantes" :key="i"
                        class="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                        <td class="p-3 border-r border-slate-100 dark:border-slate-700 text-center text-slate-500">
                            {{ i + 1 }}</td>
                        <td class="p-3 border-r border-slate-100 dark:border-slate-700">
                            <input v-model="est.nombre" type="text" placeholder="Nombre del estudiante"
                                class="w-full bg-transparent outline-none text-slate-700 dark:text-slate-200" />
                        </td>

                        <template v-for="(nivel, key) in niveles" :key="key">
                            <td v-for="(_pregunta, idx) in nivel.preguntas" :key="idx"
                                class="p-1 border-r border-slate-100 dark:border-slate-700 text-center">
                                <select :value="est.respuestas[String(key)]?.[idx] || ''" @change="(e) => {
                                    if (!est.respuestas[String(key)]) est.respuestas[String(key)] = [];
                                    const respArray = est.respuestas[String(key)];
                                    if (respArray) respArray[idx] = (e.target as HTMLSelectElement).value;
                                }"
                                    class="w-full text-center bg-transparent outline-none cursor-pointer focus:bg-indigo-50 dark:focus:bg-indigo-900/20 rounded py-1 text-slate-700 dark:text-slate-300">
                                    <option value="" class="dark:bg-slate-800">-</option>
                                    <option value="A" class="dark:bg-slate-800">A</option>
                                    <option value="B" class="dark:bg-slate-800">B</option>
                                    <option value="C" class="dark:bg-slate-800">C</option>
                                    <option value="D" class="dark:bg-slate-800">D</option>
                                </select>
                            </td>
                        </template>

                        <td class="p-3 text-center">
                            <span v-if="est.nivelFinal" class="px-3 py-1.5 rounded-full text-xs font-bold shadow-sm"
                                :class="{
                                    'bg-red-100 text-red-700 ring-2 ring-red-200 dark:bg-red-900/40 dark:text-red-400 dark:ring-red-900/50': est.nivelFinal === 'PRE INICIO',
                                    'bg-orange-100 text-orange-700 ring-2 ring-orange-200 dark:bg-orange-900/40 dark:text-orange-400 dark:ring-orange-900/50': est.nivelFinal === 'INICIO',
                                    'bg-yellow-100 text-yellow-700 ring-2 ring-yellow-200 dark:bg-yellow-900/40 dark:text-yellow-400 dark:ring-yellow-900/50': est.nivelFinal === 'EN PROCESO',
                                    'bg-green-100 text-green-700 ring-2 ring-green-200 dark:bg-green-900/40 dark:text-green-400 dark:ring-green-900/50': est.nivelFinal === 'SATISFACTORIO',
                                    'bg-violet-100 text-violet-700 ring-2 ring-violet-200 dark:bg-violet-900/40 dark:text-violet-400 dark:ring-violet-900/50': est.nivelFinal === 'LOGRO DESTACADO',
                                }">
                                {{ est.nivelFinal }}
                            </span>
                            <span v-else class="text-slate-400 text-xs">Pendiente</span>
                        </td>

                        <td class="p-3 text-center">
                            <button @click="emit('removeEstudiante', i)"
                                class="text-slate-400 hover:text-red-500 transition-colors">
                                <Trash2 class="w-4 h-4" />
                            </button>
                        </td>
                    </tr>
                    <tr v-if="estudiantes.length === 0">
                        <td :colspan="20" class="p-16 text-center">
                            <div class="flex flex-col items-center gap-4">
                                <div
                                    class="w-20 h-20 bg-gradient-to-br from-amber-100 to-orange-100 dark:from-slate-700 dark:to-slate-800 rounded-2xl flex items-center justify-center shadow-lg">
                                    <GraduationCap class="w-10 h-10 text-amber-600" />
                                </div>
                                <div>
                                    <p class="text-lg font-bold text-slate-700 dark:text-slate-300 mb-1">No hay
                                        estudiantes registrados
                                    </p>
                                    <p class="text-sm text-slate-500">Haz clic en "Agregar Estudiante" para comenzar</p>
                                </div>
                            </div>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</template>
