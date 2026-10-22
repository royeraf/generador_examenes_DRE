<script setup lang="ts">
import { ESCALA_CNEB, NIVEL_CNEB_COLORS, type NivelCneb } from '../utils/escalaCneb'
</script>

<template>
  <div class="rounded-2xl border border-slate-300 dark:border-slate-800 overflow-hidden">
    <div class="hidden sm:grid sm:grid-cols-[3.5rem_1.2fr_2fr_5rem] gap-3 px-4 py-2.5 bg-slate-50 dark:bg-slate-800/50 border-b border-slate-200 dark:border-slate-800">
      <span class="text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-wider">Escala</span>
      <span class="text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-wider">Nivel</span>
      <span class="text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-wider">Significado</span>
      <span class="text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-wider">Rango</span>
    </div>

    <div v-for="n in ESCALA_CNEB" :key="n.codigo"
      class="px-4 py-3 border-b border-slate-200 dark:border-slate-800 last:border-b-0">
      <div class="sm:grid sm:grid-cols-[3.5rem_1.2fr_2fr_5rem] sm:gap-3 sm:items-center space-y-1.5 sm:space-y-0">
        <span class="inline-flex items-center justify-center w-9 h-9 rounded-lg text-sm font-black border border-transparent"
          :class="NIVEL_CNEB_COLORS[n.codigo as NivelCneb]">
          {{ n.codigo }}
        </span>
        <span class="block text-xs font-bold text-slate-700 dark:text-slate-200">{{ n.nombre }}</span>
        <span class="block text-xs text-slate-500 dark:text-slate-400 leading-snug">{{ n.significado }}</span>
        <span class="block text-xs font-black tabular-nums text-slate-700 dark:text-slate-200">
          {{ String(n.min).padStart(2, '0') }} – {{ n.max }}
        </span>
      </div>
    </div>
  </div>
</template>
