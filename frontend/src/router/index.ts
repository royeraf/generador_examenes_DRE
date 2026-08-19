import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import type { RolCodigo } from '../shared/types'

// Vistas existentes
const LoginView = () => import('../modules/auth/LoginView.vue')
const HomeView = () => import('../modules/home/HomeView.vue')
const LectoSistemView = () => import('../modules/lectosistem/LectoSistemView.vue')
const MatSistemView = () => import('../modules/matsistem/MatSistemView.vue')
const AdminCurriculumView = () => import('../modules/admin/AdminCurriculumView.vue')
const AdminUsuariosView = () => import('../modules/admin/AdminUsuariosView.vue')
const MetricasView = () => import('../modules/metricas/MetricasView.vue')

// Asignaciones (docente)
const AsignacionesView = () => import('../modules/asignaciones/AsignacionesView.vue')

// Vistas nuevas - Organizacionales
const AdminUgelesView = () => import('../modules/admin/AdminUgelesView.vue')
const AdminInstitucionesView = () => import('../modules/admin/AdminInstitucionesView.vue')
const MiUgelView = () => import('../modules/admin/MiUgelView.vue')
const MiInstitucionView = () => import('../modules/admin/MiInstitucionView.vue')
const CodigosClaseView = () => import('../modules/codigos_clase/CodigosClaseView.vue')

// Vistas nuevas - Registro público
const RegistroEstudianteView = () => import('../modules/auth/RegistroEstudianteView.vue')

// Gestión de estudiantes por docente
const MisEstudiantesView = () => import('../modules/admin/MisEstudiantesView.vue')

// Vistas nuevas - Portal estudiantil
const EstudianteDashboardView = () => import('../modules/estudiante/EstudianteDashboardView.vue')
const EstudianteExamenesView = () => import('../modules/estudiante/EstudianteExamenesView.vue')
const EstudianteExamenView = () => import('../modules/estudiante/EstudianteExamenView.vue')
const EstudianteProgresoView = () => import('../modules/estudiante/EstudianteProgresoView.vue')

declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean
    requiresGuest?: boolean
    // Alias de compatibilidad
    requiresAdmin?: boolean
    // Nuevo sistema: lista de roles permitidos (OR - cualquiera de estos)
    requiredRoles?: RolCodigo[]
    // Módulo requerido (el usuario debe tener ESTE módulo)
    requiredModulo?: string
    // Módulos alternativos (el usuario debe tener AL MENOS UNO)
    requiredModuloAny?: string[]
  }
}

const DRE_ROLES: RolCodigo[] = ['especialista_dre_comunicacion', 'especialista_dre_matematica']
const DRE_UGEL_ROLES: RolCodigo[] = [...DRE_ROLES, 'responsable_ugel']
const GESTORES_ROLES: RolCodigo[] = [...DRE_UGEL_ROLES, 'director']
const EXAM_CREATORS: RolCodigo[] = [...GESTORES_ROLES, 'auxiliar', 'docente']

