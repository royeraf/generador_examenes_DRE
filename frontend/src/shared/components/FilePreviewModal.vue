<script setup lang="ts">
import { computed, onUnmounted, shallowRef, watch } from 'vue';
import { X, ExternalLink, AlertTriangle, Loader2, FileWarning } from 'lucide-vue-next';
import { getFileKind } from '../utils/uploadFeedback';
import FileTypeIcon from './FileTypeIcon.vue';

/**
 * Visor estándar de archivos subidos para todo el sistema.
 * - PDF: visor nativo del navegador (iframe).
 * - DOCX: render fiel con mammoth (formato, tablas, listas, imágenes).
 * - DOC (antiguo): sin vista previa — aviso + datos del archivo.
 * El `file` es el objeto original en memoria (solo disponible en sesión).
 */
const props = defineProps<{
  open: boolean;
  file: File | null;
  url: string | null;
}>();

const emit = defineEmits<{
  close: [];
}>();

const kind = computed(() => getFileKind(props.file?.name ?? ''));

const docxHtml = shallowRef<string | null>(null);
const docxLoading = shallowRef(false);
const docxError = shallowRef<string | null>(null);

let requestId = 0;

watch(() => props.file, async (file) => {
  docxHtml.value = null;
  docxError.value = null;
  if (!file || getFileKind(file.name) !== 'word' || file.name.toLowerCase().endsWith('.doc')) return;
  const current = ++requestId;
  docxLoading.value = true;
  try {
    // Import diferido: mammoth (~500 KB) solo se descarga al previsualizar un Word.
    const { default: mammoth } = await import('mammoth');
    const arrayBuffer = await file.arrayBuffer();
    const result = await mammoth.convertToHtml({ arrayBuffer });
    if (current !== requestId) return;
    docxHtml.value = result.value;
    if (!result.value.trim()) {
      docxError.value = 'No se pudo extraer contenido visible de este documento.';
    }
  } catch {
    if (current !== requestId) return;
    docxError.value = 'No se pudo mostrar este documento. El texto extraído sigue disponible.';
  } finally {
    if (current === requestId) docxLoading.value = false;
  }
}, { immediate: true });

function onEscape(event: KeyboardEvent) {
  if (event.key === 'Escape' && props.open) emit('close');
}

watch(() => props.open, (isOpen) => {
  if (isOpen) window.addEventListener('keydown', onEscape);
  else window.removeEventListener('keydown', onEscape);
  // Bloquea el scroll de la página detrás (visor a pantalla completa).
  document.body.style.overflow = isOpen ? 'hidden' : '';
});

