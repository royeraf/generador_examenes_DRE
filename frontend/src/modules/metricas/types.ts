export interface AvanceItem {
  id: number
  nombre: string
  ugel?: string | null
  provincia?: string | null
  asignaciones: number
  completados: number
  avance_pct: number
}

export interface EstudianteItem {
  id: number
  nombre: string
  ugel?: string | null
  provincia?: string | null
  estudiantes: number
}

export interface DistribucionData {
  rol: string
  avance_por_ugel: AvanceItem[]
  avance_por_institucion: AvanceItem[]
  estudiantes_por_institucion: EstudianteItem[]
  totales: {
    asignaciones: number
    completados: number
    estudiantes: number
    instituciones: number
  }
}

export type MetricaMapa = 'avance' | 'estudiantes'

export interface ProvinciaStats {
  nombre: string
  asignaciones: number
  completados: number
  estudiantes: number
  avancePct: number
  enAlcance: boolean
}
