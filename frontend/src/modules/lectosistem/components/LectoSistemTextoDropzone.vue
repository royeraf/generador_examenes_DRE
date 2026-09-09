<script setup lang="ts">
import { ref, computed } from 'vue';
import {
  CloudUpload,
  FileCheck,
  FileText,
  Loader2,
  Eye,
  RefreshCw,
  Trash2,
  Plus,
  AlertTriangle
} from 'lucide-vue-next';
import type { TextoBaseItem, TextosBaseStatus } from '../composables/useLectoSistem';
import { formatPalabras } from '../../../shared/utils/uploadFeedback';

const props = defineProps<{
  textosBase: TextoBaseItem[];
  status: TextosBaseStatus;
}>();

const emit = defineEmits<{
  (e: 'uploadFiles', files: File[], idx?: number): void;
  (e: 'openModal'): void;
  (e: 'clearFiles', idx: number): void;
  (e: 'addTexto'): void;
}>();

const isDragging = ref(false);
const fileInputRef = ref<HTMLInputElement | null>(null);

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

const summaryLabel = computed(() => {
  const conArchivos = props.textosBase.filter(t => t.filesMetadata && t.filesMetadata.archivos.length > 0);
  if (conArchivos.length > 0) {
    return conArchivos.length === 1 ? 'Archivo cargado' : `${conArchivos.length} archivos`;
  }
  return filledItems.value.length === 1 ? 'Lectura lista' : `${filledItems.value.length} lecturas listas`;
});

const triggerFileInput = () => {
  if (fileInputRef.value) {
    fileInputRef.value.value = '';
    fileInputRef.value.click();
  }
};

const onFileInputChange = (event: Event) => {
  const input = event.target as HTMLInputElement;
  if (input.files && input.files.length > 0) {
    emit('uploadFiles', Array.from(input.files), 0);
  }
};

const onDrop = (event: DragEvent) => {
  isDragging.value = false;
  if (event.dataTransfer?.files && event.dataTransfer.files.length > 0) {
    emit('uploadFiles', Array.from(event.dataTransfer.files), 0);
  }
};
</script>

