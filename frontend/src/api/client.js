import axios from 'axios'
import { useAuthStore } from '../stores/useAuthStore'
import { offlineSyncManager } from '../utils/offlineSync'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080'

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().token
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor for error handling and offline mode
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle authentication errors
    if (error.response?.status === 401) {
      useAuthStore.getState().logout()
      window.location.href = '/login'
      return Promise.reject(error)
    }

    // Handle network errors (offline mode)
    if (!navigator.onLine || error.code === 'ERR_NETWORK') {
      // Queue the request for later sync if it's a mutation
      const config = error.config
      if (config.method !== 'get' && config.method !== 'head') {
        console.log('Offline: Queuing request for later sync')
        // The specific action type will be determined by the calling code
        // This is just a fallback for generic requests
        return Promise.reject({
          ...error,
          isOffline: true,
          message: 'You are offline. This action will be synced when you reconnect.',
        })
      }
    }

    return Promise.reject(error)
  }
)

// Helper function to make offline-aware API calls
export async function offlineAwareRequest(config, actionType, actionPayload) {
  try {
    return await apiClient(config)
  } catch (error) {
    if (error.isOffline && actionType) {
      // Queue the action for offline sync
      offlineSyncManager.queueAction(actionType, actionPayload)
      return {
        data: { queued: true, message: 'Action queued for sync when online' },
      }
    }
    throw error
  }
}

export default apiClient
