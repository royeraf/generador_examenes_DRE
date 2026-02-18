import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const LoginView = () => import('../views/LoginView.vue')
const HomeView = () => import('../views/HomeView.vue')
const LectoSistemView = () => import('../views/LectoSistemView.vue')
const MatSistemView = () => import('../views/MatSistemView.vue')
const AdminView = () => import('../views/AdminView.vue')
const AdminMatView = () => import('../views/AdminMatView.vue')
const AdminUsuariosView = () => import('../views/AdminUsuariosView.vue')

const routes = [
  {
    path: '/login',
    component: LoginView,
    meta: { requiresGuest: true },
  },
  {
    path: '/',
    component: HomeView,
    meta: { requiresAuth: true },
  },
  {
    path: '/lectosistem',
    component: LectoSistemView,
    meta: { requiresAuth: true },
  },
  {
    path: '/matsistem',
    component: MatSistemView,
    meta: { requiresAuth: true },
  },
  {
    path: '/admin',
    component: AdminView,
    meta: { requiresAuth: true, requiresAdmin: true },
  },
  {
    path: '/admin/mat',
    component: AdminMatView,
    meta: { requiresAuth: true, requiresAdmin: true },
  },
  {
    path: '/admin/usuarios',
    component: AdminUsuariosView,
    meta: { requiresAuth: true, requiresAdmin: true },
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

  // If we have a token but no user yet, try to init
  if (auth.token && !auth.user) {
    await auth.init()
  }

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return '/login'
  }

  if (to.meta.requiresGuest && auth.isAuthenticated) {
    return '/'
  }

  if (to.meta.requiresAdmin && !auth.isAdmin) {
    return '/'
  }
})

export default router
