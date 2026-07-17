import axios from 'axios'

// En prod : .env.production ou variable VITE_API_URL sur Render (build time)
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api/v1'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
})

export { API_BASE_URL }

// Interceptor requête : injecter le token
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Interceptor réponse : gérer 401 avec refresh token
let isRefreshing = false
let failedQueue = []

const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(token)
    }
  })
  isRefreshing = false
  failedQueue = []
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then(token => {
          originalRequest.headers.Authorization = `Bearer ${token}`
          return apiClient(originalRequest)
        })
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        const refreshToken = localStorage.getItem('refresh_token')
        if (!refreshToken) {
          throw new Error('No refresh token')
        }

        const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
          refresh_token: refreshToken
        })

        const { token, refresh_token } = response.data
        localStorage.setItem('token', token)
        localStorage.setItem('refresh_token', refresh_token)
        apiClient.defaults.headers.common.Authorization = `Bearer ${token}`

        processQueue(null, token)
        originalRequest.headers.Authorization = `Bearer ${token}`
        return apiClient(originalRequest)
      } catch (err) {
        processQueue(err, null)
        localStorage.removeItem('token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('user')
        window.location.href = '/login'
        return Promise.reject(err)
      }
    }

    return Promise.reject(error)
  }
)

export default apiClient
