import { ref, computed } from 'vue'
import apiClient from '@/api/client'

export const useAuth = () => {
  const user = ref(null)
  const token = ref(localStorage.getItem('token') || null)
  const refreshToken = ref(localStorage.getItem('refresh_token') || null)
  const isLoggedIn = computed(() => !!token.value)
  const loading = ref(false)
  const error = ref(null)

  const loadUserFromStorage = () => {
    const stored = localStorage.getItem('user')
    if (stored) {
      user.value = JSON.parse(stored)
    }
  }

  const login = async (username, password) => {
    loading.value = true
    error.value = null
    try {
      const response = await apiClient.post('/auth/login', {
        username,
        password,
      })
      const { token: newToken, refresh_token: newRefreshToken, user: userData } = response.data
      
      token.value = newToken
      refreshToken.value = newRefreshToken
      user.value = userData

      localStorage.setItem('token', newToken)
      localStorage.setItem('refresh_token', newRefreshToken)
      localStorage.setItem('user', JSON.stringify(userData))
      
      return { success: true, user: userData }
    } catch (err) {
      error.value = err.response?.data?.error || 'Erreur de connexion'
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  const register = async (payload) => {
    loading.value = true
    error.value = null
    try {
      const response = await apiClient.post('/auth/register', payload)
      const { token: newToken, refresh_token: newRefreshToken, user: userData } = response.data

      token.value = newToken
      refreshToken.value = newRefreshToken
      user.value = userData

      localStorage.setItem('token', newToken)
      localStorage.setItem('refresh_token', newRefreshToken)
      localStorage.setItem('user', JSON.stringify(userData))

      return { success: true, user: userData }
    } catch (err) {
      error.value = err.response?.data?.error || 'Erreur lors de l inscription'
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  const logout = async () => {
    loading.value = true
    try {
      if (refreshToken.value) {
        await apiClient.post('/auth/logout', {
          refresh_token: refreshToken.value,
        })
      }
    } catch (err) {
      console.error('Logout error:', err)
    } finally {
      token.value = null
      refreshToken.value = null
      user.value = null
      localStorage.removeItem('token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user')
      loading.value = false
    }
  }

  const setupMFA = async () => {
    try {
      const response = await apiClient.post('/mfa/mfa/setup')
      return response.data
    } catch (err) {
      error.value = err.response?.data?.error || 'Erreur MFA setup'
      throw err
    }
  }

  const verifyMFA = async (totpToken) => {
    try {
      const response = await apiClient.post('/mfa/mfa/verify', {
        totp_token: totpToken,
      })
      return response.data
    } catch (err) {
      error.value = err.response?.data?.error || 'Token TOTP invalide'
      throw err
    }
  }

  const getMFAStatus = async () => {
    try {
      const response = await apiClient.get('/mfa/mfa/status')
      return response.data
    } catch (err) {
      console.error('MFA status error:', err)
      return null
    }
  }

  loadUserFromStorage()

  return {
    user,
    token,
    refreshToken,
    isLoggedIn,
    loading,
    error,
    login,
    logout,
    setupMFA,
    verifyMFA,
    getMFAStatus,
  }
}