<template>
  <div class="space-y-2">
    <!-- Input oculto para selección de archivos -->
    <input
      ref="fileInputRef"
      type="file"
      accept=".pdf,.doc,.docx"
      multiple
      class="hidden"
      @change="onFileInputChange"
    />

    <!-- Estado 1: Extracción en progreso (Uploading) -->
    <div
      v-if="isUploading"
      class="p-4 rounded-xl border-2 border-dashed border-teal-400 dark:border-teal-500 bg-teal-50/70 dark:bg-teal-950/40 flex flex-col items-center justify-center gap-2 text-center"
    >
      <Loader2 class="w-7 h-7 text-teal-500 animate-spin" />
      <span class="text-xs font-bold text-teal-800 dark:text-teal-200">Extrayendo texto del archivo...</span>
      <span class="text-[10px] text-slate-500 dark:text-slate-400">Analizando lectura y contando palabras</span>
    </div>

    <!-- Estado 2: Error al procesar archivo -->
    <div
      v-else-if="uploadError"
      class="p-3 rounded-xl border border-red-200 dark:border-red-900/50 bg-red-50/80 dark:bg-red-950/30 flex flex-col gap-2"
    >
      <div class="flex items-start gap-2 text-red-600 dark:text-red-400">
        <AlertTriangle class="w-4 h-4 shrink-0 mt-0.5" />
        <p class="text-xs font-semibold leading-tight">{{ uploadError }}</p>
      </div>
      <div class="flex items-center gap-2 justify-end">
        <button
          type="button"
          @click="emit('clearFiles', 0)"
          class="text-[11px] font-bold text-red-600 dark:text-red-400 hover:underline cursor-pointer"
        >
          Descartar
        </button>
        <button
          type="button"
          @click="triggerFileInput"
          class="text-[11px] font-bold text-teal-600 dark:text-teal-400 hover:underline cursor-pointer"
        >
          Intentar con otro archivo
        </button>
      </div>
    </div>

    <!-- Estado 3: Archivo o lectura ya cargada (Listo) -->
    <div
      v-else-if="hasContent"
      class="rounded-xl border border-emerald-300/80 dark:border-emerald-700/60 bg-emerald-50/40 dark:bg-emerald-950/20 p-3 space-y-2.5 transition-all"
    >
      <!-- Cabecera de estado -->
      <div class="flex items-center justify-between gap-2">
        <div class="flex items-center gap-1.5 min-w-0">
          <span class="w-6 h-6 rounded-lg bg-emerald-100 dark:bg-emerald-900/60 text-emerald-600 dark:text-emerald-300 flex items-center justify-center shrink-0">
            <FileCheck class="w-3.5 h-3.5" />
          </span>
          <span class="text-xs font-bold text-emerald-800 dark:text-emerald-200 truncate">
            {{ summaryLabel }}
          </span>
        </div>
        <span class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 dark:bg-emerald-900/50 text-emerald-700 dark:text-emerald-300 shrink-0">
          {{ props.status.count.filled }}/{{ props.status.count.total }}
        </span>
      </div>

      <!-- Detalle del archivo cargado -->
      <div class="p-2.5 rounded-lg bg-white/80 dark:bg-slate-900/70 border border-emerald-200/70 dark:border-emerald-800/40">
        <div class="flex items-center gap-2">
          <FileText class="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
          <div class="min-w-0 flex-1">
            <p class="text-xs font-bold text-slate-800 dark:text-slate-100 truncate" :title="primaryFilename">
              {{ primaryFilename }}
            </p>
            <p class="text-[10px] font-semibold text-emerald-700 dark:text-emerald-400">
              {{ wordsSummary }}
            </p>
          </div>
        </div>
      </div>

      <!-- Barra de acciones rápidas -->
      <div class="flex items-center gap-1.5 pt-0.5">
        <button
          type="button"
          @click="emit('openModal')"
          class="flex-1 py-1.5 px-2 rounded-lg bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-700 text-[11px] font-bold text-slate-700 dark:text-slate-200 flex items-center justify-center gap-1 transition-colors cursor-pointer"
        >
          <Eye class="w-3 h-3 text-slate-500 dark:text-slate-400" />
          <span>Ver / Editar</span>
        </button>

        <button
          type="button"
          @click="triggerFileInput"
          class="py-1.5 px-2.5 rounded-lg bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-700 text-[11px] font-bold text-slate-700 dark:text-slate-200 flex items-center justify-center gap-1 transition-colors cursor-pointer"
          title="Reemplazar archivo"
        >
          <RefreshCw class="w-3 h-3 text-teal-600 dark:text-teal-400" />
          <span>Cambiar</span>
        </button>

        <button
          type="button"
          @click="emit('clearFiles', 0)"
          class="py-1.5 px-2 rounded-lg bg-white dark:bg-slate-800 border border-red-200 dark:border-red-900/50 hover:bg-red-50 dark:hover:bg-red-900/30 text-[11px] font-bold text-red-600 dark:text-red-400 flex items-center justify-center transition-colors cursor-pointer"
          title="Eliminar texto base"
        >
          <Trash2 class="w-3.5 h-3.5" />
        </button>
      </div>

      <!-- Enlace para añadir otro texto si < 4 -->
      <div v-if="props.textosBase.length < 4" class="pt-1 text-center">
        <button
          type="button"
          @click="emit('openModal')"
          class="text-[10px] font-semibold text-teal-600 dark:text-teal-400 hover:underline flex items-center justify-center gap-1 w-full cursor-pointer"
        >
          <Plus class="w-3 h-3" /> Añadir otro texto base (hasta 4)
        </button>
      </div>
    </div>

    <!-- Estado 4: Dropzone Vacío y Sugerente -->
    <div
      v-else
      @dragover.prevent="isDragging = true"
      @dragleave.prevent="isDragging = false"
      @drop.prevent="onDrop"
      @click="triggerFileInput"
      class="border-2 border-dashed rounded-xl p-4 text-center cursor-pointer transition-all duration-200 group relative flex flex-col items-center justify-center"
      :class="isDragging
        ? 'border-teal-500 bg-teal-50 dark:bg-teal-950/60 shadow-sm scale-[1.01] ring-2 ring-teal-500/20'
        : 'border-slate-300 dark:border-slate-600 hover:border-teal-500 dark:hover:border-teal-400 bg-slate-50/70 dark:bg-slate-900/40 hover:bg-teal-50/40 dark:hover:bg-teal-950/30'"
    >
      <!-- Ícono animado en hover -->
      <div class="w-11 h-11 rounded-xl bg-teal-100 dark:bg-teal-900/50 text-teal-600 dark:text-teal-400 flex items-center justify-center mb-2 group-hover:scale-110 group-hover:bg-teal-500 group-hover:text-white transition-all shadow-xs">
        <CloudUpload class="w-5 h-5" />
      </div>

      <!-- Textos sugerentes -->
      <p class="text-xs font-bold text-slate-800 dark:text-slate-100 leading-snug">
        Subir lectura o arrastrar archivo
      </p>
      <p class="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
        Haz clic para examinar archivos
      </p>

      <!-- Badges de formatos soportados -->
      <div class="flex items-center gap-1.5 mt-2.5">
        <span class="px-2 py-0.5 rounded-full bg-slate-200/80 dark:bg-slate-800 text-[10px] font-bold text-slate-600 dark:text-slate-300">
          PDF
        </span>
        <span class="px-2 py-0.5 rounded-full bg-slate-200/80 dark:bg-slate-800 text-[10px] font-bold text-slate-600 dark:text-slate-300">
          Word (.docx)
        </span>
      </div>

      <!-- Vía alternativa: redactar o pegar texto manualmente -->
      <button
        type="button"
        @click.stop="emit('openModal')"
        class="mt-3 text-[11px] text-teal-600 dark:text-teal-400 hover:text-teal-700 dark:hover:text-teal-300 font-semibold flex items-center gap-1 cursor-pointer transition-colors"
      >
        <FileText class="w-3 h-3" />
        <span>o escribir / pegar texto manualmente</span>
      </button>
    </div>
  </div>
</template>
