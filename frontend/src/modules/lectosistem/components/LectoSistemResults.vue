<script setup lang="ts">
import { ref } from 'vue';
import { Bot, AlertTriangle, Download, Loader2, Sparkles, MessageSquare, X, CheckCircle2, XCircle } from 'lucide-vue-next';
import ThinkingLoader from '../../../shared/components/ThinkingLoader.vue';
import type { Examen, FilaTablaRespuestas } from '../../../shared/types';
import BaseButton from '../../../shared/components/BaseButton.vue';

interface Resultado {
    grado: string;
    desempenos_usados: string;
    saludo: string;
    examen: Examen;
    lecturas?: { titulo: string; texto: string }[];
    total_preguntas: number;
}

const props = defineProps<{
    resultado: Resultado | null;
    loading: boolean;
    showResults: boolean;
    descargandoWord: boolean;
    fillHeight?: boolean;
}>();

const emit = defineEmits<{
    (e: 'descargar-word'): void;
}>();

// ── Modal de retroalimentación ────────────────────────────────────────────────

const modalPregunta = ref<FilaTablaRespuestas | null>(null);

const getTablaRow = (numeroPregunta: number): FilaTablaRespuestas | undefined =>
    props.resultado?.examen.tabla_respuestas.find(t => t.pregunta === numeroPregunta);

const abrirModal = (numeroPregunta: number) => {
    modalPregunta.value = getTablaRow(numeroPregunta) ?? null;
};

const cerrarModal = () => {
    modalPregunta.value = null;
};

const tieneRetroalimentacion = (numeroPregunta: number): boolean => {
    const row = getTablaRow(numeroPregunta);
    return !!(row?.retroalimentacion_correcta || row?.retroalimentacion_incorrecta);
};
</script>

