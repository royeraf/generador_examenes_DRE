import { apiClient } from './api'
import type { Usuario } from '../types'

export interface Token {
  access_token: string
  token_type: string
}

export const authService = {
  async login(identifier: string, password: string): Promise<Token> {
    const formData = new FormData()
    // identifier puede ser DNI o código de estudiante (EST0001)
    formData.append('username', identifier)
    formData.append('password', password)

    const response = await apiClient.post<Token>('/auth/login', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })

    if (response.data.access_token) {
      localStorage.setItem('token', response.data.access_token)
    }
    return response.data
  },

  async getMe(): Promise<Usuario> {
    const response = await apiClient.get<Usuario>('/auth/me')
    return response.data
  },

  logout() {
    localStorage.removeItem('token');
  },

  async logoutRequest(): Promise<void> {
    // Captura el token antes de que el store lo elimine y avisa al backend
    const token = localStorage.getItem('token');
    try {
      await apiClient.post('/auth/logout', null, {
        headers: token ? { Authorization: `Bearer ${token}` } : undefined,
      });
    } catch {
      // El cierre de sesión en servidor es best-effort
    }
  },

  isAuthenticated(): boolean {
    return !!localStorage.getItem('token');
  },
}
