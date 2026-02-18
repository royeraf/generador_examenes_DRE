import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import type { Docente } from '../types'
import { authService } from '../services/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<Docente | null>(null)
  const token = ref<string | null>(localStorage.getItem('token'))

  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.is_superuser ?? false)
  const displayName = computed(() => {
    if (!user.value) return ''
    return [user.value.nombres, user.value.apellidos].filter(Boolean).join(' ') || user.value.dni
  })

  async function login(dni: string, password: string) {
    const data = await authService.login(dni, password)
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

  return { user, token, isAuthenticated, isAdmin, displayName, login, logout, fetchMe, init }
})