<template>
    <div class="flex flex-col h-full bg-transparent text-slate-700 dark:text-slate-200">

        <!-- Header -->
        <div class="h-14 px-4 border-b border-slate-300 dark:border-slate-700 flex items-center justify-between shrink-0">
            <h2 class="text-sm font-medium text-slate-800 dark:text-white flex items-center gap-2">
                <Sparkles class="w-4 h-4 text-slate-500 dark:text-slate-400" /> Examen Generado
            </h2>
            <div v-if="resultado" class="flex gap-2">
                <button @click="emit('descargar-word')" :disabled="descargandoWord"
                    class="p-1.5 rounded-full hover:bg-slate-200 dark:bg-slate-700/50 text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-white transition-colors"
                    title="Descargar Word">
                    <Loader2 v-if="descargandoWord" class="w-4 h-4 animate-spin" />
                    <Download v-else class="w-4 h-4" />
                </button>
            </div>
        </div>

        <!-- Empty State -->
        <div v-if="!resultado && !loading" class="flex-1 flex flex-col items-center justify-center p-6 text-center">
            <div class="w-12 h-12 bg-slate-50 dark:bg-slate-950 rounded-2xl flex items-center justify-center mb-4 border border-slate-300 dark:border-slate-700">
                <Bot class="w-6 h-6 text-slate-600" />
            </div>
            <h3 class="text-sm font-medium text-slate-800 dark:text-white mb-2">Comienza a generar</h3>
            <p class="text-xs text-slate-500 max-w-xs mb-6">Selecciona los parámetros a la izquierda y presiona Generar Examen.</p>
            <div class="max-w-sm flex items-start gap-2 p-3 rounded-xl bg-amber-500/10 border border-amber-500/20">
                <AlertTriangle class="w-3.5 h-3.5 text-amber-500 shrink-0 mt-0.5" />
                <p class="text-[10px] text-amber-500/80 text-left">El contenido generado puede contener errores. Revisa y valida siempre antes de usar.</p>
            </div>
        </div>

        <!-- Loading State -->
        <div v-if="loading" class="flex-1 flex flex-col items-center justify-center p-6">
            <ThinkingLoader text="Generando..." variant="teal" />
            <p class="text-xs text-slate-500 mt-4">Analizando textos base y estructurando preguntas...</p>
        </div>

        <!-- Content -->
        <div v-if="resultado && !loading && showResults" class="flex-1 overflow-y-auto custom-scrollbar p-6">
            <div class="max-w-2xl mx-auto space-y-8">

                <div class="text-center space-y-2">
                    <h1 class="text-xl font-bold text-slate-800 dark:text-white">{{ resultado.examen.titulo }}</h1>
                    <p class="text-xs text-slate-500 dark:text-slate-400">{{ resultado.examen.grado }} | {{ resultado.total_preguntas }} Preguntas</p>
                </div>

                <div v-if="resultado.lecturas && resultado.lecturas.length" class="space-y-6">
                    <div v-for="(lectura, idx) in resultado.lecturas" :key="idx"
                        class="bg-slate-50 dark:bg-slate-950 rounded-2xl p-5 border border-slate-300 dark:border-slate-700">
                        <h3 class="text-sm font-bold text-slate-800 dark:text-white mb-3">{{ lectura.titulo }}</h3>
                        <p class="text-sm text-slate-600 dark:text-slate-300 leading-relaxed whitespace-pre-wrap font-serif">{{ lectura.texto }}</p>
                    </div>
                </div>

                <div class="space-y-6">
                    <div v-for="(pregunta, pIdx) in resultado.examen.preguntas" :key="pIdx"
                        class="bg-slate-50 dark:bg-slate-950 rounded-2xl p-5 border border-slate-300 dark:border-slate-700 space-y-4">

                        <!-- Encabezado pregunta -->
                        <div class="flex items-start justify-between gap-3">
                            <h4 class="text-sm font-medium text-slate-800 dark:text-white leading-relaxed flex-1">
                                <span class="text-slate-500 font-bold">{{ pIdx + 1 }}.</span> {{ pregunta.enunciado }}
                            </h4>
                            <div class="flex items-center gap-2 shrink-0">
                                <span class="text-[9px] font-bold uppercase px-2 py-1 rounded bg-slate-100 dark:bg-slate-800/50 text-slate-500 dark:text-slate-400">
                                    {{ pregunta.nivel }}
                                </span>
                                <!-- Botón retroalimentación -->
                                <button v-if="tieneRetroalimentacion(pregunta.numero)"
                                    @click="abrirModal(pregunta.numero)"
                                    class="p-1.5 rounded-lg bg-teal-50 dark:bg-teal-900/20 hover:bg-teal-100 dark:hover:bg-teal-900/40 text-teal-600 dark:text-teal-400 transition-colors"
                                    title="Ver retroalimentación">
                                    <MessageSquare class="w-3.5 h-3.5" />
                                </button>
                            </div>
                        </div>

                        <!-- Opciones -->
                        <div class="space-y-2 pl-6">
                            <div v-for="(alt, aIdx) in pregunta.opciones" :key="aIdx" class="flex items-start gap-2 text-sm">
                                <span class="font-bold w-5" :class="alt.es_correcta ? 'text-emerald-500' : 'text-slate-500'">
                                    {{ String.fromCharCode(65 + aIdx) }})
                                </span>
                                <span :class="alt.es_correcta ? 'text-emerald-500' : 'text-slate-600 dark:text-slate-300'">
                                    {{ alt.texto }}
                                </span>
                            </div>
                        </div>

                        <!-- Justificación -->
                        <div v-if="getTablaRow(pregunta.numero)?.justificacion"
                            class="p-3 bg-slate-100 dark:bg-slate-800/50 rounded-xl text-xs text-slate-500 dark:text-slate-400">
                            <strong>Justificación:</strong> {{ getTablaRow(pregunta.numero)?.justificacion }}
                        </div>
                    </div>
                </div>

            </div>
        </div>

        <Teleport to="body">
            <Transition name="modal">
                <div v-if="modalPregunta"
                    class="fixed inset-0 z-[200] flex items-end sm:items-center justify-center sm:p-4 cursor-pointer"
                    @click.self="cerrarModal">

                    <!-- Backdrop -->
                    <div class="absolute inset-0 bg-black/50 backdrop-blur-sm cursor-pointer" @click="cerrarModal" />

                    <!-- Dialog -->
                    <div class="relative z-10 w-full sm:max-w-lg bg-white dark:bg-slate-900 rounded-t-2xl sm:rounded-2xl shadow-2xl border border-slate-300 dark:border-slate-700 overflow-hidden flex flex-col max-h-[92dvh] sm:max-h-[85vh]">
                        
                        <!-- Drag handle (mobile) -->
                        <div class="sm:hidden flex justify-center pt-3 pb-1 shrink-0" @click="cerrarModal">
                            <div class="w-10 h-1 rounded-full bg-slate-200 dark:bg-slate-600"></div>
                        </div>

                        <!-- Header modal -->
                        <div class="flex items-center justify-between px-5 py-4 border-b border-slate-300 dark:border-slate-700">
                            <div class="flex items-center gap-2">
                                <MessageSquare class="w-4 h-4 text-teal-500" />
                                <span class="text-sm font-semibold text-slate-800 dark:text-white">
                                    Retroalimentación — Pregunta {{ modalPregunta.pregunta }}
                                </span>
                            </div>
                            <button @click="cerrarModal"
                                class="p-1 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors">
                                <X class="w-4 h-4" />
                            </button>
                        </div>

                        <!-- Body modal -->
                        <div class="p-5 space-y-4 max-h-[70vh] overflow-y-auto custom-scrollbar">

                            <!-- Si respondió correctamente -->
                            <div v-if="modalPregunta.retroalimentacion_correcta"
                                class="rounded-xl border border-emerald-200 dark:border-emerald-800/50 bg-emerald-50 dark:bg-emerald-900/10 p-4 space-y-2">
                                <div class="flex items-center gap-2">
                                    <CheckCircle2 class="w-4 h-4 text-emerald-500 shrink-0" />
                                    <span class="text-xs font-semibold text-emerald-700 dark:text-emerald-400 uppercase tracking-wide">
                                        Si respondió correctamente
                                    </span>
                                </div>
                                <p class="text-sm text-emerald-800 dark:text-emerald-300 leading-relaxed">
                                    {{ modalPregunta.retroalimentacion_correcta }}
                                </p>
                            </div>

                            <!-- Si respondió incorrectamente -->
                            <div v-if="modalPregunta.retroalimentacion_incorrecta"
                                class="rounded-xl border border-rose-200 dark:border-rose-800/50 bg-rose-50 dark:bg-rose-900/10 p-4 space-y-2">
                                <div class="flex items-center gap-2">
                                    <XCircle class="w-4 h-4 text-rose-500 shrink-0" />
                                    <span class="text-xs font-semibold text-rose-700 dark:text-rose-400 uppercase tracking-wide">
                                        Si respondió incorrectamente
                                    </span>
                                </div>
                                <p class="text-sm text-rose-800 dark:text-rose-300 leading-relaxed">
                                    {{ modalPregunta.retroalimentacion_incorrecta }}
                                </p>
                            </div>

                            <!-- Justificación (si existe) -->
                            <div v-if="modalPregunta.justificacion"
                                class="rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 p-4 space-y-2">
                                <span class="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">
                                    Justificación de la respuesta correcta
                                </span>
                                <p class="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
                                    {{ modalPregunta.justificacion }}
                                </p>
                            </div>
                        </div>

                        <!-- Footer modal -->
                        <div class="px-5 py-3 border-t border-slate-300 dark:border-slate-700 flex justify-end">
                            <BaseButton variant="secondary" size="sm" @click="cerrarModal">
                                Cerrar
                            </BaseButton>
                        </div>
                    </div>
                </div>
            </Transition>
        </Teleport>

    </div>
</template>

<style scoped>
.modal-enter-active,
.modal-leave-active {
    transition: opacity 0.25s ease;
}
.modal-enter-active .relative,
.modal-leave-active .relative {
    transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}
.modal-enter-from,
.modal-leave-to {
    opacity: 0;
}
/* Mobile slides from bottom */
.modal-enter-from .relative,
.modal-leave-to .relative {
    transform: translateY(100%);
}
/* Desktop scales from center */
@media (min-width: 640px) {
    .modal-enter-from .relative,
    .modal-leave-to .relative {
        transform: translateY(0) scale(0.95);
    }
}
</style>
