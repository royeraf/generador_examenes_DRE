<script setup lang="ts">
import { computed } from 'vue'
import {
  esNivelCneb,
  nivelCnebClass,
  NIVEL_CNEB_LABELS,
  type NivelCneb,
} from '../utils/escalaCneb'

const props = defineProps<{
  nivel?: string | null
  nota?: number | null
}>()

const esValido = computed(() => esNivelCneb(props.nivel))
const clase = computed(() => nivelCnebClass(props.nivel))
const titulo = computed(() =>
  esValido.value ? `${NIVEL_CNEB_LABELS[props.nivel as NivelCneb]} — ${props.nivel}` : undefined
)
</script>

<template>
  <span
    v-if="esValido"
    :class="clase"
    :title="titulo"
    class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-black uppercase tracking-wider border border-transparent leading-none"
  >
    <template v-if="nota != null">
      <span class="tabular-nums">{{ nota.toFixed(0) }}/20</span>
      <span class="opacity-50">·</span>
    </template>
    {{ nivel }}
  </span>
</template>
