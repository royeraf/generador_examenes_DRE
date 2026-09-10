import { shallowRef } from 'vue';

/**
 * Estado estándar para la vista previa de archivos subidos (PDF/Word).
 * La vista previa usa el `File` original en memoria (URL de objeto), por lo
 * que solo está disponible en la sesión actual: tras recargar, los `File` se
 * pierden (solo persiste la metadata) y el llamador debe ocultar el botón.
 */
export function useFilePreview() {
  const previewFile = shallowRef<File | null>(null);
  const previewUrl = shallowRef<string | null>(null);
  const isPreviewOpen = shallowRef(false);

  function openPreview(file: File) {
    closePreview();
    previewFile.value = file;
    previewUrl.value = URL.createObjectURL(file);
    isPreviewOpen.value = true;
  }

  function closePreview() {
    isPreviewOpen.value = false;
    if (previewUrl.value) URL.revokeObjectURL(previewUrl.value);
    previewUrl.value = null;
    previewFile.value = null;
  }

  return {
    previewFile,
    previewUrl,
    isPreviewOpen,
    openPreview,
    closePreview,
  };
}
