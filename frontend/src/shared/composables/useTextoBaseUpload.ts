import { computed, ref, shallowRef } from 'vue';
import type { FilesMetadata } from '../types';
import desempenosService from '../services/api';
import { validateFiles, parseUploadError, formatPalabras, MAX_UPLOAD_FILES } from '../utils/uploadFeedback';

/**
 * Estado y acciones para subir/gestionar el "texto base" (PDF/Word) usado por
 * el Generador de exámenes. El backend concatena el texto de todos los
 * archivos enviados en una sola llamada, así que agregar o quitar un archivo
 * implica reenviar el conjunto completo.
 */
export function useTextoBaseUpload() {
  const selectedFiles = ref<File[]>([]);
  const filesMetadata = ref<FilesMetadata | null>(null);
  const uploadingFile = shallowRef(false);
  const uploadError = shallowRef<string | null>(null);
  const textoBase = shallowRef('');

  const hasContent = computed(() =>
    selectedFiles.value.length > 0 || textoBase.value.trim() !== '');

  const resumen = computed(() => {
    if (uploadingFile.value) return { tone: 'uploading' as const, label: 'Procesando archivo...' };
    if (uploadError.value) return { tone: 'error' as const, label: uploadError.value };
    const archivos = filesMetadata.value?.archivos ?? [];
    if (archivos.length === 1) {
      return { tone: 'ready' as const, label: `${archivos[0]!.filename} · ${formatPalabras(archivos[0]!.palabras)}` };
    }
    if (archivos.length > 1) {
      return {
        tone: 'ready' as const,
        label: `${archivos.length} archivos · ${formatPalabras(filesMetadata.value?.total_palabras ?? 0)}`,
      };
    }
    if (textoBase.value.trim() !== '') return { tone: 'ready' as const, label: 'Texto escrito manualmente' };
    return { tone: 'empty' as const, label: 'Sin contenido' };
  });

  async function upload(files: File[]) {
    if (files.length === 0) {
      selectedFiles.value = [];
      filesMetadata.value = null;
      textoBase.value = '';
      return;
    }
    const validationError = validateFiles(files);
    if (validationError) {
      uploadError.value = validationError;
      return;
    }
    selectedFiles.value = files;
    uploadingFile.value = true;
    uploadError.value = null;
    try {
      const result = await desempenosService.uploadTextoBase(files);
      textoBase.value = result.texto;
      filesMetadata.value = {
        archivos: result.archivos,
        total_palabras: result.total_palabras,
        total_caracteres: result.total_caracteres,
        advertencias: result.advertencias,
      };
    } catch (e: unknown) {
      uploadError.value = parseUploadError(e);
      selectedFiles.value = [];
      filesMetadata.value = null;
      textoBase.value = '';
    } finally {
      uploadingFile.value = false;
    }
  }

  /** Agrega archivos nuevos a los ya seleccionados (respetando el máximo) y re-sube el conjunto. */
  async function addFiles(files: File[]) {
    const combined = [...selectedFiles.value, ...files].slice(0, MAX_UPLOAD_FILES);
    await upload(combined);
  }

  /** Quita un archivo por índice y re-sube los restantes. */
  async function removeFileAt(index: number) {
    const remaining = selectedFiles.value.filter((_, i) => i !== index);
    await upload(remaining);
  }

  function clear() {
    selectedFiles.value = [];
    filesMetadata.value = null;
    textoBase.value = '';
    uploadError.value = null;
  }

  return {
    selectedFiles,
    filesMetadata,
    uploadingFile,
    uploadError,
    textoBase,
    hasContent,
    resumen,
    addFiles,
    removeFileAt,
    clear,
  };
}
