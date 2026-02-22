import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../api/client'

interface UserInfo {
  id: number
  username: string
  full_name: string
  role: string
  is_active: boolean
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<UserInfo | null>(null)
  const token = ref(localStorage.getItem('access_token') || '')

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const isDispatcher = computed(() => user.value?.role === 'dispatcher')

  async function login(username: string, password: string) {
    const res = await api.post('/auth/login', { username, password })
    token.value = res.data.access_token
    localStorage.setItem('access_token', res.data.access_token)
    localStorage.setItem('refresh_token', res.data.refresh_token)
    await fetchUser()
  }

  async function fetchUser() {
    try {
      const res = await api.get('/auth/me')
      user.value = res.data
    } catch {
      logout()
    }
  }

  function logout() {
    user.value = null
    token.value = ''
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  return { user, token, isLoggedIn, isAdmin, isDispatcher, login, fetchUser, logout }
})
