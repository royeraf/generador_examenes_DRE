<script setup lang="ts">
import {
    X, Award, Clock, GraduationCap, FileText, Link, Trash2,
    ClipboardCheck, BookOpen, HelpCircle,
    Check, LayoutGrid, Sparkles, Target, Loader2
} from 'lucide-vue-next';
import type { ExamenHistoryEntry } from '../../types';

defineProps<{
    entry: ExamenHistoryEntry | null;
    loadingDelete?: boolean;
    isLoading?: boolean;
}>();

const emit = defineEmits<{
    (e: 'close'): void;
    (e: 'vincular'): void;
    (e: 'eliminar'): void;
}>();

const getCapacidadBadgeClass = (capacidad: string): string => {
    // Determine capacity class based on keyword content or just cycle
    if (capacidad.includes('cantidad')) return 'bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-400';
    if (capacidad.includes('regularidad')) return 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400';
    if (capacidad.includes('forma')) return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400';
    if (capacidad.includes('datos')) return 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400';

    return 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400';
};

function formatFecha(iso: string): string {
    const d = new Date(iso);
    return d.toLocaleDateString('es-PE', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}
</script>

<template>
    <Teleport to="body">
        <Transition name="modal">
            <div v-if="entry || isLoading" class="fixed inset-0 z-50 flex items-center justify-center p-4"
                @click.self="emit('close')">
                <!-- Backdrop -->
                <div class="absolute inset-0 bg-slate-900/60 backdrop-blur-sm" />

                <!-- Modal -->
                <div
                    class="relative w-full max-w-4xl max-h-[90vh] bg-white dark:bg-slate-800 rounded-2xl shadow-2xl border border-gray-200 dark:border-slate-700 flex flex-col overflow-hidden">

                    <!-- Header -->
                    <div class="bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 px-5 py-4 flex-shrink-0">
                        <div class="flex items-center justify-between gap-3">
                            <div class="flex items-center gap-3 min-w-0 flex-1">
                                <div
                                    class="w-11 h-11 bg-white/20 backdrop-blur-sm rounded-xl flex items-center justify-center shadow-lg flex-shrink-0">
                                    <Award class="w-6 h-6 text-white" />
                                </div>
                                <div class="min-w-0 flex-1">
                                    <h2 class="text-lg font-bold text-white truncate">
                                        {{ entry?.resultado.examen.titulo || 'Cargando examen...' }}
                                    </h2>
                                    <div v-if="entry" class="flex items-center gap-3 text-xs text-indigo-100 mt-0.5">
                                        <span class="flex items-center gap-1">
                                            <GraduationCap class="w-3 h-3" />
                                            {{ entry.gradoLabel }}
                                        </span>
                                        <span class="flex items-center gap-1">
                                            <FileText class="w-3 h-3" />
                                            {{ entry.resultado.total_preguntas }} preguntas
                                        </span>
                                        <span class="flex items-center gap-1">
                                            <Clock class="w-3 h-3" />
                                            {{ formatFecha(entry.fechaCreacion) }}
                                        </span>
                                    </div>
                                    <div v-else class="flex gap-4 mt-2">
                                        <div class="h-3 w-20 bg-white/20 rounded animate-pulse"></div>
                                        <div class="h-3 w-20 bg-white/20 rounded animate-pulse"></div>
                                    </div>
                                </div>
                            </div>
                            <button @click="emit('close')"
                                class="w-9 h-9 bg-white/20 hover:bg-white/30 rounded-xl flex items-center justify-center text-white transition-colors flex-shrink-0">
                                <X class="w-5 h-5" />
                            </button>
                        </div>
                    </div>

                    <!-- Scrollable Body -->
                    <div class="flex-1 overflow-y-auto p-5 space-y-6">
                        <template v-if="isLoading">
                            <!-- Skeleton Body -->
                            <div class="space-y-6">
                                <!-- Instructions Skeleton -->
                                <div class="bg-gray-100 dark:bg-slate-700/50 rounded-xl p-4 animate-pulse">
                                    <div class="h-4 w-32 bg-gray-200 dark:bg-slate-600 rounded mb-3"></div>
                                    <div class="h-3 w-full bg-gray-200 dark:bg-slate-600 rounded"></div>
                                </div>
                                <!-- Problem Skeleton -->
                                <div class="bg-gray-100 dark:bg-slate-700/50 rounded-xl p-5 animate-pulse">
                                    <div class="flex items-center gap-2 mb-4">
                                        <div class="w-8 h-8 bg-gray-200 dark:bg-slate-600 rounded"></div>
                                        <div class="h-4 w-28 bg-gray-200 dark:bg-slate-600 rounded"></div>
                                    </div>
                                    <div class="space-y-3">
                                        <div class="h-3 w-full bg-gray-200 dark:bg-slate-600 rounded"></div>
                                        <div class="h-3 w-full bg-gray-200 dark:bg-slate-600 rounded"></div>
                                        <div class="h-3 w-4/5 bg-gray-200 dark:bg-slate-600 rounded"></div>
                                    </div>
                                </div>
                                <!-- Questions Skeleton -->
                                <div class="space-y-4">
                                    <div v-for="i in 2" :key="i"
                                        class="p-5 border-2 border-gray-100 dark:border-slate-700 rounded-xl animate-pulse">
                                        <div class="flex gap-4">
                                            <div
                                                class="w-10 h-10 bg-gray-200 dark:bg-slate-600 rounded-xl flex-shrink-0">
                                            </div>
                                            <div class="flex-1 space-y-3">
                                                <div class="h-3 w-20 bg-gray-200 dark:bg-slate-600 rounded"></div>
                                                <div class="h-4 w-full bg-gray-200 dark:bg-slate-600 rounded"></div>
                                                <div class="grid grid-cols-1 gap-2">
                                                    <div v-for="j in 3" :key="j"
                                                        class="h-10 bg-gray-100 dark:bg-slate-700 rounded-lg"></div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </template>

                        <template v-else-if="entry">
                            <!-- Instrucciones -->
                            <div
                                class="bg-gradient-to-r from-indigo-50 to-purple-50 dark:from-indigo-900/40 dark:to-slate-900 rounded-xl p-4 border-2 border-indigo-100 dark:border-indigo-800">
                                <p class="text-slate-700 dark:text-slate-300 text-sm">
                                    <strong class="text-indigo-700 dark:text-indigo-400 flex items-center gap-2 mb-2">
                                        <ClipboardCheck class="w-4 h-4" />
                                        Instrucciones:
                                    </strong>
                                    {{ entry.resultado.examen.instrucciones }}
                                </p>
                            </div>

                            <!-- Situación Problemática -->
                            <div
                                class="bg-gradient-to-br from-amber-50 to-orange-50 dark:from-slate-900 dark:to-slate-950 rounded-xl p-5 border-2 border-amber-100 dark:border-slate-700">
                                <h4
                                    class="text-sm font-bold text-slate-800 dark:text-white mb-3 flex items-center gap-2">
                                    <div
                                        class="w-8 h-8 bg-gradient-to-br from-amber-400 to-orange-500 rounded-lg flex items-center justify-center">
                                        <BookOpen class="w-4 h-4 text-white" />
                                    </div>
                                    Situación Problemática
                                </h4>
                                <p
                                    class="text-slate-700 dark:text-slate-300 text-sm leading-7 whitespace-pre-line bg-white/50 dark:bg-black/20 p-4 rounded-lg">
                                    {{ entry.resultado.examen.lectura }}
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

                                <div v-for="pregunta in entry.resultado.examen.preguntas" :key="pregunta.numero"
                                    class="bg-white dark:bg-slate-800 rounded-xl p-5 border-2 border-slate-100 dark:border-slate-700 hover:border-indigo-200 dark:hover:border-indigo-700 transition-all duration-300">
                                    <div class="flex items-start gap-4">
                                        <span
                                            class="w-10 h-10 bg-gradient-to-br from-indigo-500 to-violet-500 rounded-xl flex items-center justify-center text-white font-bold text-sm flex-shrink-0 shadow-lg shadow-indigo-500/20">
                                            {{ pregunta.numero }}
                                        </span>
                                        <div class="flex-1">
                                            <span
                                                class="inline-flex items-center gap-1 px-3 py-1 text-[10px] font-bold uppercase rounded-full mb-2"
                                                :class="getCapacidadBadgeClass(pregunta.nivel)">
                                                <Target class="w-3 h-3" />
                                                {{ pregunta.nivel }}
                                            </span>
                                            <p class="text-slate-800 dark:text-slate-200 font-semibold mb-4">
                                                {{ pregunta.enunciado }}
                                            </p>

                                            <div class="space-y-2">
                                                <div v-for="opcion in pregunta.opciones" :key="opcion.letra"
                                                    class="flex items-center gap-3 text-sm py-3 px-4 rounded-xl border-2 transition-all duration-200"
                                                    :class="opcion.es_correcta
                                                        ? 'bg-gradient-to-r from-teal-50 to-emerald-50 dark:from-emerald-900/40 dark:to-slate-900 border-teal-300 dark:border-emerald-800 text-teal-700 dark:text-emerald-400'
                                                        : 'bg-gray-50 dark:bg-slate-900 border-gray-200 dark:border-slate-700 text-slate-600 dark:text-slate-400'">
                                                    <span
                                                        class="w-8 h-8 rounded-lg flex items-center justify-center font-bold text-sm"
                                                        :class="opcion.es_correcta ? 'bg-teal-500 text-white' : 'bg-gray-200 dark:bg-slate-700 text-slate-600 dark:text-slate-400'">
                                                        {{ opcion.letra }}
                                                    </span>
                                                    <span class="flex-1">{{ opcion.texto }}</span>
                                                    <Check v-if="opcion.es_correcta" class="w-5 h-5 text-teal-500" />
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- Tabla de Respuestas -->
                            <div
                                class="bg-white dark:bg-slate-800 rounded-xl p-5 border-2 border-indigo-100 dark:border-slate-700">
                                <h4
                                    class="text-sm font-bold text-slate-800 dark:text-white mb-4 flex items-center gap-2">
                                    <div
                                        class="w-8 h-8 bg-gradient-to-br from-indigo-400 to-blue-500 rounded-lg flex items-center justify-center">
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
                                                    Desempeño</th>
                                                <th
                                                    class="text-left py-3 px-4 text-slate-600 dark:text-slate-400 font-bold text-xs">
                                                    Capacidad</th>
                                                <th
                                                    class="text-center py-3 px-4 text-slate-600 dark:text-slate-400 font-bold text-xs">
                                                    Rpta.</th>
                                            </tr>
                                        </thead>
                                        <tbody class="divide-y divide-gray-100 dark:divide-slate-700">
                                            <tr v-for="fila in entry.resultado.examen.tabla_respuestas"
                                                :key="fila.pregunta"
                                                class="hover:bg-gray-50 dark:hover:bg-slate-800/50 transition-colors">
                                                <td class="py-3 px-4 text-slate-800 dark:text-slate-200 font-bold">
                                                    {{ fila.pregunta }}
                                                </td>
                                                <td class="py-3 px-4 text-slate-600 dark:text-slate-400 text-xs">
                                                    {{ fila.desempeno }}
                                                </td>
                                                <td class="py-3 px-4">
                                                    <span
                                                        class="px-2.5 py-1 text-[10px] font-bold rounded-full inline-flex items-center gap-1"
                                                        :class="getCapacidadBadgeClass(fila.nivel)">
                                                        <Target class="w-3 h-3" />
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
                                class="text-center text-xs text-slate-500 dark:text-slate-400 bg-gradient-to-r from-indigo-50 to-purple-50 dark:from-slate-900 dark:to-slate-800 p-3 rounded-xl flex items-center justify-center gap-2">
                                <Sparkles class="w-4 h-4 text-amber-500" /> Examen de Matemática con IA -
                                <strong>Revisar antes de usar</strong>
                                <GraduationCap class="w-4 h-4 text-indigo-500" />
                            </p>
                        </template>
                    </div>

                    <!-- Footer -->
                    <div
                        class="flex-shrink-0 px-5 py-4 border-t border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-900/50 flex items-center justify-between gap-3">
                        <button @click="emit('eliminar')" :disabled="loadingDelete"
                            class="px-4 py-2.5 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-xl text-sm font-bold flex items-center gap-2 transition-colors disabled:opacity-50">
                            <Loader2 v-if="loadingDelete" class="w-4 h-4 animate-spin" />
                            <Trash2 v-else class="w-4 h-4" />
                            {{ loadingDelete ? 'Eliminando...' : 'Eliminar' }}
                        </button>
                        <div class="flex gap-2">
                            <button @click="emit('close')"
                                class="px-4 py-2.5 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-xl text-sm font-semibold transition-colors">
                                Cerrar
                            </button>
                            <button @click="emit('vincular')"
                                class="px-5 py-2.5 bg-gradient-to-r from-indigo-500 to-purple-500 hover:from-indigo-600 hover:to-purple-600 text-white rounded-xl text-sm font-bold flex items-center gap-2 shadow-lg shadow-indigo-500/30 transition-all hover:-translate-y-0.5">
                                <Link class="w-4 h-4" />
                                Vincular Sistematizador
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </Transition>
    </Teleport>
</template>

<style scoped>
.modal-enter-active,
.modal-leave-active {
    transition: opacity 0.25s ease;
}

.modal-enter-active .relative,
.modal-leave-active .relative {
    transition: transform 0.25s ease;
}

.modal-enter-from,
.modal-leave-to {
    opacity: 0;
}

.modal-enter-from .relative {
    transform: scale(0.95) translateY(10px);
}

.modal-leave-to .relative {
    transform: scale(0.95) translateY(10px);
}
</style>