onUnmounted(() => {
  window.removeEventListener('keydown', onEscape);
  document.body.style.overflow = '';
});
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
      <div v-if="open" class="fixed inset-0 z-[120] bg-slate-900/60 dark:bg-slate-950/80 backdrop-blur-sm cursor-pointer" @click="emit('close')"></div>
    </Transition>

    <Transition
      enter-active-class="transition duration-300 ease-out transform"
      enter-from-class="opacity-0 scale-95"
      enter-to-class="opacity-100 scale-100"
      leave-active-class="transition duration-200 ease-in transform"
      leave-from-class="opacity-100 scale-100"
      leave-to-class="opacity-0 scale-95"
    >
      <div v-if="open && file" class="fixed inset-0 z-[121] flex pointer-events-none">
        <div class="pointer-events-auto w-full h-full h-dvh bg-white dark:bg-slate-900 sm:border border-slate-200 dark:border-slate-700 shadow-2xl flex flex-col overflow-hidden">

          <!-- Header -->
          <div class="px-4 sm:px-6 pt-[max(0.75rem,env(safe-area-inset-top))] sm:pt-5 pb-3 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between gap-3 shrink-0">
            <div class="min-w-0 flex items-center gap-3">
              <FileTypeIcon :filename="file.name" size="md" />
              <div class="min-w-0">
                <h3 class="text-sm sm:text-base font-bold text-slate-900 dark:text-white truncate" :title="file.name">{{ file.name }}</h3>
                <p class="text-[11px] text-slate-400 dark:text-slate-500">Vista previa · {{ kind === 'pdf' ? 'PDF' : 'Word' }}</p>
              </div>
            </div>
            <div class="flex items-center gap-2 shrink-0">
              <a v-if="url" :href="url" target="_blank" rel="noopener"
                class="w-8 h-8 rounded-full flex items-center justify-center bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-500 dark:text-slate-400 transition-colors" title="Abrir en pestaña nueva">
                <ExternalLink class="w-4 h-4" />
              </a>
              <button @click="emit('close')" aria-label="Cerrar vista previa"
                class="w-8 h-8 rounded-full flex items-center justify-center bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-500 dark:text-slate-400 transition-colors cursor-pointer">
                <X class="w-4 h-4" />
              </button>
            </div>
          </div>

          <!-- Body -->
          <div class="flex-1 min-h-0 bg-slate-100 dark:bg-slate-950 p-3 sm:p-4 pb-[max(0.75rem,env(safe-area-inset-bottom))] sm:pb-[max(1rem,env(safe-area-inset-bottom))] flex flex-col"
            :class="kind === 'pdf' && url ? 'overflow-hidden' : 'overflow-y-auto'">
            <!-- PDF: visor nativo -->
            <iframe v-if="kind === 'pdf' && url" :src="url" :title="`Vista previa de ${file.name}`"
              class="w-full flex-1 min-h-0 rounded-xl border border-slate-200 dark:border-slate-700 bg-white shadow-sm"></iframe>

            <!-- DOCX: render fiel -->
            <template v-else-if="kind === 'word' && !file.name.toLowerCase().endsWith('.doc')">
              <div v-if="docxLoading" class="flex flex-col items-center justify-center py-16 gap-3">
                <Loader2 class="w-8 h-8 animate-spin text-teal-500" />
                <p class="text-sm font-bold text-slate-500 dark:text-slate-400">Mostrando documento...</p>
              </div>
              <div v-else-if="docxError" class="flex flex-col items-center justify-center py-16 gap-3 text-center px-6">
                <FileWarning class="w-12 h-12 text-slate-300 dark:text-slate-600" />
                <p class="text-sm font-bold text-slate-600 dark:text-slate-300">{{ docxError }}</p>
              </div>
              <!-- Hoja tipo Word -->
              <div v-else-if="docxHtml" class="docx-sheet mx-auto max-w-3xl bg-white text-slate-900 rounded-lg shadow-lg px-6 py-8 sm:px-12 sm:py-10" v-html="docxHtml"></div>
            </template>

            <!-- DOC antiguo: sin vista previa -->
            <div v-else class="flex flex-col items-center justify-center py-16 gap-3 text-center px-6">
              <AlertTriangle class="w-12 h-12 text-slate-300 dark:text-slate-600" />
              <p class="text-sm font-bold text-slate-600 dark:text-slate-300">Vista previa no disponible para .doc</p>
              <p class="text-xs text-slate-500 dark:text-slate-400 max-w-sm">Convierta el archivo a .docx o PDF para verlo aquí. El texto extraído sigue disponible en el gestor.</p>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.docx-sheet {
  font-family: 'Calibri', 'Carlito', 'Segoe UI', Arial, sans-serif;
  font-size: 15px;
  line-height: 1.6;
  word-wrap: break-word;
}
.docx-sheet :deep(p) { margin: 0 0 0.6em; text-align: left; }
@media (min-width: 640px) {
  .docx-sheet :deep(p) { text-align: justify; }
}
.docx-sheet :deep(h1),
.docx-sheet :deep(h2),
.docx-sheet :deep(h3),
.docx-sheet :deep(h4) { font-weight: 800; line-height: 1.3; margin: 1em 0 0.5em; text-align: left; }
.docx-sheet :deep(h1) { font-size: 1.6em; }
.docx-sheet :deep(h2) { font-size: 1.35em; }
.docx-sheet :deep(h3) { font-size: 1.15em; }
.docx-sheet :deep(ul),
.docx-sheet :deep(ol) { margin: 0 0 0.6em 1.5em; padding: 0; }
.docx-sheet :deep(li) { margin-bottom: 0.25em; }
.docx-sheet :deep(table) { border-collapse: collapse; margin: 0.8em 0; width: 100%; font-size: 0.92em; }
.docx-sheet :deep(td),
.docx-sheet :deep(th) { border: 1px solid #cbd5e1; padding: 6px 10px; text-align: left; overflow-wrap: break-word; }
.docx-sheet :deep(th) { background: #f1f5f9; font-weight: 700; }
.docx-sheet :deep(img) { max-width: 100%; height: auto; border-radius: 6px; margin: 0.5em 0; }
.docx-sheet :deep(a) { color: #0d9488; text-decoration: underline; }
.docx-sheet :deep(strong) { font-weight: 700; }
</style>
