// Escala de calificación CNEB (AD / A / B / C) — fuente compartida del frontend.
// Referencia: "Tabla Comparativa Referencial de Calificaciones" del MINEDU.

export type NivelCneb = 'AD' | 'A' | 'B' | 'C'

export interface EscalaCnebItem {
  codigo: NivelCneb
  nombre: string
  significado: string
  min: number
  max: number
}

export const ESCALA_CNEB: EscalaCnebItem[] = [
  {
    codigo: 'AD',
    nombre: 'Logro Destacado',
    significado: 'El estudiante demuestra un aprendizaje que supera las expectativas y los estándares previstos para el periodo.',
    min: 18,
    max: 20,
  },
  {
    codigo: 'A',
    nombre: 'Logro Esperado',
    significado: 'El estudiante demuestra el manejo adecuado de las tareas y cumple satisfactoriamente con las competencias esperadas.',
    min: 15,
    max: 17,
  },
  {
    codigo: 'B',
    nombre: 'En Proceso',
    significado: 'El estudiante se encuentra próximo al nivel esperado, pero requiere acompañamiento o mayor tiempo para lograrlo.',
    min: 11,
    max: 14,
  },
  {
    codigo: 'C',
    nombre: 'En Inicio',
    significado: 'El estudiante muestra un progreso mínimo, evidencia dificultades significativas y necesita una intervención docente directa.',
    min: 0,
    max: 10,
  },
]

export const NIVEL_CNEB_LABELS: Record<NivelCneb, string> = {
  AD: 'Logro Destacado',
  A: 'Logro Esperado',
  B: 'En Proceso',
  C: 'En Inicio',
}

// Colores oficiales MINEDU ("semáforo") para la escala CNEB:
// AD = verde, A = celeste, B = amarillo, C = rojo.
export const NIVEL_CNEB_HEX: Record<NivelCneb, string> = {
  AD: '#00A651',
  A: '#00AEEF',
  B: '#FDB913',
  C: '#ED1C24',
}

export const NIVEL_CNEB_COLORS: Record<NivelCneb, string> = {
  AD: 'text-green-600 bg-green-50 dark:bg-green-500/10 dark:text-green-400 border-green-100 dark:border-green-500/20',
  A: 'text-sky-600 bg-sky-50 dark:bg-sky-500/10 dark:text-sky-400 border-sky-100 dark:border-sky-500/20',
  B: 'text-amber-600 bg-amber-50 dark:bg-amber-500/10 dark:text-amber-400 border-amber-100 dark:border-amber-500/20',
  C: 'text-red-600 bg-red-50 dark:bg-red-500/10 dark:text-red-400 border-red-100 dark:border-red-500/20',
}

export function esNivelCneb(valor: unknown): valor is NivelCneb {
  return valor === 'AD' || valor === 'A' || valor === 'B' || valor === 'C'
}

export function nivelCnebClass(nivel?: string | null): string {
  return nivel && esNivelCneb(nivel)
    ? NIVEL_CNEB_COLORS[nivel]
    : 'text-slate-500 bg-slate-100 dark:bg-slate-500/10 border-transparent'
}
