<script setup lang="ts">
import { onMounted, onUnmounted, shallowRef } from 'vue';
import { FileUp, X, CloudUpload, Trash2 } from 'lucide-vue-next';
import type { FilesMetadata } from '../types';
import { ACCEPT_UPLOAD, MAX_UPLOAD_FILES, MAX_UPLOAD_MB, countWords, formatPalabras } from '../utils/uploadFeedback';
import BaseButton from './BaseButton.vue';
import UploadStatus from './UploadStatus.vue';

const props = withDefaults(defineProps<{
  open: boolean;
  uploading?: boolean;
  error?: string | null;
  metadata?: FilesMetadata | null;
  modelValue: string;
}>(), {
  uploading: false,
  error: null,
  metadata: null,
});

const emit = defineEmits<{
  close: [];
  'update:modelValue': [value: string];
  files: [files: File[]];
  remove: [index: number];
  clear: [];
}>();

const isDragging = shallowRef(false);

function onInputChange(event: Event) {
  const input = event.target as HTMLInputElement;
  const files = input.files;
  if (files && files.length > 0) {
    emit('files', Array.from(files));
  }
  input.value = '';
}

function onDrop(event: DragEvent) {
  isDragging.value = false;
  const files = event.dataTransfer?.files;
  if (files && files.length > 0) {
    emit('files', Array.from(files));
  }
}

function onEscape(event: KeyboardEvent) {
  if (event.key === 'Escape' && props.open) emit('close');
}

onMounted(() => window.addEventListener('keydown', onEscape));
onUnmounted(() => window.removeEventListener('keydown', onEscape));
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
      <div v-if="open" class="fixed inset-0 z-[100] bg-slate-900/60 dark:bg-slate-950/80 backdrop-blur-sm transition-opacity"
        @click="emit('close')">
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
      <div v-if="open" class="fixed bottom-0 inset-x-0 sm:inset-0 z-[101] flex sm:items-center sm:justify-center sm:p-6">
        <div
          class="w-full sm:max-w-lg bg-white dark:bg-slate-900 rounded-t-[2.5rem] sm:rounded-2xl border-t sm:border border-slate-200 dark:border-slate-800 shadow-2xl flex flex-col max-h-[85vh] sm:max-h-[80vh] overflow-hidden">
          <!-- Handle gesture bar (mobile only) -->
          <div class="py-3 flex justify-center shrink-0 cursor-pointer sm:hidden" @click="emit('close')">
            <div class="w-12 h-1.5 bg-slate-300 dark:bg-slate-700 rounded-full hover:bg-slate-400 dark:hover:bg-slate-600 transition-colors"></div>
          </div>

          <!-- Header -->
          <div class="px-6 pb-4 sm:pt-6 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between shrink-0 gap-4">
            <div class="min-w-0 flex items-center gap-3">
              <div class="w-9 h-9 bg-gradient-to-br from-sky-400 to-sky-600 rounded-xl flex items-center justify-center shrink-0">
                <FileUp class="w-4 h-4 text-white" />
              </div>
              <div class="min-w-0">
                <h3 class="text-sm sm:text-base font-bold text-slate-900 dark:text-white">Texto base</h3>
                <p class="text-[11px] text-slate-400 dark:text-slate-500">
                  PDF o Word · hasta {{ MAX_UPLOAD_FILES }} archivos · máx. {{ MAX_UPLOAD_MB }} MB c/u
                </p>
              </div>
            </div>
            <button @click="emit('close')"
              class="w-8 h-8 rounded-full flex items-center justify-center bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-500 dark:text-slate-400 transition-colors cursor-pointer shrink-0">
              <X class="w-4 h-4" />
            </button>
          </div>

          <!-- Body -->
          <div class="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4">

            <!-- Dropzone -->
            <div class="relative rounded-xl border-2 border-dashed transition-all duration-200"
              :class="isDragging
                ? 'border-teal-400 bg-teal-50 dark:bg-teal-900/20'
                : 'border-sky-300 dark:border-slate-600 bg-gradient-to-br from-sky-50 to-teal-50 dark:bg-slate-950'"
              @dragover.prevent="isDragging = true" @dragleave.prevent="isDragging = false" @drop.prevent="onDrop">
              <input type="file" :accept="ACCEPT_UPLOAD" multiple class="hidden" id="texto-base-file-input"
                @change="onInputChange" />
              <label for="texto-base-file-input"
                class="flex flex-col items-center justify-center py-6 px-4 cursor-pointer">
                <CloudUpload class="w-7 h-7 text-teal-500 mb-1.5" />
                <span class="text-teal-700 dark:text-slate-300 text-sm font-semibold">Arrastra un archivo o haz clic para elegir</span>
                <span class="text-teal-600/70 dark:text-slate-500 text-xs mt-0.5">PDF o Word</span>
              </label>
            </div>

            <UploadStatus :uploading="uploading" :error="error" :metadata="metadata" :has-text="modelValue.trim() !== ''"
              accent="teal" removable @remove="(idx) => emit('remove', idx)" />

            <!-- Texto -->
            <div class="space-y-1.5">
              <div class="flex items-center justify-between">
                <span class="text-xs font-bold text-slate-500 dark:text-slate-400">O escribe / edita el texto</span>
                <span class="text-[11px] text-slate-400 dark:text-slate-500">{{ formatPalabras(countWords(modelValue)) }}</span>
              </div>
              <textarea :value="modelValue" @input="emit('update:modelValue', ($event.target as HTMLTextAreaElement).value)"
                rows="6" placeholder="Escribe o pega el texto base aquí..."
                class="w-full text-sm rounded-xl border-2 border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-950 p-3 text-slate-700 dark:text-slate-300 focus:outline-none focus:ring-2 focus:ring-teal-500/40 focus:border-teal-400 resize-none"></textarea>
            </div>
          </div>

          <!-- Footer -->
          <div class="p-4 sm:p-6 border-t border-slate-100 dark:border-slate-800 shrink-0 bg-slate-50 dark:bg-slate-950/40 flex flex-col-reverse sm:flex-row gap-3">
            <BaseButton v-if="metadata || modelValue.trim() !== ''" type="button" variant="destructive" size="md" block
              @click="emit('clear')">
              <template #icon><Trash2 class="w-4 h-4" /></template>
              Quitar todo
            </BaseButton>
            <BaseButton type="button" variant="primary" size="md" block @click="emit('close')">
              Listo
            </BaseButton>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
