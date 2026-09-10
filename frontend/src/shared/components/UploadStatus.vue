<script setup lang="ts">
import { computed } from 'vue';
import { Loader2, AlertTriangle, FileQuestion, X, Eye } from 'lucide-vue-next';
import type { FilesMetadata } from '../types';
import { formatPalabras, formatFileSize, MAX_UPLOAD_FILES, MAX_UPLOAD_MB } from '../utils/uploadFeedback';
import FileTypeIcon from './FileTypeIcon.vue';

const props = withDefaults(defineProps<{
  uploading?: boolean;
  error?: string | null;
  metadata?: FilesMetadata | null;
  hasText?: boolean;
  accent?: 'teal' | 'indigo';
  compact?: boolean;
  removable?: boolean;
  /** Archivos originales en memoria, en el mismo orden que `metadata.archivos`.
   * Si hay File para un índice, se muestra el botón de vista previa. */
  previewFiles?: (File | null)[] | null;
}>(), {
  uploading: false,
  error: null,
  metadata: null,
  hasText: false,
  accent: 'teal',
  compact: false,
  removable: false,
  previewFiles: null,
});

const emit = defineEmits<{
  remove: [index: number];
  preview: [index: number];
}>();

const accentClasses = computed(() => props.accent === 'indigo'
  ? 'bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border-indigo-500/20'
  : 'bg-teal-500/10 text-teal-500 dark:text-teal-400 border-teal-500/20');

const showEmpty = computed(() =>
  !props.uploading && !props.error && !props.hasText && !(props.metadata && props.metadata.archivos.length > 0));
</script>

<template>
  <div class="space-y-2">
    <div v-if="uploading" class="flex items-center gap-2 rounded-lg border px-3 text-xs" :class="[accentClasses, compact ? 'py-2' : 'py-2.5']">
      <Loader2 class="w-3.5 h-3.5 animate-spin shrink-0" /> Procesando archivo...
    </div>

    <div v-if="error" class="flex items-center gap-2 rounded-lg border border-red-500/20 bg-red-500/10 px-3 text-xs text-red-500 dark:text-red-400" :class="compact ? 'py-2' : 'py-2.5'">
      <AlertTriangle class="w-3.5 h-3.5 shrink-0" /> {{ error }}
    </div>

    <div v-if="metadata && metadata.archivos.length > 0" class="flex flex-wrap gap-2">
      <div v-for="(archivo, idx) in metadata.archivos" :key="idx"
        class="flex min-w-0 max-w-full items-center gap-1.5 sm:gap-2 rounded-lg border border-emerald-500/20 bg-emerald-500/10 pl-1.5 pr-2 sm:pr-3 py-1.5 text-xs text-emerald-600 dark:text-emerald-400">
        <FileTypeIcon :filename="archivo.filename" :extension="archivo.extension" />
        <span class="truncate max-w-[8rem] sm:max-w-[12rem] font-medium">{{ archivo.filename }}</span>
        <span class="text-emerald-500/80 dark:text-emerald-400/80 whitespace-nowrap">· {{ formatPalabras(archivo.palabras) }}</span>
        <span v-if="archivo.size_kb" class="hidden sm:inline text-emerald-500/80 dark:text-emerald-400/80 whitespace-nowrap">· {{ formatFileSize(archivo.size_kb) }}</span>
        <button v-if="previewFiles?.[idx]" type="button" @click="emit('preview', idx)"
          class="ml-1 rounded-full p-1.5 hover:bg-emerald-500/20 transition-colors cursor-pointer shrink-0" :aria-label="`Vista previa de ${archivo.filename}`" :title="`Vista previa de ${archivo.filename}`">
          <Eye class="w-3.5 h-3.5" />
        </button>
        <button v-if="removable" type="button" @click="emit('remove', idx)"
          class="ml-1 rounded-full p-1.5 hover:bg-emerald-500/20 transition-colors cursor-pointer shrink-0" :aria-label="`Quitar ${archivo.filename}`">
          <X class="w-3 h-3" />
        </button>
      </div>
      <div v-if="metadata.archivos.length > 1" class="w-full text-[11px] text-slate-500 dark:text-slate-400">
        Total: {{ formatPalabras(metadata.total_palabras) }}
      </div>
    </div>

    <div v-if="metadata?.advertencias && metadata.advertencias.length > 0" class="flex items-start gap-2 rounded-lg border border-amber-500/20 bg-amber-500/10 px-3 py-2.5 text-xs text-amber-600 dark:text-amber-400">
      <AlertTriangle class="w-3.5 h-3.5 shrink-0 mt-0.5" />
      <div class="space-y-0.5">
        <p class="font-medium">Algunos archivos no se pudieron procesar:</p>
        <p v-for="(adv, idx) in metadata.advertencias" :key="idx">{{ adv.archivo }}: {{ adv.error }}</p>
      </div>
    </div>

    <div v-if="showEmpty" class="flex items-center gap-2 text-[11px] text-slate-400 dark:text-slate-500">
      <FileQuestion class="w-3.5 h-3.5 shrink-0" /> Sin contenido — sube hasta {{ MAX_UPLOAD_FILES }} PDF/Word (máx.
      {{ MAX_UPLOAD_MB }} MB c/u) o escribe el texto
    </div>
  </div>
</template>
