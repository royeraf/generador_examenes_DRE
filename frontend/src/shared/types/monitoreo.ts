export interface SesionAcceso {
  id: number
  exito: boolean
  motivo: string | null
  tipo_usuario: string | null
  usuario_id: number | null
  identificador: string | null
  nombres: string | null
  apellidos: string | null
  rol_codigo: string | null
  institucion_educativa_id: number | null
  institucion_nombre: string | null
  ugel_id: number | null
  ugel_nombre: string | null
  ip: string | null
  dispositivo: string | null
  sistema_operativo: string | null
  navegador: string | null
  es_movil: boolean
  login_at: string | null
  last_activity: string | null
  logout_at: string | null
  is_active: boolean
  en_linea: boolean
  duracion_minutos: number | null
}

export interface ConteoItem {
  clave: string
  total: number
}

export interface PuntoSerie {
  periodo: string
  total: number
  exitos: number
  fallidos: number
}

export interface ResumenMonitoreo {
  sesiones_activas: number
  estudiantes_activos: number
  staff_activos: number
  logins_hoy: number
  fallidos_hoy: number
  sesiones_hoy: number
  activos_por_rol: ConteoItem[]
  activos_por_ugel: ConteoItem[]
  top_instituciones: ConteoItem[]
  ultima_actualizacion: string
}

export interface EstadisticasMonitoreo {
  accesos_por_hora: PuntoSerie[]
  accesos_por_dia: PuntoSerie[]
  dispositivos: ConteoItem[]
  sistemas_operativos: ConteoItem[]
  navegadores: ConteoItem[]
  top_instituciones: ConteoItem[]
  ultima_actualizacion: string
}

export interface SesionesFiltros {
  page?: number
  size?: number
  q?: string
  rol?: string
  ie_id?: number
  ugel_id?: number
  fecha_desde?: string
  fecha_hasta?: string
  solo_fallidos?: boolean
}
