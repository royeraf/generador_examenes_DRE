<script setup lang="ts">
import { ref, computed } from 'vue';
import { Bot, AlertTriangle, Download, Loader2, Sparkles, MessageSquare, X, CheckCircle2, XCircle, BookOpen, Maximize2 } from 'lucide-vue-next';
import ThinkingLoader from '../../../shared/components/ThinkingLoader.vue';
import type { Examen, FilaTablaRespuestas } from '../../../shared/types';
import BaseButton from '../../../shared/components/BaseButton.vue';
import MathText from '../../../shared/components/MathText.vue';

interface Resultado {
    grado: string;
    desempenos_usados: string;
    saludo: string;
    examen: Examen;
    lecturas?: { titulo: string; texto: string }[];
    total_preguntas: number;
    advertencias_calidad?: string[];
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

// ── Lecturas y texto extenso ─────────────────────────────────────────────────

const UMBRAL_TEXTO_EXTENSO = 400;

const listaLecturas = computed<{ titulo: string; texto: string }[]>(() => {
    if (props.resultado?.lecturas && props.resultado.lecturas.length > 0) {
        return props.resultado.lecturas;
    }
    if (props.resultado?.examen.lectura && props.resultado.examen.lectura.trim()) {
        return [{
            titulo: props.resultado.examen.titulo ? `Lectura: ${props.resultado.examen.titulo}` : 'Lectura Principal',
            texto: props.resultado.examen.lectura
        }];
    }
    return [];
});

const esTextoExtenso = (texto: string): boolean => {
    return (texto || '').trim().length > UMBRAL_TEXTO_EXTENSO;
};

const advertencias = computed<string[]>(() => props.resultado?.advertencias_calidad ?? []);

const getTextoResumen = (texto: string): string => {
    if (!texto) return '';
    const limpio = texto.trim();
    if (limpio.length <= UMBRAL_TEXTO_EXTENSO) return limpio;
    const corte = limpio.slice(0, 350);
    const ultimoEspacio = corte.lastIndexOf(' ');
    const base = ultimoEspacio > 220 ? corte.slice(0, ultimoEspacio) : corte;
    return `${base.trim()}...`;
};

const contarPalabras = (texto: string): number => {
    if (!texto) return 0;
    return texto.trim().split(/\s+/).filter(Boolean).length;
};

// ── Modal de lectura completa ─────────────────────────────────────────────────

const modalLectura = ref<{ titulo: string; texto: string } | null>(null);

const abrirModalLectura = (lectura: { titulo: string; texto: string }) => {
    modalLectura.value = lectura;
};

const cerrarModalLectura = () => {
    modalLectura.value = null;
};

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

                <div v-if="advertencias.length"
                    class="rounded-2xl border border-amber-300 dark:border-amber-700/60 bg-amber-50 dark:bg-amber-950/40 p-4 space-y-2">
                    <div class="flex items-center gap-2.5">
                        <div class="w-7 h-7 rounded-lg bg-amber-100 dark:bg-amber-900/40 flex items-center justify-center text-amber-600 dark:text-amber-400 shrink-0">
                            <AlertTriangle class="w-4 h-4" />
                        </div>
                        <p class="text-sm font-bold text-amber-800 dark:text-amber-300">Revisa el examen antes de descargarlo</p>
                    </div>
                    <ul class="space-y-1.5 pl-9">
                        <li v-for="(aviso, idx) in advertencias" :key="idx"
                            class="text-xs text-amber-700 dark:text-amber-300/90 leading-relaxed">
                            {{ aviso }}
                        </li>
                    </ul>
                </div>

