<script setup lang="ts">
import { onMounted, watch } from 'vue';
import ComboBox from './ComboBox.vue';
import {
    Settings,
    ClipboardList,
    BarChart3,
    GraduationCap,
    BookOpen,
    Target,
    UserPlus,
    Calculator,
    Trophy,
    Users,
    Plus,
    Key,
    X,
    Trash2
} from 'lucide-vue-next';
import { useSistematizador } from '../composables/useSistematizador';
const {
    selectedGradoId,
    activeTab,
    niveles,
    competencia,
    estudiantes,
    chartContainer,
    gradoOptions,
    desempenoOptions,
    stats,
    loadGrados,
    addPregunta,
    removePregunta,
    onDesempenoSelect,
    addEstudiante,
    removeEstudiante,
    calcularResultados,
    exportarExcel,
    updateChart
} = useSistematizador();

// Lifecycle
onMounted(() => {
    console.log('Sistematizador mounted'); // Small log
    if (chartContainer.value) updateChart(); // Reference it
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

// Watch tab to update chart
watch(activeTab, (newTab) => {
    if (newTab === 'resultados') {
        setTimeout(() => updateChart(), 100);
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
            <div v-show="activeTab === 'config'" class="animate-fadeIn">
                <div class="flex flex-wrap justify-between items-start mb-8 gap-4">
                    <div>
                        <h2 class="text-2xl font-bold text-teal-700 dark:text-teal-400 flex items-center gap-3">
                            <Target class="w-8 h-8" /> Configuración de Desempeños
                        </h2>
                        <p class="text-slate-500 dark:text-slate-400 mt-1">Define la competencia y los desempeños a
                            evaluar
                            por cada nivel de logro</p>
                    </div>
                    <!-- Grade Selector -->
                    <div class="w-full md:w-72">
                        <label
                            class="text-sm font-bold text-slate-600 dark:text-slate-400 mb-2 block flex items-center gap-2">
                            <GraduationCap class="w-4 h-4" /> Grado Escolar
                        </label>
                        <ComboBox v-model="selectedGradoId" :options="gradoOptions"
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
                        <input v-model="competencia" type="text"
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
                                <span
                                    class="px-3 py-1.5 rounded-full text-xs font-bold tracking-wider uppercase shadow-sm"
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
                                            @update:model-value="(val) => onDesempenoSelect(String(key), idx, val)"
                                            :options="desempenoOptions" placeholder="Seleccionar Desempeño..." />
                                    </div>

                                    <!-- Fallback or Full Text Edit -->
                                    <textarea v-model="pregunta.descripcion" placeholder="Descripción del desempeño..."
                                        rows="2"
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

                                        <button @click="removePregunta(String(key), idx)"
                                            class="text-red-400 hover:text-red-600 p-2 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition-all duration-300">
                                            <X class="w-4 h-4" />
                                        </button>
                                    </div>
                                </div>
                            </div>

                            <button @click="addPregunta(String(key))"
                                class="w-full py-4 border-2 border-dashed rounded-xl text-slate-500 hover:text-teal-600 hover:border-teal-400 hover:bg-teal-50 dark:hover:bg-teal-900/10 transition-all duration-300 flex items-center justify-center gap-2 text-sm font-bold"
                                :style="{ borderColor: nivel.color + '50' }">
                                <Plus class="w-5 h-5" />
                                Agregar Pregunta
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Tab 2: Registro - Educativo -->
            <div v-show="activeTab === 'registro'" class="animate-fadeIn">
                <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">
                    <div>
                        <h2
                            class="text-xl sm:text-2xl font-bold text-amber-600 dark:text-amber-400 flex items-center gap-3">
                            <ClipboardList class="w-6 h-6 sm:w-8 sm:h-8" /> Registro
                        </h2>
                        <p class="text-xs sm:text-sm text-slate-500 mt-1">Ingresa datos y respuestas</p>
                    </div>
                    <div class="flex flex-wrap gap-2 sm:gap-3 w-full sm:w-auto">
                        <button @click="addEstudiante"
                            class="flex-1 sm:flex-none px-3 py-2 sm:px-5 sm:py-3 bg-white dark:bg-slate-800 border-2 border-teal-200 dark:border-slate-700 rounded-xl text-teal-700 dark:text-slate-300 hover:bg-teal-50 dark:hover:bg-slate-700 text-xs sm:text-base font-bold flex items-center justify-center gap-2 transition-all duration-300">
                            <UserPlus class="w-4 h-4 sm:w-5 sm:h-5" />
                            <span class="whitespace-nowrap">Estudiante</span>
                        </button>
                        <button @click="calcularResultados"
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
                                <td
                                    class="p-3 border-r border-slate-100 dark:border-slate-700 text-center text-slate-500">
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
                                    <span v-if="est.nivelFinal"
                                        class="px-3 py-1.5 rounded-full text-xs font-bold shadow-sm" :class="{
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
                                    <button @click="removeEstudiante(i)"
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
                                            <p class="text-sm text-slate-500">Haz clic en "Agregar Estudiante" para
                                                comenzar</p>
                                        </div>
                                    </div>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Tab 3: Resultados - Educativo -->
            <div v-show="activeTab === 'resultados'" class="animate-fadeIn">
                <div class="flex justify-between items-center mb-8">
                    <div>
                        <h2 class="text-2xl font-bold text-violet-600 dark:text-violet-400 flex items-center gap-3">
                            <BarChart3 class="w-8 h-8" /> Resultados del Análisis
                        </h2>
                        <p class="text-slate-500 mt-1">Resumen estadístico y gráficos de evaluación</p>
                    </div>
                    <button @click="exportarExcel"
                        class="px-5 py-3 bg-gradient-to-r from-teal-500 to-emerald-500 text-white rounded-xl hover:from-teal-600 hover:to-emerald-600 font-bold shadow-lg shadow-teal-500/30 flex items-center gap-2 transition-all duration-300 hover:-translate-y-0.5">
                        <Download class="w-5 h-5" />
                        Exportar Excel
                    </button>
                </div>

                <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
                    <!-- Stat Cards - Educativo -->
                    <div
                        class="bg-white dark:bg-slate-800 p-5 rounded-2xl border-2 border-teal-100 dark:border-slate-700 shadow-lg relative overflow-hidden group hover:-translate-y-1 transition-all duration-300">
                        <div class="absolute top-0 left-0 w-full h-1.5 bg-gradient-to-r from-teal-500 to-sky-500"></div>
                        <p
                            class="text-xs text-slate-500 font-bold uppercase tracking-wider mb-2 flex items-center gap-1">
                            <Users class="w-4 h-4" /> Total
                        </p>
                        <p class="text-3xl font-bold text-teal-600 dark:text-teal-400">{{ stats.total }}</p>
                    </div>

                    <div v-for="(count, key) in { 'Pre Inicio': stats['pre-inicio'], 'Inicio': stats['inicio'], 'Proceso': stats['proceso'], 'Satisfactorio': stats['satisfactorio'], 'Destacado': stats['destacado'] }"
                        :key="key"
                        class="bg-white dark:bg-slate-800 p-5 rounded-2xl border-2 dark:border-slate-700 shadow-lg relative overflow-hidden hover:-translate-y-1 transition-all duration-300"
                        :class="{
                            'border-red-100 dark:border-red-900/40': key === 'Pre Inicio',
                            'border-orange-100 dark:border-orange-900/40': key === 'Inicio',
                            'border-yellow-100 dark:border-yellow-900/40': key === 'Proceso',
                            'border-green-100 dark:border-green-900/40': key === 'Satisfactorio',
                            'border-violet-100 dark:border-violet-900/40': key === 'Destacado'
                        }">
                        <div class="absolute top-0 left-0 w-full h-1.5" :class="{
                            'bg-gradient-to-r from-red-500 to-red-400': key === 'Pre Inicio',
                            'bg-gradient-to-r from-orange-500 to-amber-400': key === 'Inicio',
                            'bg-gradient-to-r from-yellow-500 to-amber-400': key === 'Proceso',
                            'bg-gradient-to-r from-green-500 to-emerald-400': key === 'Satisfactorio',
                            'bg-gradient-to-r from-violet-500 to-purple-400': key === 'Destacado'
                        }"></div>
                        <p class="text-xs text-slate-500 font-bold uppercase tracking-wider mb-2">{{ key }}</p>
                        <div class="flex items-end justify-between">
                            <p class="text-3xl font-bold" :class="{
                                'text-red-500': key === 'Pre Inicio',
                                'text-orange-500': key === 'Inicio',
                                'text-yellow-500': key === 'Proceso',
                                'text-green-500': key === 'Satisfactorio',
                                'text-violet-500': key === 'Destacado'
                            }">{{ count }}</p>
                            <span class="text-xs font-bold px-2 py-1 rounded-full" :class="{
                                'bg-red-100 text-red-600 dark:bg-red-900/40 dark:text-red-400': key === 'Pre Inicio',
                                'bg-orange-100 text-orange-600 dark:bg-orange-900/40 dark:text-orange-400': key === 'Inicio',
                                'bg-yellow-100 text-yellow-600 dark:bg-yellow-900/40 dark:text-yellow-400': key === 'Proceso',
                                'bg-green-100 text-green-600 dark:bg-green-900/40 dark:text-green-400': key === 'Satisfactorio',
                                'bg-violet-100 text-violet-600 dark:bg-violet-900/40 dark:text-violet-400': key === 'Destacado'
                            }">
                                {{ stats.total > 0 ? Math.round(count / stats.total * 100) : 0 }}%
                            </span>
                        </div>
                    </div>
                </div>

                <div class="grid lg:grid-cols-2 gap-6">
                    <!-- Chart - Educativo -->
                    <div
                        class="bg-white dark:bg-slate-800 p-6 rounded-2xl border-2 border-violet-100 dark:border-slate-700 shadow-lg">
                        <h3 class="font-bold text-violet-700 dark:text-violet-400 mb-6 flex items-center gap-2 text-lg">
                            <BarChart3 class="w-5 h-5" /> Distribución por Niveles
                        </h3>
                        <div class="relative h-64 w-full flex items-center justify-center">
                            <div ref="chartContainer" class="w-full h-full flex items-center justify-center"></div>
                        </div>

                        <!-- Summary Table - Educativo -->
                        <div class="mt-6 border-t-2 border-violet-100 dark:border-slate-700 pt-4">
                            <h4
                                class="text-sm font-bold text-slate-600 dark:text-slate-400 mb-4 flex items-center gap-2">
                                <FileText class="w-4 h-4" /> Resumen de Niveles
                            </h4>
                            <div class="overflow-x-auto rounded-xl border-2 border-slate-100 dark:border-slate-700">
                                <table class="w-full text-sm">
                                    <thead>
                                        <tr
                                            class="bg-gradient-to-r from-slate-50 to-gray-50 dark:from-slate-900 dark:to-slate-950 border-b-2 border-slate-200 dark:border-slate-700">
                                            <th
                                                class="py-3 px-4 text-left font-bold text-slate-700 dark:text-slate-400">
                                                Nivel
                                            </th>
                                            <th
                                                class="py-3 px-4 text-center font-bold text-slate-700 dark:text-slate-400">
                                                Cantidad</th>
                                            <th
                                                class="py-3 px-4 text-center font-bold text-slate-700 dark:text-slate-400">
                                                Porcentaje</th>
                                        </tr>
                                    </thead>
                                    <tbody class="divide-y divide-slate-100 dark:divide-slate-700">
                                        <tr class="hover:bg-red-50/50 dark:hover:bg-red-900/10 transition-colors">
                                            <td class="py-3 px-4 flex items-center gap-3">
                                                <span
                                                    class="w-4 h-4 rounded-full bg-gradient-to-r from-red-500 to-red-400 shadow-sm"></span>
                                                <span class="text-slate-700 dark:text-slate-300 font-medium">Pre
                                                    Inicio</span>
                                            </td>
                                            <td
                                                class="py-3 px-4 text-center font-bold text-slate-800 dark:text-white text-lg">
                                                {{
                                                    stats['pre-inicio'] }}</td>
                                            <td class="py-3 px-4 text-center">
                                                <span
                                                    class="px-3 py-1 rounded-full bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400 text-xs font-bold">
                                                    {{ stats.total > 0 ? Math.round(stats['pre-inicio'] / stats.total *
                                                        100) : 0 }}%
                                                </span>
                                            </td>
                                        </tr>
                                        <tr class="hover:bg-orange-50/50 dark:hover:bg-orange-900/10 transition-colors">
                                            <td class="py-3 px-4 flex items-center gap-3">
                                                <span
                                                    class="w-4 h-4 rounded-full bg-gradient-to-r from-orange-500 to-amber-400 shadow-sm"></span>
                                                <span
                                                    class="text-slate-700 dark:text-slate-300 font-medium">Inicio</span>
                                            </td>
                                            <td
                                                class="py-3 px-4 text-center font-bold text-slate-800 dark:text-white text-lg">
                                                {{
                                                    stats['inicio'] }}</td>
                                            <td class="py-3 px-4 text-center">
                                                <span
                                                    class="px-3 py-1 rounded-full bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400 text-xs font-bold">
                                                    {{ stats.total > 0 ? Math.round(stats['inicio'] / stats.total * 100)
                                                        : 0 }}%
                                                </span>
                                            </td>
                                        </tr>
                                        <tr class="hover:bg-yellow-50/50 dark:hover:bg-yellow-900/10 transition-colors">
                                            <td class="py-3 px-4 flex items-center gap-3">
                                                <span
                                                    class="w-4 h-4 rounded-full bg-gradient-to-r from-yellow-500 to-amber-400 shadow-sm"></span>
                                                <span class="text-slate-700 dark:text-slate-300 font-medium">En
                                                    Proceso</span>
                                            </td>
                                            <td
                                                class="py-3 px-4 text-center font-bold text-slate-800 dark:text-white text-lg">
                                                {{
                                                    stats['proceso'] }}</td>
                                            <td class="py-3 px-4 text-center">
                                                <span
                                                    class="px-3 py-1 rounded-full bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400 text-xs font-bold">
                                                    {{ stats.total > 0 ? Math.round(stats['proceso'] / stats.total *
                                                        100) : 0 }}%
                                                </span>
                                            </td>
                                        </tr>
                                        <tr class="hover:bg-green-50/50 dark:hover:bg-green-900/10 transition-colors">
                                            <td class="py-3 px-4 flex items-center gap-3">
                                                <span
                                                    class="w-4 h-4 rounded-full bg-gradient-to-r from-green-500 to-emerald-400 shadow-sm"></span>
                                                <span
                                                    class="text-slate-700 dark:text-slate-300 font-medium">Satisfactorio</span>
                                            </td>
                                            <td
                                                class="py-3 px-4 text-center font-bold text-slate-800 dark:text-white text-lg">
                                                {{
                                                    stats['satisfactorio'] }}</td>
                                            <td class="py-3 px-4 text-center">
                                                <span
                                                    class="px-3 py-1 rounded-full bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 text-xs font-bold">
                                                    {{ stats.total > 0 ? Math.round(stats['satisfactorio'] / stats.total
                                                        * 100) : 0
                                                    }}%
                                                </span>
                                            </td>
                                        </tr>
                                        <tr class="hover:bg-violet-50/50 dark:hover:bg-violet-900/10 transition-colors">
                                            <td class="py-3 px-4 flex items-center gap-3">
                                                <span
                                                    class="w-4 h-4 rounded-full bg-gradient-to-r from-violet-500 to-purple-400 shadow-sm"></span>
                                                <span class="text-slate-700 dark:text-slate-300 font-medium">Logro
                                                    Destacado</span>
                                            </td>
                                            <td
                                                class="py-3 px-4 text-center font-bold text-slate-800 dark:text-white text-lg">
                                                {{
                                                    stats['destacado'] }}</td>
                                            <td class="py-3 px-4 text-center">
                                                <span
                                                    class="px-3 py-1 rounded-full bg-violet-100 text-violet-700 dark:bg-violet-900/30 dark:text-violet-400 text-xs font-bold">
                                                    {{ stats.total > 0 ? Math.round(stats['destacado'] / stats.total *
                                                        100) : 0 }}%
                                                </span>
                                            </td>
                                        </tr>
                                    </tbody>
                                    <tfoot class="border-t-2 border-slate-300 dark:border-slate-600">
                                        <tr class="bg-slate-50 dark:bg-slate-900">
                                            <td class="py-2 px-3 font-bold text-slate-800 dark:text-white">Total</td>
                                            <td class="py-2 px-3 text-center font-bold text-slate-800 dark:text-white">
                                                {{
                                                    stats.total }}</td>
                                            <td class="py-2 px-3 text-center font-bold text-slate-800 dark:text-white">
                                                100%</td>
                                        </tr>
                                    </tfoot>
                                </table>
                            </div>
                        </div>
                    </div>

                    <!-- Resumen Table -->
                    <div
                        class="bg-white dark:bg-slate-800 p-6 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm flex flex-col">
                        <h3 class="font-bold text-slate-700 dark:text-slate-200 mb-6">Resumen por Estudiante</h3>
                        <div
                            class="overflow-y-auto flex-1 max-h-[300px] border rounded-lg border-slate-100 dark:border-slate-700">
                            <table class="w-full text-sm">
                                <thead class="bg-slate-50 dark:bg-slate-900 sticky top-0">
                                    <tr>
                                        <th class="p-2 text-left font-semibold text-slate-600 dark:text-slate-400">
                                            Estudiante</th>
                                        <th class="p-2 text-center font-semibold text-slate-600 dark:text-slate-400">
                                            Nivel</th>
                                    </tr>
                                </thead>
                                <tbody class="divide-y divide-slate-100 dark:divide-slate-700">
                                    <tr v-for="(est, i) in estudiantes" :key="i">
                                        <td class="p-2 text-slate-700 dark:text-slate-300">{{ est.nombre || 'Sin Nombre'
                                        }}</td>
                                        <td class="p-2 text-center">
                                            <span v-if="est.nivelFinal"
                                                class="px-2 py-0.5 rounded text-[10px] font-bold uppercase" :class="{
                                                    'bg-red-100 text-red-600 dark:bg-red-900/40 dark:text-red-400': est.nivelFinal === 'PRE INICIO',
                                                    'bg-orange-100 text-orange-600 dark:bg-orange-900/40 dark:text-orange-400': est.nivelFinal === 'INICIO',
                                                    'bg-yellow-100 text-yellow-600 dark:bg-yellow-900/40 dark:text-yellow-400': est.nivelFinal === 'EN PROCESO',
                                                    'bg-green-100 text-green-600 dark:bg-green-900/40 dark:text-green-400': est.nivelFinal === 'SATISFACTORIO',
                                                    'bg-indigo-100 text-indigo-600 dark:bg-indigo-900/40 dark:text-indigo-400': est.nivelFinal === 'LOGRO DESTACADO',
                                                }">
                                                {{ est.nivelFinal }}
                                            </span>
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>

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

/* Ensure Chart.js canvas has size */
canvas {
    max-width: 100%;
}
</style>
