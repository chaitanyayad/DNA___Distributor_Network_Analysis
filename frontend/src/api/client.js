import axios from 'axios'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' },
})

// Inject token on every request
client.interceptors.request.use((config) => {
  const token = window.__authToken
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Global 401 handler — page reload clears state and sends to /login
client.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      window.__authToken = null
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export default client