                <div v-if="listaLecturas.length" class="space-y-6">
                    <div v-for="(lectura, idx) in listaLecturas" :key="idx"
                        class="bg-slate-50 dark:bg-slate-950 rounded-2xl p-5 border border-slate-300 dark:border-slate-700">
                        <div class="flex items-start justify-between gap-3 mb-3">
                            <div class="flex items-center gap-2 min-w-0">
                                <div class="w-7 h-7 rounded-lg bg-teal-100/80 dark:bg-teal-900/30 flex items-center justify-center text-teal-600 dark:text-teal-400 shrink-0">
                                    <BookOpen class="w-4 h-4" />
                                </div>
                                <MathText as="h3" class="text-sm font-bold text-slate-800 dark:text-white truncate"
                                    :text="lectura.titulo || (listaLecturas.length > 1 ? `Texto ${idx + 1}` : 'Lectura Principal')" />
                            </div>
                            <span v-if="esTextoExtenso(lectura.texto)"
                                class="text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full bg-teal-50 dark:bg-teal-900/30 text-teal-600 dark:text-teal-400 border border-teal-200 dark:border-teal-800/60 shrink-0">
                                {{ contarPalabras(lectura.texto) }} palabras
                            </span>
                        </div>

                        <!-- Si es extenso, mostrar resumen + botón para abrir modal -->
                        <template v-if="esTextoExtenso(lectura.texto)">
                            <div class="relative">
                                <MathText as="p" class="text-sm text-slate-600 dark:text-slate-300 leading-relaxed whitespace-pre-wrap font-serif"
                                    :text="getTextoResumen(lectura.texto)" />
                                <div class="h-6 bg-gradient-to-t from-slate-50 dark:from-slate-950 to-transparent pointer-events-none -mt-4"></div>
                            </div>
                            <div class="mt-3 pt-3 border-t border-slate-200 dark:border-slate-800 flex flex-wrap items-center justify-between gap-2">
                                <p class="text-xs text-slate-500 dark:text-slate-400">
                                    Vista previa del texto base.
                                </p>
                                <button type="button" @click="abrirModalLectura(lectura)"
                                    class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold bg-teal-500/10 dark:bg-teal-500/20 text-teal-600 dark:text-teal-400 hover:bg-teal-500/20 dark:hover:bg-teal-500/30 border border-teal-500/30 transition-colors">
                                    <Maximize2 class="w-3.5 h-3.5" />
                                    <span>Ver texto completo</span>
                                </button>
                            </div>
                        </template>

                        <!-- Si es corto, mostrar el texto completo directamente -->
                        <template v-else>
                            <MathText as="p" class="text-sm text-slate-600 dark:text-slate-300 leading-relaxed whitespace-pre-wrap font-serif" :text="lectura.texto" />
                        </template>
                    </div>
                </div>

                <div class="space-y-6">
                    <div v-for="(pregunta, pIdx) in resultado.examen.preguntas" :key="pIdx"
                        class="bg-slate-50 dark:bg-slate-950 rounded-2xl p-5 border border-slate-300 dark:border-slate-700 space-y-4">

                        <!-- Encabezado pregunta -->
                        <div class="flex items-start justify-between gap-3">
                            <h4 class="text-sm font-medium text-slate-800 dark:text-white leading-relaxed flex-1">
                                <span class="text-slate-500 font-bold">{{ pIdx + 1 }}.</span> <MathText :text="pregunta.enunciado" />
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
                                <MathText as="span" :class="alt.es_correcta ? 'text-emerald-500' : 'text-slate-600 dark:text-slate-300'"
                                    :text="alt.texto" />
                            </div>
                        </div>

                        <!-- Justificación -->
                        <div v-if="getTablaRow(pregunta.numero)?.justificacion"
                            class="p-3 bg-slate-100 dark:bg-slate-800/50 rounded-xl text-xs text-slate-500 dark:text-slate-400">
                            <strong>Justificación:</strong> <MathText :text="getTablaRow(pregunta.numero)?.justificacion" />
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
                                <MathText as="p" class="text-sm text-emerald-800 dark:text-emerald-300 leading-relaxed"
                                    :text="modalPregunta.retroalimentacion_correcta" />
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
                                <MathText as="p" class="text-sm text-rose-800 dark:text-rose-300 leading-relaxed"
                                    :text="modalPregunta.retroalimentacion_incorrecta" />
                            </div>

