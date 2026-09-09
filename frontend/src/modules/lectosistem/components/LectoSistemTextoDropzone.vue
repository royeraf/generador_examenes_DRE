<script setup lang="ts">
import { computed } from 'vue';
import {
  CloudUpload,
  FileCheck,
  Loader2,
  AlertTriangle,
  ExternalLink
} from 'lucide-vue-next';
import type { TextoBaseItem, TextosBaseStatus } from '../composables/useLectoSistem';
import { formatPalabras } from '../../../shared/utils/uploadFeedback';

const props = defineProps<{
  textosBase: TextoBaseItem[];
  status: TextosBaseStatus;
}>();

const emit = defineEmits<{
  (e: 'openModal'): void;
}>();

const isUploading = computed(() => props.textosBase.some(t => t.uploadingFile));

const uploadError = computed(() => {
  const item = props.textosBase.find(t => !!t.uploadError);
  return item?.uploadError || null;
});

const filledItems = computed(() =>
  props.textosBase.filter(t => t.texto.trim().length > 0 || (t.filesMetadata && t.filesMetadata.archivos.length > 0))
);

const hasContent = computed(() => filledItems.value.length > 0);

const primaryItem = computed(() => filledItems.value[0] ?? props.textosBase[0] ?? null);

const primaryFilename = computed(() => {
  const meta = primaryItem.value?.filesMetadata;
  if (meta && meta.archivos && meta.archivos.length > 0) {
    const firstFile = meta.archivos[0];
    if (firstFile) {
      if (meta.archivos.length === 1) {
        return firstFile.filename;
      }
      return `${firstFile.filename} (+${meta.archivos.length - 1} más)`;
    }
  }
  if (primaryItem.value?.texto?.trim()) {
    return primaryItem.value.titulo?.trim() || 'Texto escrito manualmente';
  }
  return '';
});

const totalWords = computed(() => {
  return props.textosBase.reduce((acc, item) => {
    if (item.filesMetadata?.total_palabras) {
      return acc + item.filesMetadata.total_palabras;
    }
    if (item.texto.trim()) {
      const words = item.texto.trim().split(/\s+/).filter(Boolean).length;
      return acc + words;
    }
    return acc;
  }, 0);
});

const wordsSummary = computed(() => formatPalabras(totalWords.value));
</script>

<template>
  <div class="space-y-1.5">
    <!-- Estado 1: Extracción en progreso (Uploading) -->
    <div
      v-if="isUploading"
      class="p-2.5 rounded-xl border-2 border-dashed border-teal-400 dark:border-teal-500 bg-teal-50/70 dark:bg-teal-950/40 flex items-center gap-2.5"
    >
      <Loader2 class="w-5 h-5 text-teal-500 animate-spin shrink-0" />
      <div class="flex-1 min-w-0">
        <p class="text-xs font-bold text-teal-800 dark:text-teal-200 truncate">Extrayendo texto...</p>
        <p class="text-[10px] text-slate-500 dark:text-slate-400 truncate">Analizando lectura</p>
      </div>
    </div>

    <!-- Estado 2: Error al procesar archivo -->
    <div
      v-else-if="uploadError"
      @click="emit('openModal')"
      class="p-2.5 rounded-xl border border-red-200 dark:border-red-900/50 bg-red-50/80 dark:bg-red-950/30 flex items-center justify-between gap-2 cursor-pointer hover:bg-red-100/70 transition-colors"
      title="Haz clic para abrir el gestor y revisar"
    >
      <div class="flex items-center gap-2 min-w-0 flex-1">
        <AlertTriangle class="w-4 h-4 text-red-600 dark:text-red-400 shrink-0" />
        <p class="text-xs font-semibold text-red-600 dark:text-red-400 truncate">{{ uploadError }}</p>
      </div>
      <span class="text-[10px] font-bold px-2 py-0.5 rounded bg-teal-500 text-white shrink-0">
        Revisar
      </span>
    </div>

    <!-- Estado 3: Resumen de archivos subidos (Exclusivamente informativo, abre modal) -->
    <div
      v-else-if="hasContent"
      @click="emit('openModal')"
      class="p-2.5 rounded-xl border border-emerald-300/80 dark:border-emerald-700/60 bg-emerald-50/40 dark:bg-emerald-950/20 flex items-center gap-2.5 transition-all cursor-pointer hover:border-emerald-400 dark:hover:border-emerald-500 hover:bg-emerald-50/70 dark:hover:bg-emerald-950/30 group"
      title="Haz clic para abrir el gestor de textos"
    >
      <!-- Ícono verde -->
      <div class="w-8 h-8 rounded-lg bg-emerald-100 dark:bg-emerald-900/60 text-emerald-600 dark:text-emerald-300 flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform">
        <FileCheck class="w-4 h-4" />
      </div>

      <!-- Datos del archivo/lectura -->
      <div class="flex-1 min-w-0 text-left">
        <p class="text-xs font-bold text-slate-800 dark:text-slate-100 truncate" :title="primaryFilename">
          {{ primaryFilename }}
        </p>
        <p class="text-[10px] font-bold text-emerald-600 dark:text-emerald-400 truncate">
          {{ wordsSummary }}
        </p>
      </div>

      <!-- Resumen: badge de conteo e indicador de apertura -->
      <div class="flex items-center gap-1.5 shrink-0">
        <span class="text-[9px] font-bold px-1.5 py-0.5 rounded-full bg-emerald-100 dark:bg-emerald-900/50 text-emerald-700 dark:text-emerald-300 border border-emerald-500/20">
          {{ props.status.count.filled }}/{{ props.status.count.total }}
        </span>
        <ExternalLink class="w-3.5 h-3.5 text-slate-400 group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors" />
      </div>
    </div>

    <!-- Estado 4: Activador Visual Sugerente Compacto (Abre Modal al Clic) -->
    <div
      v-else
      @click="emit('openModal')"
      class="p-2.5 rounded-xl border-2 border-dashed flex items-center gap-2.5 cursor-pointer transition-all duration-200 group border-slate-300 dark:border-slate-600 hover:border-teal-500 dark:hover:border-teal-400 bg-slate-50/70 dark:bg-slate-900/40 hover:bg-teal-50/40 dark:hover:bg-teal-950/30"
    >
      <!-- Ícono compacto -->
      <div class="w-8 h-8 rounded-lg bg-teal-100 dark:bg-teal-900/50 text-teal-600 dark:text-teal-400 flex items-center justify-center shrink-0 group-hover:scale-105 group-hover:bg-teal-500 group-hover:text-white transition-all shadow-2xs">
        <CloudUpload class="w-4 h-4" />
      </div>

      <!-- Textos -->
      <div class="flex-1 min-w-0 text-left">
        <p class="text-xs font-bold text-slate-800 dark:text-slate-100 truncate">
          Subir o redactar lectura
        </p>
        <p class="text-[10px] text-slate-500 dark:text-slate-400 truncate">
          Haz clic para abrir el gestor
        </p>
      </div>

      <!-- Badges / Indicador -->
      <div class="flex items-center gap-1.5 shrink-0">
        <span class="px-1.5 py-0.5 rounded-md bg-teal-500/10 text-[9px] font-bold text-teal-700 dark:text-teal-300 border border-teal-500/20">
          PDF · Word
        </span>
        <ExternalLink class="w-3.5 h-3.5 text-slate-400 group-hover:text-teal-500 transition-colors" />
      </div>
    </div>
  </div>
</template>
