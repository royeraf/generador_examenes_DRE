<script setup lang="ts">
import { Bot, AlertTriangle, Download, Loader2, Sparkles } from 'lucide-vue-next';
import ThinkingLoader from '../../../shared/components/ThinkingLoader.vue';
import type { Examen } from '../../../shared/types';

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
    // (e: 'vincular-sistematizador'): void;
}>();

const getJustificacion = (numeroPregunta: number): string | undefined => {
    return props.resultado?.examen.tabla_respuestas.find(t => t.pregunta === numeroPregunta)?.justificacion;
};


</script>

<template>
    <div class="flex flex-col h-full bg-transparent text-slate-700 dark:text-slate-200">
        
        <!-- Header -->
        <div class="h-14 px-4 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between shrink-0">
            <h2 class="text-sm font-medium text-slate-800 dark:text-white flex items-center gap-2"><Sparkles class="w-4 h-4 text-slate-500 dark:text-slate-400"/> Examen Generado</h2>
            <div v-if="resultado" class="flex gap-2">
                <button @click="emit('descargar-word')" :disabled="descargandoWord" class="p-1.5 rounded-full hover:bg-slate-200 dark:bg-slate-200 dark:bg-slate-700/50 text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:text-white transition-colors" title="Descargar Word">
                    <Loader2 v-if="descargandoWord" class="w-4 h-4 animate-spin" />
                    <Download v-else class="w-4 h-4" />
                </button>
                <!-- <button @click="emit('vincular-sistematizador')" class="p-1.5 rounded-full hover:bg-slate-200 dark:bg-slate-200 dark:bg-slate-700/50 text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:text-white transition-colors" title="Vincular a Sistematizador">
                    <Link class="w-4 h-4" />
                </button> -->
            </div>
        </div>

        <!-- Empty State -->
        <div v-if="!resultado && !loading" class="flex-1 flex flex-col items-center justify-center p-6 text-center">
            <div class="w-12 h-12 bg-slate-50 dark:bg-slate-950 rounded-2xl flex items-center justify-center mb-4 border border-slate-200 dark:border-slate-700">
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
                    <div v-for="(lectura, idx) in resultado.lecturas" :key="idx" class="bg-slate-50 dark:bg-slate-950 rounded-2xl p-5 border border-slate-200 dark:border-slate-700">
                        <h3 class="text-sm font-bold text-slate-800 dark:text-white mb-3">{{ lectura.titulo }}</h3>
                        <p class="text-sm text-slate-600 dark:text-slate-300 leading-relaxed whitespace-pre-wrap font-serif">{{ lectura.texto }}</p>
                    </div>
                </div>

                <div class="space-y-6">
                    <div v-for="(pregunta, pIdx) in resultado.examen.preguntas" :key="pIdx" class="bg-slate-50 dark:bg-slate-950 rounded-2xl p-5 border border-slate-200 dark:border-slate-700 space-y-4">
                        <div class="flex items-start justify-between gap-4">
                            <h4 class="text-sm font-medium text-slate-800 dark:text-white leading-relaxed"><span class="text-slate-500 font-bold">{{ pIdx + 1 }}.</span> {{ pregunta.enunciado }}</h4>
                            <span class="shrink-0 text-[9px] font-bold uppercase px-2 py-1 rounded bg-slate-100 dark:bg-slate-800/50 text-slate-500 dark:text-slate-400">{{ pregunta.nivel }}</span>
                        </div>
                        <div class="space-y-2 pl-6">
                            <div v-for="(alt, aIdx) in pregunta.opciones" :key="aIdx" class="flex items-start gap-2 text-sm">
                                <span class="font-bold w-5" :class="alt.es_correcta ? 'text-emerald-400' : 'text-slate-500'">{{ String.fromCharCode(65 + aIdx) }})</span>
                                <span :class="alt.es_correcta ? 'text-emerald-400' : 'text-slate-600 dark:text-slate-300'">{{ alt.texto }}</span>
                            </div>
                        </div>
                        <div v-if="getJustificacion(pregunta.numero)" class="mt-4 p-3 bg-slate-100 dark:bg-slate-800/50 rounded-xl text-xs text-slate-500 dark:text-slate-400">
                            <strong>Justificación:</strong> {{ getJustificacion(pregunta.numero) }}
                        </div>
                    </div>
                </div>

            </div>
        </div>

    </div>
</template>
