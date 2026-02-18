<script setup lang="ts">
import { Zap, AlertTriangle, Award, Download, Loader2, ClipboardCheck, BookOpen, HelpCircle, FileSearch, Lightbulb, Check, LayoutGrid, Sparkles, GraduationCap, Link } from 'lucide-vue-next';
import ThinkingLoader from '../ThinkingLoader.vue';
import type { Examen } from '../../types';

interface Resultado {
    grado: string;
    desempenos_usados: string;
    saludo: string;
    examen: Examen;
    total_preguntas: number;
}

const props = defineProps<{
    resultado: Resultado | null;
    loading: boolean;
    showResults: boolean;
    descargandoWord: boolean;
}>();

const emit = defineEmits<{
    (e: 'descargar-word'): void;
    (e: 'vincular-sistematizador'): void;
}>();

const getNivelBadgeClass = (nivel: string): string => {
    const classes: Record<string, string> = {
        'LITERAL': 'bg-teal-100 text-teal-700 dark:bg-teal-900/30 dark:text-teal-400',
        'INFERENCIAL': 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
        'CRITICO': 'bg-violet-100 text-violet-700 dark:bg-violet-900/30 dark:text-violet-400'
    };
    return classes[nivel] || 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300';
};
</script>

<template>
    <div class="flex flex-col order-2 lg:order-2">

        <!-- Empty State -->
        <div v-if="!resultado && !loading"
            class="h-[300px] sm:h-[580px] lg:h-[650px] bg-white dark:bg-slate-800 rounded-xl border border-gray-200 dark:border-slate-700 text-center flex flex-col items-center justify-center shadow-sm p-6">
            <Zap class="w-10 h-10 sm:w-12 sm:h-12 text-gray-300 dark:text-slate-600 mb-4" />
            <h3 class="text-base sm:text-lg font-semibold text-slate-800 dark:text-white mb-2">Listo para generar</h3>
            <p class="text-slate-500 dark:text-slate-400 text-xs sm:text-sm max-w-xs mb-4">
                Selecciona los desempeños y genera tu examen con IA.
            </p>
            <!-- Advertencia de riesgos de IA -->
            <div
                class="max-w-sm mx-auto flex items-start gap-2 p-3 rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700/50">
                <AlertTriangle class="w-4 h-4 text-amber-500 dark:text-amber-400 flex-shrink-0 mt-0.5" />
                <p class="text-[11px] sm:text-xs text-amber-700 dark:text-amber-300/90 text-left leading-relaxed">
                    <strong>Riesgos del uso de IA:</strong> El contenido generado puede contener errores, imprecisiones
                    o
                    información incompleta. Revisa y valida siempre antes de usar con estudiantes.
                </p>
            </div>
        </div>

        <!-- Loading State -->
        <div v-if="loading"
            class="h-[400px] sm:h-[580px] lg:h-[650px] bg-gradient-to-br from-white via-slate-50 to-emerald-50/30 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900 rounded-xl border border-slate-200 dark:border-slate-700/50 text-center flex flex-col items-center justify-center shadow-lg p-6 relative overflow-hidden">
            <div class="absolute inset-0 opacity-20">
                <div class="absolute top-1/4 left-1/4 w-32 h-32 bg-teal-500/30 rounded-full blur-3xl animate-pulse">
                </div>
                <div class="absolute bottom-1/3 right-1/4 w-40 h-40 bg-indigo-500/20 rounded-full blur-3xl animate-pulse"
                    style="animation-delay: 1s;"></div>
            </div>
            <div class="relative z-10 flex flex-col items-center">
                <ThinkingLoader text="Generando examen" variant="teal" />
                <p class="text-slate-500 dark:text-slate-400 text-xs sm:text-sm mt-4">Esto puede tomar unos segundos...
                </p>
                <div
                    class="mt-6 max-w-sm mx-auto flex items-start gap-2 p-3 rounded-lg bg-amber-50 dark:bg-amber-500/10 border border-amber-200 dark:border-amber-500/20">
                    <AlertTriangle class="w-4 h-4 text-amber-500 dark:text-amber-400 flex-shrink-0 mt-0.5" />
                    <p class="text-[11px] sm:text-xs text-amber-700 dark:text-amber-300/90 text-left leading-relaxed">
                        El contenido generado por IA puede contener errores. Revisa y valida siempre el examen antes de
                        utilizarlo.
                    </p>
                </div>
            </div>
        </div>

        <!-- Results -->
        <div v-if="resultado && !loading && showResults"
            class="h-[500px] sm:h-[580px] lg:h-[650px] bg-white dark:bg-slate-800 rounded-2xl border-2 border-amber-200 dark:border-slate-700 shadow-xl flex flex-col overflow-hidden">

            <!-- Results Header -->
            <div
                class="bg-gradient-to-r from-amber-400 via-amber-500 to-orange-500 px-4 sm:px-5 py-3 sm:py-4 flex-shrink-0">
                <div class="flex items-center gap-3 mb-3">
                    <div
                        class="w-10 h-10 bg-white/20 backdrop-blur-sm rounded-xl flex items-center justify-center shadow-lg flex-shrink-0">
                        <Award class="w-5 h-5 text-white" />
                    </div>
                    <div class="min-w-0 flex-1">
                        <h2 class="text-sm sm:text-lg font-bold text-white truncate">
                            {{ resultado.examen.titulo }}
                        </h2>
                        <span class="text-[10px] sm:text-xs text-amber-100 font-medium block">
                            {{ resultado.total_preguntas }} preguntas · {{ resultado.examen.grado }}
                        </span>
                    </div>
                </div>
                <div class="flex gap-2">
                    <button @click="emit('vincular-sistematizador')"
                        class="flex-1 px-3 py-2 bg-white/90 text-orange-600 hover:bg-orange-50 text-xs font-bold rounded-xl transition-all duration-300 flex items-center justify-center gap-1.5 shadow-lg">
                        <Link class="w-3.5 h-3.5 flex-shrink-0" />
                        <span class="truncate">Vincular</span>
                    </button>
                    <button @click="emit('descargar-word')" :disabled="descargandoWord"
                        class="flex-1 px-3 py-2 bg-white text-amber-600 hover:bg-amber-50 text-xs font-bold rounded-xl transition-all duration-300 flex items-center justify-center gap-1.5 shadow-lg">
                        <Loader2 v-if="descargandoWord" class="w-3.5 h-3.5 animate-spin flex-shrink-0" />
                        <Download v-else class="w-3.5 h-3.5 flex-shrink-0" />
                        <span class="truncate">{{ descargandoWord ? 'Generando...' : 'Descargar Word' }}</span>
                    </button>
                </div>
            </div>

            <!-- Scrollable Content -->
            <div class="flex-1 overflow-y-auto p-4 space-y-4">

                <!-- Instrucciones -->
                <div
                    class="bg-gradient-to-r from-teal-50 to-sky-50 dark:from-teal-900/40 dark:to-slate-900 rounded-xl p-4 border-2 border-teal-100 dark:border-teal-800">
                    <p class="text-slate-700 dark:text-slate-300 text-sm">
                        <strong class="text-teal-700 dark:text-teal-400 flex items-center gap-2 mb-2">
                            <ClipboardCheck class="w-4 h-4" />
                            Instrucciones:
                        </strong>
                        {{ resultado.examen.instrucciones }}
                    </p>
                </div>

                <!-- Lectura -->
                <div
                    class="bg-gradient-to-br from-amber-50 to-orange-50 dark:from-slate-900 dark:to-slate-950 rounded-xl p-5 border-2 border-amber-100 dark:border-slate-700">
                    <h4 class="text-sm font-bold text-slate-800 dark:text-white mb-3 flex items-center gap-2">
                        <div
                            class="w-8 h-8 bg-gradient-to-br from-amber-400 to-orange-500 rounded-lg flex items-center justify-center">
                            <BookOpen class="w-4 h-4 text-white" />
                        </div>
                        Lectura
                    </h4>
                    <p
                        class="text-slate-700 dark:text-slate-300 text-sm leading-7 whitespace-pre-line bg-white/50 dark:bg-black/20 p-4 rounded-lg">
                        {{ resultado.examen.lectura }}
                    </p>
                </div>

                <!-- Preguntas -->
                <div class="space-y-4">
                    <h4 class="text-sm font-bold text-slate-800 dark:text-white flex items-center gap-2">
                        <div
                            class="w-8 h-8 bg-gradient-to-br from-violet-400 to-purple-500 rounded-lg flex items-center justify-center">
                            <HelpCircle class="w-4 h-4 text-white" />
                        </div>
                        Preguntas del Examen
                    </h4>

                    <div v-for="pregunta in resultado.examen.preguntas" :key="pregunta.numero"
                        class="bg-white dark:bg-slate-800 rounded-xl p-5 border-2 border-slate-100 dark:border-slate-700 hover:border-teal-200 dark:hover:border-teal-700 transition-all duration-300">
                        <div class="flex items-start gap-4">
                            <span
                                class="w-10 h-10 bg-gradient-to-br from-teal-500 to-sky-500 rounded-xl flex items-center justify-center text-white font-bold text-sm flex-shrink-0 shadow-lg shadow-teal-500/20">
                                {{ pregunta.numero }}
                            </span>
                            <div class="flex-1">
                                <span
                                    class="inline-flex items-center gap-1 px-3 py-1 text-[10px] font-bold uppercase rounded-full mb-2"
                                    :class="getNivelBadgeClass(pregunta.nivel)">
                                    <BookOpen v-if="pregunta.nivel === 'LITERAL'" class="w-3 h-3" />
                                    <FileSearch v-else-if="pregunta.nivel === 'INFERENCIAL'" class="w-3 h-3" />
                                    <Lightbulb v-else class="w-3 h-3" />
                                    {{ pregunta.nivel }}
                                </span>
                                <p class="text-slate-800 dark:text-slate-200 font-semibold mb-4">{{ pregunta.enunciado
                                    }}</p>

                                <div class="space-y-2">
                                    <div v-for="opcion in pregunta.opciones" :key="opcion.letra"
                                        class="flex items-center gap-3 text-sm py-3 px-4 rounded-xl border-2 transition-all duration-200"
                                        :class="opcion.es_correcta
                                            ? 'bg-gradient-to-r from-teal-50 to-emerald-50 dark:from-emerald-900/40 dark:to-slate-900 border-teal-300 dark:border-emerald-800 text-teal-700 dark:text-emerald-400'
                                            : 'bg-gray-50 dark:bg-slate-900 border-gray-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:border-gray-300'">
                                        <span
                                            class="w-8 h-8 rounded-lg flex items-center justify-center font-bold text-sm"
                                            :class="opcion.es_correcta ? 'bg-teal-500 text-white' : 'bg-gray-200 dark:bg-slate-700 text-slate-600 dark:text-slate-400'">{{
                                                opcion.letra }}</span>
                                        <span class="flex-1">{{ opcion.texto }}</span>
                                        <Check v-if="opcion.es_correcta" class="w-5 h-5 text-teal-500" />
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Answer Table -->
                <div class="bg-white dark:bg-slate-800 rounded-xl p-5 border-2 border-sky-100 dark:border-slate-700">
                    <h4 class="text-sm font-bold text-slate-800 dark:text-white mb-4 flex items-center gap-2">
                        <div
                            class="w-8 h-8 bg-gradient-to-br from-sky-400 to-blue-500 rounded-lg flex items-center justify-center">
                            <LayoutGrid class="w-4 h-4 text-white" />
                        </div>
                        Tabla de Respuestas
                    </h4>
                    <div class="overflow-x-auto rounded-xl border-2 border-gray-100 dark:border-slate-700">
                        <table class="w-full text-sm">
                            <thead>
                                <tr
                                    class="bg-gradient-to-r from-slate-50 to-gray-50 dark:from-slate-900 dark:to-slate-950 border-b-2 border-gray-200 dark:border-slate-700">
                                    <th
                                        class="text-left py-3 px-4 text-slate-600 dark:text-slate-400 font-bold text-xs">
                                        #</th>
                                    <th
                                        class="text-left py-3 px-4 text-slate-600 dark:text-slate-400 font-bold text-xs">
                                        Desempeño
                                    </th>
                                    <th
                                        class="text-left py-3 px-4 text-slate-600 dark:text-slate-400 font-bold text-xs">
                                        Nivel
                                    </th>
                                    <th
                                        class="text-center py-3 px-4 text-slate-600 dark:text-slate-400 font-bold text-xs">
                                        Rpta.
                                    </th>
                                </tr>
                            </thead>
                            <tbody class="divide-y divide-gray-100 dark:divide-slate-700">
                                <tr v-for="fila in resultado.examen.tabla_respuestas" :key="fila.pregunta"
                                    class="hover:bg-gray-50 dark:hover:bg-slate-800/50 transition-colors">
                                    <td class="py-3 px-4 text-slate-800 dark:text-slate-200 font-bold">{{ fila.pregunta
                                        }}
                                    </td>
                                    <td class="py-3 px-4 text-slate-600 dark:text-slate-400 text-xs">{{ fila.desempeno
                                        }}</td>
                                    <td class="py-3 px-4">
                                        <span
                                            class="px-2.5 py-1 text-[10px] font-bold rounded-full inline-flex items-center gap-1"
                                            :class="getNivelBadgeClass(fila.nivel)">
                                            <BookOpen v-if="fila.nivel === 'LITERAL'" class="w-3 h-3" />
                                            <FileSearch v-else-if="fila.nivel === 'INFERENCIAL'" class="w-3 h-3" />
                                            <Lightbulb v-else class="w-3 h-3" />
                                            {{ fila.nivel }}
                                        </span>
                                    </td>
                                    <td class="py-3 px-4 text-center">
                                        <span
                                            class="w-8 h-8 bg-gradient-to-br from-teal-400 to-teal-600 text-white rounded-lg inline-flex items-center justify-center font-bold text-sm shadow-lg shadow-teal-500/20">
                                            {{ fila.respuesta_correcta }}
                                        </span>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>

                <p
                    class="text-center text-xs text-slate-500 dark:text-slate-400 bg-gradient-to-r from-teal-50 to-amber-50 dark:from-slate-900 dark:to-slate-800 p-3 rounded-xl flex items-center justify-center gap-2">
                    <Sparkles class="w-4 h-4 text-amber-500" /> Examen generado con IA - <strong>Revisar antes de usar
                        con los estudiantes</strong>
                    <GraduationCap class="w-4 h-4 text-teal-500" />
                </p>
            </div>
        </div>
    </div>
</template>
