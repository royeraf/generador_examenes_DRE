/**
 * Utilidades centralizadas de fecha/hora para el sistema SIEVA.
 *
 * CONVENCIÓN:
 * - El docente programa exámenes en hora Perú (America/Lima, UTC-5).
 * - El frontend envía la fecha/hora tal cual la escribió el usuario, en hora
 *   Perú y sin offset ("2026-05-05T08:00:00").
 * - El backend almacena todo en hora Perú (naive), igual que hace el motor de
 *   BD con CURRENT_TIMESTAMP.
 * - Al mostrar al usuario, se serializa con offset -05:00 y se formatea con
 *   timeZone 'America/Lima', así el resultado no depende del reloj del equipo.
 */

const TIMEZONE_PERU = 'America/Lima'
const LOCALE_PERU  = 'es-PE'

// ─── Construcción ───────────────────────────────────────────────────────────

/**
 * Construye un datetime ISO-8601 en hora Perú a partir de una fecha
 * ("2026-05-05") y una hora ("08:00") ingresadas por el usuario.
 *
 * No se usa toISOString(): eso convertiría a UTC según la zona del navegador
 * y dejaría la columna de la BD corridida. La convención es guardar hora Perú.
 */
export function construirFechaISO(fecha: string, hora: string): string | null {
  if (!fecha || !hora) return null
  return `${fecha}T${hora}:00`
}

// ─── Extracción (para rellenar inputs date/time al editar) ──────────────────

/**
 * Dado un ISO-8601 con offset ("-05:00"), extrae la fecha y hora en hora Perú
 * para rellenar inputs type="date" y type="time".
 *
 * Se formatea con timeZone explícita para que el resultado sea el mismo sin
 * importar la zona horaria configurada en el equipo.
 */
export function extraerFechaHora(iso: string | null): { date: string; time: string } {
  if (!iso) return { date: '', time: '' }
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return { date: '', time: '' }
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: TIMEZONE_PERU,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hourCycle: 'h23',
  }).formatToParts(d)
  const get = (type: string) => parts.find(p => p.type === type)?.value ?? ''
  return {
    date: `${get('year')}-${get('month')}-${get('day')}`,
    time: `${get('hour')}:${get('minute')}`,
  }
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
