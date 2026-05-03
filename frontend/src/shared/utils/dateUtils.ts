/**
 * Utilidades centralizadas de fecha/hora para el sistema SIEVA.
 *
 * CONVENCIÓN:
 * - El docente programa exámenes en hora Perú (America/Lima, UTC-5).
 * - El frontend convierte la hora local ingresada a UTC ISO-8601 antes de
 *   enviarla al backend.
 * - El backend almacena todo en UTC.
 * - Al mostrar al usuario, se formatea de vuelta a hora Perú.
 */

const TIMEZONE_PERU = 'America/Lima'
const LOCALE_PERU  = 'es-PE'

// ─── Construcción ───────────────────────────────────────────────────────────

/**
 * Construye un datetime ISO-8601 en UTC a partir de una fecha ("2026-05-05")
 * y una hora ("08:00") ingresadas por el usuario en hora Perú.
 *
 * Usa la zona horaria del navegador (que en Perú es America/Lima) para
 * determinar el offset correcto.
 */
export function construirFechaISO(fecha: string, hora: string): string | null {
  if (!fecha || !hora) return null
  // Construimos "2026-05-05T08:00:00" — el constructor de Date lo interpreta
  // como hora local del navegador.
  return new Date(`${fecha}T${hora}:00`).toISOString()
}

// ─── Extracción (para rellenar inputs date/time al editar) ──────────────────

/**
 * Dado un ISO-8601 UTC ("2026-05-05T13:00:00.000Z"), extrae la fecha y hora
 * en hora local del navegador (Perú) para rellenar inputs type="date" y
 * type="time".
 */
export function extraerFechaHora(iso: string | null): { date: string; time: string } {
  if (!iso) return { date: '', time: '' }
  const d = new Date(iso)
  const date = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
  const time = `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
  return { date, time }
}

// ─── Formateo para mostrar al usuario ───────────────────────────────────────

/**
 * Formato completo: "05 may. 2026, 08:00 a. m."
 * Usado en listados de asignaciones, historial de exámenes, resultados.
 */
export function formatFechaHora(iso: string | null): string {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleString(LOCALE_PERU, {
    timeZone: TIMEZONE_PERU,
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

/**
 * Solo fecha: "05 may. 2026"
 * Usado en perfiles, creación de usuarios, métricas.
 */
export function formatFecha(iso: string | null): string {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleDateString(LOCALE_PERU, {
    timeZone: TIMEZONE_PERU,
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}

/**
 * Solo fecha con mes largo: "05 de mayo de 2026"
 * Usado en el badge de perfil.
 */
export function formatFechaLarga(iso: string | null): string {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleDateString(LOCALE_PERU, {
    timeZone: TIMEZONE_PERU,
    day: '2-digit',
    month: 'long',
    year: 'numeric',
  })
}

/**
 * Fecha corta sin año: "05 may."
 * Usado en el portal de estudiantes para rangos "Desde: ... Hasta: ...".
 */
export function formatFechaCorta(iso: string | null): string {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleDateString(LOCALE_PERU, {
    timeZone: TIMEZONE_PERU,
    day: '2-digit',
    month: 'short',
  })
}

/**
 * Fecha corta con hora: "05 may. 08:00 a. m."
 * Usado en el portal de estudiantes para rangos horarios.
 */
export function formatFechaHoraCorta(iso: string | null): string {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleString(LOCALE_PERU, {
    timeZone: TIMEZONE_PERU,
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
}
