<script setup lang="ts">
import { computed } from 'vue'
import { AlertCircle, CheckCircle2, X } from 'lucide-vue-next'
import BaseButton from '../../../shared/components/BaseButton.vue'
import MathText from '../../../shared/components/MathText.vue'
import type { Pregunta } from '../types'

const props = defineProps<{
  preguntas: Pregunta[]
  respuestas: Record<number, string>
  enviando: boolean
}>()

const emit = defineEmits<{
  cerrar: []
  enviar: []
  irAPregunta: [index: number]
}>()

interface FilaResumen {
  idx: number
  numero: number
  enunciado: string
  opcionMarcada: { letra: string; texto: string } | null
}

const filas = computed<FilaResumen[]>(() =>
  props.preguntas.map((pregunta, idx) => {
    const respuesta = props.respuestas[pregunta.numero]
    const opcion = respuesta === undefined
      ? undefined
      : pregunta.opciones.find(o => (o.valor ?? o.letra) === respuesta)
    return {
      idx,
      numero: pregunta.numero,
      enunciado: pregunta.enunciado,
      opcionMarcada: opcion ? { letra: opcion.letra, texto: opcion.texto } : null,
    }
  })
)

const marcadas = computed(() => filas.value.filter(f => f.opcionMarcada !== null).length)
const sinMarcar = computed(() => filas.value.filter(f => f.opcionMarcada === null))

function irA(idx: number) {
  emit('irAPregunta', idx)
}

function irAPrimeraSinMarcar() {
  const primera = sinMarcar.value[0]
  if (primera) emit('irAPregunta', primera.idx)
}
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition duration-300 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition duration-200 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div class="fixed inset-0 z-[100] bg-slate-900/60 dark:bg-slate-950/80 backdrop-blur-sm transition-opacity"
        @click="emit('cerrar')">
      </div>
    </Transition>

    <Transition
      enter-active-class="transition duration-300 ease-out transform"
      enter-from-class="translate-y-full sm:translate-y-8 sm:opacity-0"
      enter-to-class="translate-y-0 sm:opacity-100"
      leave-active-class="transition duration-200 ease-in transform"
      leave-from-class="translate-y-0 sm:opacity-100"
      leave-to-class="translate-y-full sm:translate-y-8 sm:opacity-0"
    >
      <div
        class="fixed bottom-0 inset-x-0 sm:inset-0 z-[101] flex sm:items-center sm:justify-center sm:p-6"
      >
        <div
          class="w-full sm:max-w-lg bg-white dark:bg-slate-900 rounded-t-[2.5rem] sm:rounded-2xl border-t sm:border border-slate-200 dark:border-slate-800 shadow-2xl flex flex-col max-h-[85vh] sm:max-h-[80vh] overflow-hidden"
        >
          <!-- Handle gesture bar (mobile only) -->
          <div class="py-3 flex justify-center shrink-0 cursor-pointer sm:hidden" @click="emit('cerrar')">
            <div class="w-12 h-1.5 bg-slate-300 dark:bg-slate-700 rounded-full hover:bg-slate-400 dark:hover:bg-slate-600 transition-colors"></div>
          </div>

          <!-- Header -->
          <div class="px-6 pb-4 sm:pt-6 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between shrink-0 gap-4">
            <div class="min-w-0">
              <h3 class="text-sm sm:text-base font-bold text-slate-900 dark:text-white">Revisa tus respuestas</h3>
              <p class="text-xs mt-0.5 flex items-center gap-1.5">
                <span class="text-teal-600 dark:text-teal-400 font-bold">{{ marcadas }} marcadas</span>
                <span class="text-slate-300 dark:text-slate-700">&middot;</span>
                <span :class="sinMarcar.length > 0 ? 'text-red-500 font-bold' : 'text-slate-400'">
                  {{ sinMarcar.length }} sin marcar
                </span>
              </p>
            </div>
            <button @click="emit('cerrar')"
              class="w-8 h-8 rounded-full flex items-center justify-center bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-500 dark:text-slate-400 transition-colors cursor-pointer shrink-0">
              <X class="w-4 h-4" />
            </button>
          </div>

          <!-- List -->
          <div class="flex-1 overflow-y-auto p-4 sm:p-6 custom-scrollbar space-y-2">
            <button
              v-for="fila in filas"
              :key="fila.numero"
              type="button"
              @click="irA(fila.idx)"
              :class="[
                'w-full text-left px-4 py-3 rounded-xl border transition-all flex items-center gap-3 cursor-pointer',
                fila.opcionMarcada
                  ? 'border-slate-200 dark:border-slate-800 bg-slate-50/60 dark:bg-slate-800/40 hover:border-indigo-300 dark:hover:border-indigo-500/40'
                  : 'border-red-200 dark:border-red-500/30 bg-red-50 dark:bg-red-500/10 hover:border-red-400'
              ]"
            >
              <span class="w-7 h-7 rounded-lg bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-300 flex items-center justify-center text-xs font-black shrink-0">
                {{ fila.numero }}
              </span>
              <MathText as="span" class="flex-1 min-w-0 text-sm text-slate-700 dark:text-slate-300 line-clamp-2"
                :text="fila.enunciado" />
              <span v-if="fila.opcionMarcada"
                class="shrink-0 flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-indigo-100 dark:bg-indigo-500/20 text-indigo-700 dark:text-indigo-300 text-xs font-black">
                {{ fila.opcionMarcada.letra }}
              </span>
              <span v-else
                class="shrink-0 flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-red-500 text-white text-[10px] font-black uppercase tracking-wide">
                <AlertCircle class="w-3.5 h-3.5" />
                Sin responder
              </span>
            </button>
          </div>

          <!-- Footer -->
          <div class="p-4 sm:p-6 border-t border-slate-100 dark:border-slate-800 shrink-0 bg-slate-50 dark:bg-slate-950/40">
            <p v-if="sinMarcar.length > 0" class="text-xs text-red-500 font-medium mb-3 text-center">
              Debes responder todas las preguntas antes de enviar.
            </p>
            <div class="flex flex-col-reverse sm:flex-row gap-3">
              <BaseButton type="button" variant="secondary" size="md" block @click="emit('cerrar')">
                Seguir revisando
              </BaseButton>
              <BaseButton
                v-if="sinMarcar.length > 0"
                type="button"
                variant="destructive"
                size="md"
                block
                @click="irAPrimeraSinMarcar"
              >
                <template #icon><AlertCircle class="w-4 h-4" /></template>
                Ir a la primera sin responder
              </BaseButton>
              <BaseButton
                v-else
                type="button"
                variant="primary"
                size="md"
                block
                :loading="enviando"
                @click="emit('enviar')"
              >
                <template #icon><CheckCircle2 class="w-4 h-4" /></template>
                Enviar examen
              </BaseButton>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, 0.2);
  border-radius: 10px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(148, 163, 184, 0.4);
}
</style>
