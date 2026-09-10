<script setup lang="ts">
import { Table, X } from 'lucide-vue-next';
import type { Examen, FilaTablaRespuestas } from '../../../shared/types';
import MathText from '../../../shared/components/MathText.vue';

export interface TablaModalResultado {
  examen: Examen;
  total_preguntas: number;
}

defineProps<{
  open: boolean;
  resultado: TablaModalResultado | null;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
}>();

const getCapacidadBadgeClass = (capacidad?: string): string => {
  if (!capacidad) return 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300';
  const cap = capacidad.toLowerCase();
  if (cap.includes('cantidad'))    return 'bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-400';
  if (cap.includes('regularidad')) return 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400';
  if (cap.includes('forma'))       return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400';
  if (cap.includes('datos'))       return 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400';
  return 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400';
};

const capacidadDe = (fila: FilaTablaRespuestas): string | undefined =>
  (fila as unknown as { capacidad?: string }).capacidad ?? fila.nivel;
</script>

<template>
  <Teleport to="body">
    <Transition name="retro">
      <div v-if="open && resultado"
        class="fixed inset-0 z-[200] flex items-end sm:items-center justify-center sm:p-4 cursor-pointer"
        @click.self="emit('close')">
        <div class="absolute inset-0 bg-black/50 backdrop-blur-sm cursor-pointer" @click="emit('close')" />
        <div class="relative z-10 w-full sm:max-w-5xl bg-white dark:bg-slate-900 rounded-t-2xl sm:rounded-2xl shadow-2xl border border-slate-300 dark:border-slate-700 overflow-hidden flex flex-col max-h-[92dvh] sm:max-h-[85vh]">

          <!-- Drag handle (mobile) -->
          <div class="sm:hidden flex justify-center pt-3 pb-1 shrink-0" @click="emit('close')">
            <div class="w-10 h-1 rounded-full bg-slate-200 dark:bg-slate-600"></div>
          </div>

          <!-- Header -->
          <div class="flex items-center justify-between gap-3 px-4 sm:px-6 py-3 sm:py-4 border-b border-slate-200 dark:border-slate-700 shrink-0">
            <h3 class="text-sm sm:text-base font-bold text-slate-900 dark:text-white flex items-center gap-2 min-w-0">
              <Table class="w-4 h-4 text-indigo-500 shrink-0" />
              <span class="truncate">Matriz de Respuestas</span>
            </h3>
            <button @click="emit('close')" aria-label="Cerrar matriz de respuestas"
              class="w-8 h-8 rounded-full flex items-center justify-center bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-500 dark:text-slate-400 transition-colors cursor-pointer shrink-0">
              <X class="w-4 h-4" />
            </button>
          </div>

          <!-- Body -->
          <div class="flex-1 min-h-0 overflow-auto p-3 sm:p-5 pb-6 sm:pb-8">
            <table class="w-full text-sm min-w-[640px]">
              <thead>
                <tr class="border-b-2 border-slate-200 dark:border-slate-700">
                  <th class="text-left py-2.5 px-3 sm:px-4 text-slate-600 dark:text-slate-400 font-bold text-xs w-10">#</th>
                  <th class="text-left py-2.5 px-3 sm:px-4 text-slate-600 dark:text-slate-400 font-bold text-xs">Desempeño</th>
                  <th class="text-left py-2.5 px-3 sm:px-4 text-slate-600 dark:text-slate-400 font-bold text-xs">Capacidad</th>
                  <th class="text-center py-2.5 px-3 sm:px-4 text-slate-600 dark:text-slate-400 font-bold text-xs">Rpta.</th>
                  <th class="text-left py-2.5 px-3 sm:px-4 text-slate-600 dark:text-slate-400 font-bold text-xs">Justificación</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-100 dark:divide-slate-700">
                <tr v-for="fila in resultado.examen.tabla_respuestas" :key="fila.pregunta"
                  class="hover:bg-gray-50 dark:hover:bg-slate-800/50 transition-colors">
                  <td class="py-2.5 px-3 sm:px-4 text-slate-800 dark:text-slate-200 font-bold">{{ fila.pregunta }}</td>
                  <td class="py-2.5 px-3 sm:px-4 text-slate-600 dark:text-slate-400 text-xs"><MathText :text="fila.desempeno" /></td>
                  <td class="py-2.5 px-3 sm:px-4">
                    <span
                      class="px-2.5 py-1 text-[10px] font-bold rounded-lg inline-flex items-center"
                      :class="getCapacidadBadgeClass(capacidadDe(fila))">
                      {{ capacidadDe(fila) }}
                    </span>
                  </td>
                  <td class="py-2.5 px-3 sm:px-4 text-center">
                    <span
                      class="w-8 h-8 bg-gradient-to-br from-teal-400 to-teal-600 text-white rounded-lg inline-flex items-center justify-center font-bold text-sm shadow-lg shadow-teal-500/20">
                      {{ fila.respuesta_correcta }}
                    </span>
                  </td>
                  <td class="py-2.5 px-3 sm:px-4 text-slate-600 dark:text-slate-400 text-xs italic">
                    <MathText :text="fila.justificacion || 'No disponible'" />
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
