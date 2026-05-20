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

  // Fallback local — solo se usa si el backend no devuelve modulos_efectivos.
  // Debe mantenerse en sync con backend/app/models/enums.py → ROLE_MODULOS_DEFAULT.
  const ROLE_MODULOS_DEFAULT_FALLBACK: Record<string, string[]> = {
    especialista_dre_comunicacion: ['lectosistem', 'matsistem', 'asignaciones', 'codigos_clase', 'metricas', 'admin_desempenos_comunicacion', 'admin_ugeles', 'admin_instituciones', 'admin_usuarios'],
    especialista_dre_matematica:   ['lectosistem', 'matsistem', 'asignaciones', 'codigos_clase', 'metricas', 'admin_desempenos_matematica',   'admin_ugeles', 'admin_instituciones', 'admin_usuarios'],
    responsable_ugel:              ['metricas', 'admin_instituciones', 'admin_usuarios'],
    director:                      ['lectosistem', 'matsistem', 'asignaciones', 'codigos_clase', 'metricas', 'admin_usuarios'],
    auxiliar:                      ['lectosistem', 'matsistem', 'asignaciones', 'codigos_clase', 'metricas'],
    docente:                       ['lectosistem', 'matsistem', 'asignaciones', 'codigos_clase', 'metricas'],
    estudiante:                    [],
  }

  const modulosEfectivos = computed((): string[] => {
    if (!user.value) return []
    // El backend calcula modulos_efectivos (permisos_modulos > rol.modulos_default > enum defaults).
    // Usarlo directamente evita duplicar la lógica de defaults en el frontend.
    if (user.value.modulos_efectivos?.length) return user.value.modulos_efectivos
    // Fallback local solo si el backend no lo devuelve por alguna razón
    return ROLE_MODULOS_DEFAULT_FALLBACK[userRole.value ?? ''] ?? []
  })

  const canAccessLectosistem = computed(() => modulosEfectivos.value.includes('lectosistem'))
  const canAccessMatsistem = computed(() => modulosEfectivos.value.includes('matsistem'))
  const canAccessAsignaciones = computed(() => modulosEfectivos.value.includes('asignaciones'))
  const canAccessCodigosClase = computed(() => modulosEfectivos.value.includes('codigos_clase'))
  const canAccessMetricas = computed(() => modulosEfectivos.value.includes('metricas'))
  // Gestión Curricular: cualquiera de los tres módulos habilita la ruta /admin
  const canAccessAdminDesempenos = computed(() => modulosEfectivos.value.includes('admin_desempenos'))
  const canAccessAdminDesempenosComunicacion = computed(() =>
    modulosEfectivos.value.includes('admin_desempenos') ||
    modulosEfectivos.value.includes('admin_desempenos_comunicacion')
  )
  const canAccessAdminDesempenosMatematica = computed(() =>
    modulosEfectivos.value.includes('admin_desempenos') ||
    modulosEfectivos.value.includes('admin_desempenos_matematica')
  )
  const canAccessGestionCurricular = computed(() =>
    canAccessAdminDesempenos.value ||
    canAccessAdminDesempenosComunicacion.value ||
    canAccessAdminDesempenosMatematica.value
  )
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
    document.cookie = '_logged_in_=1; path=/; SameSite=Lax'
    // Retry fetchMe hasta 2 veces para tolerar caché transitorio de nginx
    let lastError: unknown
    for (let i = 0; i < 3; i++) {
      try {
        await fetchMe()
        return
      } catch (e) {
        lastError = e
        if (i < 2) await new Promise(r => setTimeout(r, 400))
      }
    }
    throw lastError
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
    document.cookie = '_logged_in_=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/'
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
    canAccessAdminDesempenosComunicacion, canAccessAdminDesempenosMatematica,
    canAccessGestionCurricular,
    canAccessAdminUgeles, canAccessAdminInstituciones, canAccessAdminUsuarios,
    displayName, homeRoute,
    login, logout, fetchMe, init,
  }
})
