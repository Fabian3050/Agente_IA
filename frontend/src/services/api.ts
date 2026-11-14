import axios from 'axios'

// Environment or default microservice endpoints
export const MS_ENDPOINTS = {
  MS4_ORCHESTRATOR: import.meta.env.VITE_MS4_URL || 'http://localhost:8000',
  MS1_RETRIEVAL: import.meta.env.VITE_MS1_URL || 'http://localhost:8001',
  MS2_CLASSIFICATION: import.meta.env.VITE_MS2_URL || 'http://localhost:8002',
  MS3_AUTH: import.meta.env.VITE_MS3_URL || 'http://localhost:8003',
}

export function createApiClient(baseURL: string) {
  const client = axios.create({
    baseURL,
    timeout: 15000,
    headers: {
      'Content-Type': 'application/json',
    },
  })

  // Interceptor to inject JWT Bearer Token
  client.interceptors.request.use((config) => {
    const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token')
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  }, (error) => Promise.reject(error))

  // Interceptor to handle 401 unauthorized
  client.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response && error.response.status === 401) {
        // Clear token if expired or unauthorized
        // console.warn('Sesión expirada o no autorizada')
      }
      return Promise.reject(error)
    }
  )

  return client
}

export const ms4Client = createApiClient(MS_ENDPOINTS.MS4_ORCHESTRATOR)
export const ms1Client = createApiClient(MS_ENDPOINTS.MS1_RETRIEVAL)
export const ms2Client = createApiClient(MS_ENDPOINTS.MS2_CLASSIFICATION)
export const ms3Client = createApiClient(MS_ENDPOINTS.MS3_AUTH)

