import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import type { Usuario, RolCodigo } from '../shared/types'
import { authService } from '../shared/services/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<Usuario | null>(null)
  const token = ref<string | null>(localStorage.getItem('token'))

  const isAuthenticated = computed(() => !!token.value)

  // Computed por rol
  const userRole = computed((): RolCodigo | null => user.value?.rol_codigo ?? null)

  const isEspecialistaComunicacion = computed(() =>
    userRole.value === 'especialista_dre_comunicacion'
  )
  const isEspecialistaMatematica = computed(() =>
    userRole.value === 'especialista_dre_matematica'
  )
  const isEspecialista = computed(() =>
    isEspecialistaComunicacion.value || isEspecialistaMatematica.value
  )
  const isResponsableUGEL = computed(() => userRole.value === 'responsable_ugel')
  const isDirector = computed(() => userRole.value === 'director')
  const isAuxiliar = computed(() => userRole.value === 'auxiliar')
  const isDocente = computed(() => userRole.value === 'docente')
  const isEstudiante = computed(() => userRole.value === 'estudiante')

  // Alias de compatibilidad con código anterior
  const isAdmin = computed(() => isEspecialista.value)

  // Puede generar exámenes
  const canCreateExams = computed(() =>
    ['docente', 'auxiliar', 'director', 'especialista_dre_comunicacion', 'especialista_dre_matematica'].includes(userRole.value ?? '')
  )

  // Módulos efectivos (permisos_modulos si está seteado, sino defaults del rol)
  const ROLE_MODULOS_DEFAULT: Record<string, string[]> = {
    especialista_dre_comunicacion: ['lectosistem', 'matsistem', 'asignaciones', 'codigos_clase', 'metricas', 'admin_desempenos', 'admin_ugeles', 'admin_instituciones', 'admin_usuarios'],
    especialista_dre_matematica:   ['lectosistem', 'matsistem', 'asignaciones', 'codigos_clase', 'metricas', 'admin_desempenos', 'admin_ugeles', 'admin_instituciones', 'admin_usuarios'],
    responsable_ugel:              ['metricas', 'admin_instituciones', 'admin_usuarios'],
    director:                      ['lectosistem', 'matsistem', 'asignaciones', 'codigos_clase', 'metricas', 'admin_usuarios'],
    auxiliar:                      ['lectosistem', 'matsistem', 'asignaciones', 'codigos_clase', 'metricas'],
    docente:                       ['lectosistem', 'matsistem', 'asignaciones', 'codigos_clase', 'metricas'],
    estudiante:                    [],
  }

  const modulosEfectivos = computed((): string[] => {
    if (!user.value) return []
    // permisos_modulos null/undefined/vacío → usar defaults del rol
    if (user.value.permisos_modulos != null && user.value.permisos_modulos.length > 0) return user.value.permisos_modulos
    return ROLE_MODULOS_DEFAULT[userRole.value ?? ''] ?? []
  })

  const canAccessLectosistem = computed(() => modulosEfectivos.value.includes('lectosistem'))
  const canAccessMatsistem = computed(() => modulosEfectivos.value.includes('matsistem'))
  const canAccessAsignaciones = computed(() => modulosEfectivos.value.includes('asignaciones'))
  const canAccessCodigosClase = computed(() => modulosEfectivos.value.includes('codigos_clase'))
  const canAccessMetricas = computed(() => modulosEfectivos.value.includes('metricas'))
  const canAccessAdminDesempenos = computed(() => modulosEfectivos.value.includes('admin_desempenos'))
  const canAccessAdminUgeles = computed(() => modulosEfectivos.value.includes('admin_ugeles'))
  const canAccessAdminInstituciones = computed(() => modulosEfectivos.value.includes('admin_instituciones'))
  const canAccessAdminUsuarios = computed(() => modulosEfectivos.value.includes('admin_usuarios'))

  const displayName = computed(() => {
    if (!user.value) return ''
    return [user.value.nombres, user.value.apellidos].filter(Boolean).join(' ')
      || user.value.dni
      || user.value.codigo_estudiante
      || ''
  })

  // Ruta de inicio según rol
  const homeRoute = computed(() => {
    switch (userRole.value) {
      case 'estudiante': return '/estudiante'
      case 'responsable_ugel': return '/mi-ugel'
      default: return '/'
    }
  })

  async function login(identifier: string, password: string) {
    const data = await authService.login(identifier, password)
    token.value = data.access_token
    await fetchMe()
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
  }

  async function fetchMe() {
    user.value = await authService.getMe()
  }

  async function init() {
    if (token.value) {
      try {
        await fetchMe()
      } catch {
        logout()
      }
    }
  }

  return {
    user, token,
    isAuthenticated, userRole,
    isEspecialista, isEspecialistaComunicacion, isEspecialistaMatematica,
    isResponsableUGEL, isDirector, isAuxiliar, isDocente, isEstudiante,
    isAdmin, canCreateExams,
    modulosEfectivos,
    canAccessLectosistem, canAccessMatsistem, canAccessAsignaciones,
    canAccessCodigosClase, canAccessMetricas,
    canAccessAdminDesempenos,
    canAccessAdminUgeles, canAccessAdminInstituciones, canAccessAdminUsuarios,
    displayName, homeRoute,
    login, logout, fetchMe, init,
  }
})
