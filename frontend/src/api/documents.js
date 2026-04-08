import apiClient from './client'

export const documentsApi = {
  getAll: async (projectId) => {
    const response = await apiClient.get(`/api/documents/index.php?project_id=${projectId}`)
    return response.data
  },

  upload: async (projectId, file, onProgress) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('project_id', projectId)

    const response = await apiClient.post('/api/documents/upload.php', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (progressEvent) => {
        const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
        onProgress?.(progress)
      },
    })
    return response.data
  },

  delete: async (documentId) => {
    const response = await apiClient.delete(`/api/documents/index.php?id=${documentId}`)
    return response.data
  },

  getVersions: async (documentId) => {
    const response = await apiClient.get(`/api/documents/versions.php?document_id=${documentId}`)
    return response.data
  },
}
