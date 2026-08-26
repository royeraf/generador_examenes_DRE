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
