import apiClient from './client'

export const projectsApi = {
  getAll: async () => {
    const response = await apiClient.get('/api/projects/index.php')
    return response.data
  },

  getById: async (projectId) => {
    const response = await apiClient.get(`/api/projects/index.php?id=${projectId}`)
    return response.data
  },

  create: async (name, description) => {
    const response = await apiClient.post('/api/projects/index.php', { name, description })
    return response.data
  },

  update: async (projectId, updates) => {
    const response = await apiClient.put('/api/projects/index.php', { id: projectId, ...updates })
    return response.data
  },

  delete: async (projectId) => {
    const response = await apiClient.delete(`/api/projects/index.php?id=${projectId}`)
    return response.data
  },

  share: async (projectId, email, role) => {
    const response = await apiClient.post('/api/projects/share.php', { project_id: projectId, email, role })
    return response.data
  },
}
