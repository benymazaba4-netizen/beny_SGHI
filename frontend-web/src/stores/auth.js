import { defineStore } from 'pinia'
import apiClient from '../api/client'
import { getRolePath } from '../config/roles'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: JSON.parse(localStorage.getItem('user') || 'null'),
    token: localStorage.getItem('token') || null,
    isAuthenticated: !!localStorage.getItem('token'),
    mfaSession: sessionStorage.getItem('mfa_session') || null,
    otpSession: sessionStorage.getItem('otp_session') || null,
    otpEmailHint: sessionStorage.getItem('otp_email_hint') || null,
    otpUsername: sessionStorage.getItem('otp_username') || null,
  }),

  actions: {
    _persistAuth(token, refreshToken, user) {
      this.token = token
      this.user = user
      this.isAuthenticated = true
      this.mfaSession = null
      this.otpSession = null
      this.otpEmailHint = null
      this.otpUsername = null
      sessionStorage.removeItem('mfa_session')
      sessionStorage.removeItem('otp_session')
      sessionStorage.removeItem('otp_email_hint')
      sessionStorage.removeItem('otp_username')
      localStorage.setItem('token', token)
      if (refreshToken) localStorage.setItem('refresh_token', refreshToken)
      localStorage.setItem('user', JSON.stringify(user))
    },

    async login(username, password) {
      try {
        const response = await apiClient.post('/auth/login', { username, password })
        const data = response.data

        if (data.mfa_required) {
          this.mfaSession = data.mfa_session
          sessionStorage.setItem('mfa_session', data.mfa_session || '')
          return { success: true, mfaRequired: true, username: data.user?.username }
        }

        if (data.otp_required) {
          this.otpSession = data.otp_session
          this.otpEmailHint = data.otp_email_hint
          this.otpUsername = username
          sessionStorage.setItem('otp_session', data.otp_session || '')
          sessionStorage.setItem('otp_email_hint', data.otp_email_hint || '')
          sessionStorage.setItem('otp_username', username)
          return {
            success: true,
            otpRequired: true,
            emailHint: data.otp_email_hint,
            username: data.user?.username,
          }
        }

        this._persistAuth(data.token, data.refresh_token, data.user)
        return { success: true, user: data.user }
      } catch (error) {
        let message = 'Erreur de connexion'
        if (error.response) {
          message = error.response.data?.error || error.response.data?.detail || `Erreur ${error.response.status}`
        } else if (error.request) {
          message = 'Impossible de contacter le serveur. Vérifiez que Django tourne sur http://127.0.0.1:8000'
        }
        return { success: false, error: message }
      }
    },

    async loginMfa(totpToken) {
      try {
        const response = await apiClient.post('/auth/login/mfa', {
          mfa_session: this.mfaSession || sessionStorage.getItem('mfa_session'),
          totp_token: totpToken,
        })
        const data = response.data
        this._persistAuth(data.token, data.refresh_token, data.user)
        return { success: true, user: data.user }
      } catch (error) {
        return { success: false, error: error.response?.data?.error || 'Code MFA invalide' }
      }
    },

    async loginOtp(otpCode, username = null) {
      const pendingUser = username || this.otpUsername || sessionStorage.getItem('otp_username')
      if (!pendingUser) {
        return { success: false, error: 'Session OTP expirée — reconnectez-vous.' }
      }
      const code = String(otpCode || '').trim().replace(/\s/g, '')
      if (code.length !== 6) {
        return { success: false, error: 'Le code OTP doit contenir 6 chiffres.' }
      }
      try {
        const response = await apiClient.post('/auth/verify-otp', {
          username: pendingUser,
          otp_code: code,
        })
        const data = response.data
        this._persistAuth(data.token, data.refresh_token, data.user)
        return { success: true, user: data.user }
      } catch (error) {
        return { success: false, error: error.response?.data?.error || 'Code OTP invalide ou expiré' }
      }
    },

    async resendOtp() {
      const session = this.otpSession || sessionStorage.getItem('otp_session')
      if (!session) {
        return { success: false, error: 'Session OTP expirée — reconnectez-vous.' }
      }
      try {
        const response = await apiClient.post('/auth/login/otp/resend', { otp_session: session })
        const data = response.data
        if (data.otp_session) {
          this.otpSession = data.otp_session
          sessionStorage.setItem('otp_session', data.otp_session)
        }
        if (data.otp_email_hint) {
          this.otpEmailHint = data.otp_email_hint
          sessionStorage.setItem('otp_email_hint', data.otp_email_hint)
        }
        return { success: true, emailHint: data.otp_email_hint }
      } catch (error) {
        return { success: false, error: error.response?.data?.error || 'Impossible de renvoyer le code' }
      }
    },

    async logout() {
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken) {
        try {
          await apiClient.post('/auth/logout', { refresh_token: refreshToken })
        } catch {
          // ignore
        }
      }
      this.token = null
      this.user = null
      this.isAuthenticated = false
      this.mfaSession = null
      this.otpSession = null
      this.otpEmailHint = null
      this.otpUsername = null
      sessionStorage.removeItem('mfa_session')
      sessionStorage.removeItem('otp_session')
      sessionStorage.removeItem('otp_email_hint')
      sessionStorage.removeItem('otp_username')
      localStorage.removeItem('token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user')
    },

    dashboardPath() {
      return getRolePath(this.user?.role)
    },
  },

  getters: {
    role: (state) => state.user?.role,
    isMedecin: (state) => state.user?.role === 'MEDECIN',
    isPatient: (state) => state.user?.role === 'PATIENT',
    isAdmin: (state) => state.user?.role === 'ADMIN',
    isInfirmier: (state) => state.user?.role === 'INFIRMIER',
    isBiologiste: (state) => state.user?.role === 'BIOLOGISTE',
    isPharmacien: (state) => state.user?.role === 'PHARMACIEN',
    isComptable: (state) => state.user?.role === 'COMPTABLE',
    isSecretaire: (state) => state.user?.role === 'SECRETAIRE',
    userName: (state) => state.user ? `${state.user.first_name} ${state.user.last_name}`.trim() || state.user.username : '',
    patientId: (state) => state.user?.patient_id,
  },
})