                            <!-- Justificación (si existe) -->
                            <div v-if="modalPregunta.justificacion"
                                class="rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 p-4 space-y-2">
                                <span class="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">
                                    Justificación de la respuesta correcta
                                </span>
                                <MathText as="p" class="text-sm text-slate-600 dark:text-slate-300 leading-relaxed"
                                    :text="modalPregunta.justificacion" />
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

        <!-- Modal de Lectura Completa -->
        <Teleport to="body">
            <Transition name="modal">
                <div v-if="modalLectura"
                    class="fixed inset-0 z-[200] flex items-end sm:items-center justify-center sm:p-4 cursor-pointer"
                    @click.self="cerrarModalLectura">

                    <!-- Backdrop -->
                    <div class="absolute inset-0 bg-black/50 backdrop-blur-sm cursor-pointer" @click="cerrarModalLectura" />

                    <!-- Dialog -->
                    <div class="relative z-10 w-full sm:max-w-2xl lg:max-w-3xl bg-white dark:bg-slate-900 rounded-t-2xl sm:rounded-2xl shadow-2xl border border-slate-300 dark:border-slate-700 overflow-hidden flex flex-col max-h-[92dvh] sm:max-h-[85vh] cursor-default"
                        @click.stop>

                        <!-- Drag handle (mobile) -->
                        <div class="sm:hidden flex justify-center pt-3 pb-1 shrink-0" @click="cerrarModalLectura">
                            <div class="w-10 h-1 rounded-full bg-slate-200 dark:bg-slate-600"></div>
                        </div>

                        <!-- Header modal -->
                        <div class="flex items-center justify-between px-5 py-4 border-b border-slate-300 dark:border-slate-700 shrink-0">
                            <div class="flex items-center gap-2.5 min-w-0 pr-2">
                                <div class="w-8 h-8 rounded-lg bg-teal-50 dark:bg-teal-900/30 flex items-center justify-center text-teal-600 dark:text-teal-400 shrink-0">
                                    <BookOpen class="w-4 h-4" />
                                </div>
                                <div class="min-w-0">
                                    <h3 class="text-sm sm:text-base font-bold text-slate-800 dark:text-white truncate">
                                        {{ modalLectura.titulo || 'Texto de Lectura Completo' }}
                                    </h3>
                                    <p class="text-[11px] text-slate-500 dark:text-slate-400">
                                        {{ contarPalabras(modalLectura.texto) }} palabras · {{ modalLectura.texto.length }} caracteres
                                    </p>
                                </div>
                            </div>
                            <button @click="cerrarModalLectura"
                                class="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors shrink-0"
                                title="Cerrar">
                                <X class="w-4 h-4" />
                            </button>
                        </div>

                        <!-- Body modal -->
                        <div class="p-5 sm:p-6 overflow-y-auto custom-scrollbar flex-1 bg-slate-50/50 dark:bg-slate-950/50">
                            <div class="bg-white dark:bg-slate-900 p-5 sm:p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
                                <MathText as="div" class="text-sm sm:text-base text-slate-700 dark:text-slate-200 leading-relaxed sm:leading-loose whitespace-pre-wrap font-serif selection:bg-teal-500/20"
                                    :text="modalLectura.texto" />
                            </div>
                        </div>

                        <!-- Footer modal -->
                        <div class="px-5 py-3 border-t border-slate-300 dark:border-slate-700 flex items-center justify-between shrink-0 bg-white dark:bg-slate-900">
                            <span class="text-xs text-slate-400 dark:text-slate-500">
                                Lectura base de la evaluación
                            </span>
                            <BaseButton variant="secondary" size="sm" @click="cerrarModalLectura">
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
