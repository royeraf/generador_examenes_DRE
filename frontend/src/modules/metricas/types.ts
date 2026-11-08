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

export interface PromedioArea {
  evaluados: number
  puntaje_promedio: number | null
  nota_promedio: number | null
  nivel_cneb: string | null
}

export interface DominioDesempeno {
  desempeno_codigo: string
  desempeno_descripcion: string | null
  total_preguntas: number
  correctas: number
  porcentaje: number
  nivel_cneb: string | null
}

export interface AcademicoData {
  rol: string
  total_evaluados: number
  promedios: {
    general: PromedioArea
    comunicacion: PromedioArea
    matematica: PromedioArea
  }
  distribucion_niveles: {
    pre_inicio: number
    inicio: number
    proceso: number
    satisfactorio: number
    total: number
  }
  dominio_desempenos: {
    comunicacion: DominioDesempeno[]
    matematica: DominioDesempeno[]
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
