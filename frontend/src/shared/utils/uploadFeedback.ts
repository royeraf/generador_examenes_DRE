// Utilidades compartidas para la subida de archivos de texto/problema base (PDF/Word)
// usadas por LectoSistem, MatSistem y Generador.
// Reflejan las validaciones reales del backend (backend/app/services/file_service.py
// y backend/app/routes/lectosistem.py) para dar feedback antes de llamar al API.

export const ALLOWED_UPLOAD_EXT = ['pdf', 'docx', 'doc'];
export const MAX_UPLOAD_FILES = 5;
export const MAX_UPLOAD_MB = 10;

/**
 * Valida extensión, cantidad y tamaño de los archivos antes de subirlos.
 * Devuelve el mensaje de error a mostrar, o null si todo está bien.
 */
export function validateFiles(files: File[]): string | null {
  if (files.length === 0) return null;

  if (files.length > MAX_UPLOAD_FILES) {
    return `Se permiten máximo ${MAX_UPLOAD_FILES} archivos por vez. Seleccionaste ${files.length}.`;
  }

  for (const file of files) {
    const extension = file.name.split('.').pop()?.toLowerCase();
    if (!ALLOWED_UPLOAD_EXT.includes(extension || '')) {
      return `Archivo "${file.name}" no soportado. Solo PDF o Word.`;
    }
    if (file.size > MAX_UPLOAD_MB * 1024 * 1024) {
      const sizeMb = (file.size / (1024 * 1024)).toFixed(1);
      return `Archivo "${file.name}" pesa ${sizeMb} MB. El tamaño máximo permitido es ${MAX_UPLOAD_MB} MB.`;
    }
  }

  return null;
}

/**
 * Normaliza el error de una subida fallida. El backend responde con `detail`
 * como string (errores de validación de un solo archivo) o como
 * `{ mensaje, errores: [{ archivo, error }] }` cuando fallan todos los archivos.
 */
export function parseUploadError(e: unknown): string {
  const err = e as { response?: { data?: { detail?: unknown } }; code?: string; message?: string };
  const detail = err?.response?.data?.detail;

  if (typeof detail === 'string') return detail;

  if (detail && typeof detail === 'object') {
    const d = detail as { mensaje?: string; errores?: { archivo: string; error: string }[] };
    if (Array.isArray(d.errores) && d.errores.length > 0) {
      const lista = d.errores.map((er) => `${er.archivo}: ${er.error}`).join(' | ');
      return d.mensaje ? `${d.mensaje} (${lista})` : lista;
    }
    if (d.mensaje) return d.mensaje;
  }

  if (err?.code === 'ECONNABORTED') return 'La subida tardó demasiado. Intenta con un archivo más liviano.';

  return 'Error al procesar los archivos';
}

export function formatPalabras(n: number): string {
  return `${n.toLocaleString('es-PE')} ${n === 1 ? 'palabra' : 'palabras'}`;
}

/** Atributo `accept` para inputs de archivo, derivado de ALLOWED_UPLOAD_EXT. */
export const ACCEPT_UPLOAD = ALLOWED_UPLOAD_EXT.map((ext) => `.${ext}`).join(',');

export type FileKind = 'pdf' | 'word' | 'unknown';

export const FILE_KIND_LABEL: Record<FileKind, string> = {
  pdf: 'PDF',
  word: 'Word',
  unknown: 'Archivo',
};

/** Determina el tipo de archivo (para icono/etiqueta) a partir de su nombre o extensión. */
export function getFileKind(nameOrExt: string): FileKind {
  const raw = nameOrExt.includes('.') ? nameOrExt.split('.').pop() ?? '' : nameOrExt;
  const ext = raw.toLowerCase().trim();
  if (ext === 'pdf') return 'pdf';
  if (ext === 'doc' || ext === 'docx') return 'word';
  return 'unknown';
}

/** Formatea un tamaño en KB a KB o MB según corresponda. */
export function formatFileSize(kb?: number): string {
  if (!kb && kb !== 0) return '';
  if (kb < 1024) return `${Math.round(kb)} KB`;
  return `${(kb / 1024).toFixed(1)} MB`;
}

/** Cuenta palabras de un texto libre (para el textarea de texto base). */
export function countWords(text: string): number {
  const trimmed = text.trim();
  return trimmed === '' ? 0 : trimmed.split(/\s+/).length;
}
