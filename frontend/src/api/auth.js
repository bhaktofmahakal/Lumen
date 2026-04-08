import apiClient from './client'

export const authApi = {
  login: async (email, password) => {
    const response = await apiClient.post('/api/auth/login.php', { email, password })
    return response.data
  },

  register: async (name, email, password) => {
    const response = await apiClient.post('/api/auth/register.php', { name, email, password })
    return response.data
  },

  logout: async () => {
    const response = await apiClient.post('/api/auth/logout.php')
    return response.data
  },

  verifyEmail: async (token) => {
    const response = await apiClient.get(`/api/auth/verify-email.php?token=${token}`)
    return response.data
  },

  requestPasswordReset: async (email) => {
    const response = await apiClient.post('/api/auth/reset-password.php', { email })
    return response.data
  },

  resetPassword: async (token, password) => {
    const response = await apiClient.post('/api/auth/reset-password.php', { token, password })
    return response.data
  },

  googleOAuth: () => {
    window.location.href = `${apiClient.defaults.baseURL}/api/auth/oauth-google.php`
  },
}