const routes: RouteRecordRaw[] = [
  // ── Públicas ───────────────────────────────────────────────────────────────
  {
    path: '/login',
    component: LoginView,
    meta: { requiresGuest: true },
  },
  {
    path: '/registro',
    component: RegistroEstudianteView,
    meta: {},  // Sin auth - pantalla de auto-registro
  },

  // ── Docentes / Módulos de examen ────────────────────────────────────────────
  {
    path: '/',
    component: HomeView,
    meta: { requiresAuth: true }, // El contenido se filtra por rol dentro del componente
  },
  {
    path: '/lectosistem',
    component: LectoSistemView,
    meta: { requiresAuth: true, requiredRoles: EXAM_CREATORS, requiredModulo: 'lectosistem' },
  },
  {
    path: '/matsistem',
    component: MatSistemView,
    meta: { requiresAuth: true, requiredRoles: EXAM_CREATORS, requiredModulo: 'matsistem' },
  },
  {
    path: '/codigos-clase',
    component: CodigosClaseView,
    meta: { requiresAuth: true, requiredRoles: [...GESTORES_ROLES, 'auxiliar', 'docente'], requiredModulo: 'codigos_clase' },
  },
  {
    path: '/mis-estudiantes',
    component: MisEstudiantesView,
    meta: { requiresAuth: true, requiredRoles: EXAM_CREATORS },
  },
  {
    path: '/asignaciones',
    component: AsignacionesView,
    meta: { requiresAuth: true, requiredRoles: EXAM_CREATORS, requiredModulo: 'asignaciones' },
  },

  // ── Admin DRE (Desempeños) ──────────────────────────────────────────────────
  {
    path: '/admin',
    component: AdminCurriculumView,
    meta: { requiresAuth: true, requiresAdmin: true, requiredRoles: DRE_ROLES, requiredModuloAny: ['admin_desempenos', 'admin_desempenos_comunicacion', 'admin_desempenos_matematica'] },
  },
  {
    path: '/admin/mat',
    redirect: '/admin',
  },
  {
    path: '/admin/usuarios',
    component: AdminUsuariosView,
    meta: { requiresAuth: true, requiredRoles: GESTORES_ROLES, requiredModulo: 'admin_usuarios' },
  },
  {
    path: '/admin/metricas',
    component: MetricasView,
    meta: { requiresAuth: true, requiredRoles: EXAM_CREATORS, requiredModulo: 'metricas' },
  },

  // ── Gestión organizacional ──────────────────────────────────────────────────
  {
    path: '/admin/ugeles',
    component: AdminUgelesView,
    meta: { requiresAuth: true, requiredRoles: DRE_ROLES, requiredModulo: 'admin_ugeles' },
  },
  {
    path: '/admin/instituciones',
    component: AdminInstitucionesView,
    meta: { requiresAuth: true, requiredRoles: DRE_UGEL_ROLES, requiredModulo: 'admin_instituciones' },
  },
  {
    path: '/mi-ugel',
    component: MiUgelView,
    meta: { requiresAuth: true, requiredRoles: ['responsable_ugel'] },
  },
  {
    path: '/mi-institucion',
    component: MiInstitucionView,
    meta: { requiresAuth: true, requiredRoles: ['director', 'auxiliar', ...DRE_UGEL_ROLES] },
  },

  // ── Portal estudiantil ──────────────────────────────────────────────────────
  {
    path: '/estudiante',
    component: EstudianteDashboardView,
    meta: { requiresAuth: true, requiredRoles: ['estudiante'] },
  },
  {
    path: '/estudiante/examenes',
    component: EstudianteExamenesView,
    meta: { requiresAuth: true, requiredRoles: ['estudiante'] },
  },
  {
    path: '/estudiante/examen/:id',
    component: EstudianteExamenView,
    meta: { requiresAuth: true, requiredRoles: ['estudiante'] },
  },
  {
    path: '/estudiante/progreso',
    component: EstudianteProgresoView,
    meta: { requiresAuth: true, requiredRoles: ['estudiante'] },
  },

  {
    path: '/:pathMatch(.*)*',
    redirect: '/',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()

  // Cargar usuario solo si hay token pero NO hay objeto de usuario (primera carga / refresh)
  if (auth.token && !auth.user) {
    await auth.init()
  }

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return '/login'
  }

  if (to.meta.requiresGuest && auth.isAuthenticated) {
    return auth.homeRoute
  }

  // El home general (HomeView) es para docentes/gestores; los estudiantes tienen su propio portal
  if (to.path === '/' && auth.userRole === 'estudiante') {
    return auth.homeRoute
  }

  // Verificar roles requeridos
  const requiredRoles = to.meta.requiredRoles
  if (requiredRoles && requiredRoles.length > 0) {
    const userRole = auth.userRole
    if (!userRole || !requiredRoles.includes(userRole)) {
      // Redirigir al home del rol si no tiene acceso a esta ruta
      if (to.path !== auth.homeRoute) {
        return auth.homeRoute
      }
    }
  }

  // Compatibilidad con requiresAdmin
  if (to.meta.requiresAdmin && !auth.isAdmin) {
    return auth.homeRoute
  }

  // Módulo único requerido
  if (to.meta.requiredModulo && auth.user) {
    if (!auth.modulosEfectivos.includes(to.meta.requiredModulo)) {
      return auth.homeRoute
    }
  }

  // Al menos uno de estos módulos es requerido
  if (to.meta.requiredModuloAny && auth.user) {
    const allowed = (to.meta.requiredModuloAny as string[])
    if (!allowed.some(m => auth.modulosEfectivos.includes(m))) {
      return auth.homeRoute
    }
  }
})

export default router
