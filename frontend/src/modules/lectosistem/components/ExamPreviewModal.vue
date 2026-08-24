<script setup lang="ts">
import { ref } from 'vue';
import {
    X, Award, Clock, GraduationCap, FileText, Link, Trash2,
    ClipboardCheck, BookOpen, HelpCircle, FileSearch, Lightbulb,
    Check, LayoutGrid, Sparkles, Download,
    MessageSquare, CheckCircle2, XCircle
} from 'lucide-vue-next';
import type { ExamenHistoryEntry, FilaTablaRespuestas } from '../../../shared/types';
import { formatFechaHora } from '../../../shared/utils/dateUtils';
import BaseButton from '../../../shared/components/BaseButton.vue';
import MathText from '../../../shared/components/MathText.vue';

const props = defineProps<{
    entry: ExamenHistoryEntry | null;
    loadingDelete?: boolean;
    isLoading?: boolean;
    downloadingWord?: boolean;
}>();

const emit = defineEmits<{
    (e: 'close'): void;
    (e: 'vincular'): void;
    (e: 'eliminar'): void;
    (e: 'descargar-word'): void;
}>();

const getNivelBadgeClass = (nivel: string): string => {
    const classes: Record<string, string> = {
        'LITERAL': 'bg-teal-100 text-teal-700 dark:bg-teal-900/30 dark:text-teal-400',
        'INFERENCIAL': 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
        'CRITICO': 'bg-violet-100 text-violet-700 dark:bg-violet-900/30 dark:text-violet-400'
    };
    return classes[nivel] || 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300';
};

// ── Retroalimentación sub-modal ───────────────────────────────────────────────

const modalRetro = ref<FilaTablaRespuestas | null>(null);

const getTablaRow = (numeroPregunta: number): FilaTablaRespuestas | undefined =>
    props.entry?.resultado.examen.tabla_respuestas.find(t => t.pregunta === numeroPregunta);

const abrirRetro = (numeroPregunta: number) => {
    modalRetro.value = getTablaRow(numeroPregunta) ?? null;
};

const cerrarRetro = () => { modalRetro.value = null; };

const tieneRetro = (numeroPregunta: number): boolean => {
    const row = getTablaRow(numeroPregunta);
    return !!(row?.retroalimentacion_correcta || row?.retroalimentacion_incorrecta);
};
</script>

