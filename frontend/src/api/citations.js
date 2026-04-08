import apiClient from './client'

export const citationsApi = {
  getAll: async (projectId) => {
    const response = await apiClient.get(`/api/citations/index.php?project_id=${projectId}`)
    return response.data
  },

  create: async (projectId, citation) => {
    const response = await apiClient.post('/api/citations/index.php', { project_id: projectId, ...citation })
    return response.data
  },

  update: async (citationId, updates) => {
    const response = await apiClient.put('/api/citations/index.php', { id: citationId, ...updates })
    return response.data
  },

  delete: async (citationId) => {
    const response = await apiClient.delete(`/api/citations/index.php?id=${citationId}`)
    return response.data
  },

  export: async (projectId, format) => {
    const response = await apiClient.get(`/api/citations/export.php?project_id=${projectId}&format=${format}`)
    return response.data
  },
}
