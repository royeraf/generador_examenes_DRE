<script setup lang="ts">
import { onMounted, onUnmounted, watch } from 'vue'
import { Award, X } from 'lucide-vue-next'
import EscalaCnebLeyenda from './EscalaCnebLeyenda.vue'
import BaseButton from './BaseButton.vue'

const props = defineProps<{ open: boolean }>()
const emit = defineEmits<{ close: [] }>()

function close() {
  emit('close')
}

function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape' && props.open) close()
}

watch(() => props.open, (isOpen) => {
  document.body.style.overflow = isOpen ? 'hidden' : ''
})

onMounted(() => window.addEventListener('keydown', onKeydown))
onUnmounted(() => {
  window.removeEventListener('keydown', onKeydown)
  document.body.style.overflow = ''
})
</script>

<template>
  <Teleport to="body">
    <!-- Backdrop -->
    <Transition
      enter-active-class="transition duration-300 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition duration-200 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="open"
        class="fixed inset-0 z-[140] bg-slate-900/60 dark:bg-slate-950/80 backdrop-blur-sm"
        @click="close"
      ></div>
    </Transition>

    <!-- Dialog -->
    <Transition
      enter-active-class="transition duration-300 ease-out transform"
      enter-from-class="translate-y-full sm:translate-y-8 sm:opacity-0"
      enter-to-class="translate-y-0 sm:opacity-100"
      leave-active-class="transition duration-200 ease-in transform"
      leave-from-class="translate-y-0 sm:opacity-100"
      leave-to-class="translate-y-full sm:translate-y-8 sm:opacity-0"
    >
      <div
        v-if="open"
        class="fixed inset-0 z-[141] flex items-end sm:items-center sm:justify-center sm:p-6"
        @click.self="close"
      >
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="escala-cneb-title"
          class="w-full sm:max-w-xl bg-white dark:bg-slate-900 rounded-t-[2.5rem] sm:rounded-2xl border-t sm:border border-slate-200 dark:border-slate-800 shadow-2xl flex flex-col max-h-[85vh] sm:max-h-[80vh] overflow-hidden"
        >
          <!-- Handle gesture bar (mobile only) -->
          <div class="py-3 flex justify-center shrink-0 cursor-pointer sm:hidden" @click="close">
            <div class="w-12 h-1.5 bg-slate-300 dark:bg-slate-700 rounded-full hover:bg-slate-400 dark:hover:bg-slate-600 transition-colors"></div>
          </div>

          <!-- Header -->
          <div class="px-6 pb-4 sm:pt-6 border-b border-slate-100 dark:border-slate-800 flex items-start justify-between gap-4 shrink-0">
            <div class="min-w-0 flex items-center gap-3">
              <div class="w-9 h-9 bg-gradient-to-br from-teal-400 to-emerald-500 rounded-xl flex items-center justify-center shrink-0">
                <Award class="w-4 h-4 text-white" />
              </div>
              <div class="min-w-0">
                <h3 id="escala-cneb-title" class="text-sm sm:text-base font-bold text-slate-900 dark:text-white">
                  Escala de calificación (CNEB)
                </h3>
                <p class="text-[11px] text-slate-400 dark:text-slate-500">
                  Niveles de logro del Currículo Nacional de la Educación Básica
                </p>
              </div>
            </div>
            <button
              type="button"
              @click="close"
              aria-label="Cerrar escala de calificación"
              class="w-8 h-8 rounded-full flex items-center justify-center bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-500 dark:text-slate-400 transition-colors cursor-pointer shrink-0"
            >
              <X class="w-4 h-4" />
            </button>
          </div>

          <!-- Body -->
          <div class="flex-1 overflow-y-auto p-4 sm:p-6">
            <EscalaCnebLeyenda />
          </div>

          <!-- Footer -->
          <div class="p-4 sm:p-6 border-t border-slate-100 dark:border-slate-800 shrink-0 bg-slate-50 dark:bg-slate-950/40">
            <BaseButton type="button" variant="primary" size="md" block @click="close">
              Entendido
            </BaseButton>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