<template>
    <Teleport to="body">
        <Transition name="modal">
            <div v-if="entry || isLoading" class="fixed inset-0 z-[100] flex items-end sm:items-center justify-center p-0 sm:p-4 cursor-pointer"
                @click.self="emit('close')">
                <!-- Backdrop -->
                <div class="absolute inset-0 bg-slate-900/60 backdrop-blur-sm -z-10 cursor-pointer" @click="emit('close')" />

                <!-- Modal -->
                <div
                    class="relative w-full max-w-4xl max-h-[90vh] bg-white dark:bg-slate-800 rounded-t-2xl sm:rounded-2xl shadow-2xl border-0 sm:border border-gray-200 dark:border-slate-700 flex flex-col overflow-hidden modal-content cursor-default" @click.stop>

                    <!-- Drag handle -->
                    <div class="flex justify-center pt-3 pb-1 sm:hidden cursor-pointer flex-shrink-0" @click="emit('close')">
                        <div class="w-12 h-1.5 bg-slate-200 dark:bg-slate-700 rounded-full"></div>
                    </div>

                    <!-- Header -->
                    <div class="bg-gradient-to-r from-amber-400 via-amber-500 to-orange-500 px-5 pb-4 pt-1 sm:pt-4 flex-shrink-0">
                        <div class="flex items-center justify-between gap-3">
                            <div class="flex items-center gap-3 min-w-0 flex-1">
                                <div
                                    class="w-11 h-11 bg-white/20 rounded-xl flex items-center justify-center shadow-lg flex-shrink-0">
                                    <Award class="w-6 h-6 text-white" />
                                </div>
                                <div class="min-w-0 flex-1">
                                    <h2 class="text-lg font-bold text-white truncate">
                                        {{ entry?.resultado.examen.titulo || 'Cargando examen...' }}
                                    </h2>
                                    <div v-if="entry" class="flex items-center gap-3 text-xs text-amber-100 mt-0.5">
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
                                            {{ formatFechaHora(entry.fechaCreacion) }}
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
                                <!-- Text Skeleton -->
                                <div class="bg-gray-100 dark:bg-slate-700/50 rounded-xl p-5 animate-pulse">
                                    <div class="flex items-center gap-2 mb-4">
                                        <div class="w-8 h-8 bg-gray-200 dark:bg-slate-600 rounded"></div>
                                        <div class="h-4 w-24 bg-gray-200 dark:bg-slate-600 rounded"></div>
                                    </div>
                                    <div class="space-y-3">
                                        <div class="h-3 w-full bg-gray-200 dark:bg-slate-600 rounded"></div>
                                        <div class="h-3 w-full bg-gray-200 dark:bg-slate-600 rounded"></div>
                                        <div class="h-3 w-3/4 bg-gray-200 dark:bg-slate-600 rounded"></div>
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
                                class="bg-gradient-to-r from-teal-50 to-sky-50 dark:from-teal-900/40 dark:to-slate-900 rounded-xl p-4 border-2 border-teal-100 dark:border-teal-800">
                                <p class="text-slate-700 dark:text-slate-300 text-sm">
                                    <strong class="text-teal-700 dark:text-teal-400 flex items-center gap-2 mb-2">
                                        <ClipboardCheck class="w-4 h-4" />
                                        Instrucciones:
                                    </strong>
                                    {{ entry.resultado.examen.instrucciones }}
                                </p>
                            </div>

                            <!-- Lectura -->
                            <div
                                class="bg-gradient-to-br from-amber-50 to-orange-50 dark:from-slate-900 dark:to-slate-950 rounded-xl p-5 border-2 border-amber-100 dark:border-slate-700">
                                <h4
                                    class="text-sm font-bold text-slate-800 dark:text-white mb-3 flex items-center gap-2">
                                    <div
                                        class="w-8 h-8 bg-gradient-to-br from-amber-400 to-orange-500 rounded-lg flex items-center justify-center">
                                        <BookOpen class="w-4 h-4 text-white" />
                                    </div>
                                    Lectura
                                </h4>
                                <MathText as="p"
                                    class="text-slate-700 dark:text-slate-300 text-sm leading-7 whitespace-pre-line bg-white/50 dark:bg-black/20 p-4 rounded-lg"
                                    :text="entry.resultado.examen.lectura" />
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
                                    class="bg-white dark:bg-slate-800 rounded-xl p-5 border-2 border-slate-300 dark:border-slate-700 hover:border-teal-200 dark:hover:border-teal-700 transition-all duration-300">
                                    <div class="flex items-start gap-4">
                                        <span
                                            class="w-10 h-10 bg-gradient-to-br from-teal-500 to-sky-500 rounded-xl flex items-center justify-center text-white font-bold text-sm flex-shrink-0 shadow-lg shadow-teal-500/20">
                                            {{ pregunta.numero }}
                                        </span>
                                        <div class="flex-1 min-w-0">
                                            <!-- Nivel + botón retroalimentación -->
                                            <div class="flex items-center gap-2 mb-2 flex-wrap">
                                                <span
                                                    class="inline-flex items-center gap-1 px-3 py-1 text-[10px] font-bold uppercase rounded-full"
                                                    :class="getNivelBadgeClass(pregunta.nivel)">
                                                    <BookOpen v-if="pregunta.nivel === 'LITERAL'" class="w-3 h-3" />
                                                    <FileSearch v-else-if="pregunta.nivel === 'INFERENCIAL'" class="w-3 h-3" />
                                                    <Lightbulb v-else class="w-3 h-3" />
                                                    {{ pregunta.nivel }}
                                                </span>
                                                <button v-if="tieneRetro(pregunta.numero)"
                                                    @click="abrirRetro(pregunta.numero)"
                                                    class="inline-flex items-center gap-1.5 px-2.5 py-1 text-[10px] font-semibold rounded-full bg-teal-50 dark:bg-teal-900/20 hover:bg-teal-100 dark:hover:bg-teal-900/40 text-teal-600 dark:text-teal-400 border border-teal-200 dark:border-teal-800 transition-colors">
                                                    <MessageSquare class="w-3 h-3" />
                                                    Retroalimentación
                                                </button>
                                            </div>

                                            <MathText as="p" class="text-slate-800 dark:text-slate-200 font-semibold mb-4"
                                                :text="pregunta.enunciado" />

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
                                                    <MathText as="span" class="flex-1" :text="opcion.texto" />
                                                    <Check v-if="opcion.es_correcta" class="w-5 h-5 text-teal-500" />
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- Tabla de Respuestas -->
                            <div
                                class="bg-white dark:bg-slate-800 rounded-xl p-5 border-2 border-sky-100 dark:border-slate-700">
                                <h4
                                    class="text-sm font-bold text-slate-800 dark:text-white mb-4 flex items-center gap-2">
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
                                                    Desempeño</th>
                                                <th
                                                    class="text-left py-3 px-4 text-slate-600 dark:text-slate-400 font-bold text-xs">
                                                    Nivel</th>
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
                                                    <MathText :text="fila.desempeno" />
                                                </td>
                                                <td class="py-3 px-4">
                                                    <span
                                                        class="px-2.5 py-1 text-[10px] font-bold rounded-full inline-flex items-center gap-1"
                                                        :class="getNivelBadgeClass(fila.nivel)">
                                                        <BookOpen v-if="fila.nivel === 'LITERAL'" class="w-3 h-3" />
                                                        <FileSearch v-else-if="fila.nivel === 'INFERENCIAL'"
                                                            class="w-3 h-3" />
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
                                <Sparkles class="w-4 h-4 text-amber-500" /> Examen generado con IA -
                                <strong>Revisar antes de usar con los estudiantes</strong>
                                <GraduationCap class="w-4 h-4 text-teal-500" />
                            </p>
                        </template>
                    </div>

                    <!-- Footer -->
                    <div
                        class="flex-shrink-0 px-5 py-4 border-t border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-900/50 flex items-center justify-between gap-3">
                        <BaseButton variant="destructive" size="sm" :loading="loadingDelete" @click="emit('eliminar')">
                            <template #icon><Trash2 class="w-3.5 h-3.5" /></template>
                            {{ loadingDelete ? 'Eliminando...' : 'Eliminar' }}
                        </BaseButton>
                        <div class="flex gap-2">
                            <BaseButton variant="secondary" size="sm" :disabled="isLoading" :loading="downloadingWord" @click="emit('descargar-word')">
                                <template #icon><Download class="w-3.5 h-3.5" /></template>
                                {{ downloadingWord ? 'Descargando...' : 'Word' }}
                            </BaseButton>
                            <BaseButton variant="secondary" size="sm" @click="emit('close')">
                                Cerrar
                            </BaseButton>
                            <BaseButton variant="primary" size="sm" @click="emit('vincular')">
                                <template #icon><Link class="w-3.5 h-3.5" /></template>
                                Vincular Sistematizador
                            </BaseButton>
                        </div>
                    </div>
                </div>
            </div>
        </Transition>
    </Teleport>

    <!-- ── Sub-modal de Retroalimentación (z-60, sobre el modal principal z-50) ── -->
    <Teleport to="body">
        <Transition name="retro">
            <div v-if="modalRetro"
                class="fixed inset-0 z-[110] flex items-center justify-center p-4 cursor-pointer"
                @click.self="cerrarRetro">

                <div class="absolute inset-0 bg-black/40 backdrop-blur-sm cursor-pointer" @click="cerrarRetro" />

                <div class="relative z-10 w-full max-w-lg bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-300 dark:border-slate-700 overflow-hidden cursor-default" @click.stop>

                    <!-- Header -->
                    <div class="flex items-center justify-between px-5 py-4 border-b border-slate-300 dark:border-slate-700">
                        <div class="flex items-center gap-2">
                            <MessageSquare class="w-4 h-4 text-teal-500" />
                            <span class="text-sm font-semibold text-slate-800 dark:text-white">
                                Retroalimentación — Pregunta {{ modalRetro.pregunta }}
                            </span>
                        </div>
                        <button @click="cerrarRetro"
                            class="p-1 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors">
                            <X class="w-4 h-4" />
                        </button>
                    </div>

                    <!-- Body -->
                    <div class="p-5 space-y-4 max-h-[65vh] overflow-y-auto">

                        <div v-if="modalRetro.retroalimentacion_correcta"
                            class="rounded-xl border border-emerald-200 dark:border-emerald-800/50 bg-emerald-50 dark:bg-emerald-900/10 p-4 space-y-2">
                            <div class="flex items-center gap-2">
                                <CheckCircle2 class="w-4 h-4 text-emerald-500 shrink-0" />
                                <span class="text-xs font-semibold text-emerald-700 dark:text-emerald-400 uppercase tracking-wide">
                                    Si respondió correctamente
                                </span>
                            </div>
                            <MathText as="p" class="text-sm text-emerald-800 dark:text-emerald-300 leading-relaxed"
                                :text="modalRetro.retroalimentacion_correcta" />
                        </div>

                        <div v-if="modalRetro.retroalimentacion_incorrecta"
                            class="rounded-xl border border-rose-200 dark:border-rose-800/50 bg-rose-50 dark:bg-rose-900/10 p-4 space-y-2">
                            <div class="flex items-center gap-2">
                                <XCircle class="w-4 h-4 text-rose-500 shrink-0" />
                                <span class="text-xs font-semibold text-rose-700 dark:text-rose-400 uppercase tracking-wide">
                                    Si respondió incorrectamente
                                </span>
                            </div>
                            <MathText as="p" class="text-sm text-rose-800 dark:text-rose-300 leading-relaxed"
                                :text="modalRetro.retroalimentacion_incorrecta" />
                        </div>

                        <div v-if="modalRetro.justificacion"
                            class="rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 p-4 space-y-2">
                            <span class="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">
                                Justificación de la respuesta correcta
                            </span>
                            <MathText as="p" class="text-sm text-slate-600 dark:text-slate-300 leading-relaxed"
                                :text="modalRetro.justificacion" />
                        </div>
                    </div>

                    <!-- Footer -->
                    <div class="px-5 py-3 border-t border-slate-300 dark:border-slate-700 flex justify-end">
                        <BaseButton variant="secondary" size="sm" @click="cerrarRetro">
                            Cerrar
                        </BaseButton>
                    </div>
                </div>
            </div>
        </Transition>
    </Teleport>
</template>

<style scoped>
.modal-enter-active,
.modal-leave-active {
    transition: opacity 0.3s ease;
}

.modal-enter-active .modal-content,
.modal-leave-active .modal-content {
    transition: transform 0.3s cubic-bezier(0.34, 1.4, 0.64, 1);
}

.modal-enter-from,
.modal-leave-to {
    opacity: 0;
}

/* Mobile: slide from bottom */
@media (max-width: 639px) {
    .modal-enter-from .modal-content,
    .modal-leave-to .modal-content {
        transform: translateY(100%);
    }
}

/* Desktop: scale */
@media (min-width: 640px) {
    .modal-enter-from .modal-content,
    .modal-leave-to .modal-content {
        transform: scale(0.95);
    }
}

/* Sub-modal retroalimentación */
.retro-enter-active,
.retro-leave-active {
    transition: opacity 0.15s ease;
}
.retro-enter-active .relative,
.retro-leave-active .relative {
    transition: transform 0.15s ease, opacity 0.15s ease;
}
.retro-enter-from,
.retro-leave-to {
    opacity: 0;
}
.retro-enter-from .relative {
    transform: scale(0.96) translateY(6px);
    opacity: 0;
}
</style>
