import axios from 'axios'

/* Render's blueprint can only pass a bare API hostname via `fromService`, so
   accept `host`, `host/api/v1`, or a full URL and normalise to the base the
   app expects. The documented local value already ends with /api/v1. */
function normalizeApiBase(raw) {
  let url = (raw || 'http://localhost:8000/api/v1').trim()
  if (!/^https?:\/\//i.test(url)) url = `https://${url}`
  url = url.replace(/\/+$/, '')
  if (!/\/api\/v1$/.test(url)) url += '/api/v1'
  return url
}

const BASE_URL = normalizeApiBase(import.meta.env.VITE_API_URL)

/* Access token lives in memory only — never localStorage/sessionStorage
   (SENTRA_BUILD_SPEC.md §5). */
let accessToken = null

export function getAccessToken() {
  return accessToken
}

export function setAccessToken(token) {
  accessToken = token || null
}

/* AuthProvider registers a handler so a failed refresh can clear app state. */
let authFailureHandler = null

export function registerAuthFailureHandler(fn) {
  authFailureHandler = fn
}

export const client = axios.create({
  baseURL: BASE_URL,
  withCredentials: true, // send the httpOnly refresh cookie on /auth/* calls
  headers: { 'Content-Type': 'application/json' },
})

client.interceptors.request.use((config) => {
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`
  }
  return config
})

const AUTH_PATHS = ['/auth/login/', '/auth/register/', '/auth/refresh/', '/auth/logout/']

function isAuthPath(url = '') {
  return AUTH_PATHS.some((p) => url.endsWith(p))
}

/* A bare (interceptor-free) call so refresh can't recurse. Shared promise so a
   burst of parallel 401s only triggers one refresh round-trip. */
let refreshPromise = null

export function rawRefresh() {
  if (!refreshPromise) {
    refreshPromise = axios
      .post(`${BASE_URL}/auth/refresh/`, {}, { withCredentials: true })
      .then((res) => res.data.access)
      .finally(() => {
        refreshPromise = null
      })
  }
  return refreshPromise
}

client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config
    const status = error.response?.status

    if (status !== 401 || !original || original._retry || isAuthPath(original.url)) {
      return Promise.reject(error)
    }

    original._retry = true
    try {
      const newToken = await rawRefresh()
      setAccessToken(newToken)
      original.headers = original.headers || {}
      original.headers.Authorization = `Bearer ${newToken}`
      return client(original)
    } catch (refreshError) {
      setAccessToken(null)
      if (authFailureHandler) authFailureHandler()
      return Promise.reject(refreshError)
    }
  }
)
