import apiClient from './client'

export const chatApi = {
  getSessions: async (projectId) => {
    const response = await apiClient.get(`/api/chat/sessions.php?project_id=${projectId}`)
    return response.data
  },

  createSession: async (projectId, name) => {
    const response = await apiClient.post('/api/chat/sessions.php', { project_id: projectId, name })
    return response.data
  },

  sendMessage: async (sessionId, message, documentIds = []) => {
    const response = await apiClient.post('/api/chat/query.php', {
      session_id: sessionId,
      message,
      document_ids: documentIds,
    })
    return response.data
  },

  streamMessage: async (sessionId, message, documentIds = [], onChunk) => {
    const response = await fetch(`${apiClient.defaults.baseURL}/api/chat/stream.php`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiClient.defaults.headers.Authorization?.split(' ')[1]}`,
      },
      body: JSON.stringify({
        session_id: sessionId,
        message,
        document_ids: documentIds,
      }),
    })

    const reader = response.body.getReader()
    const decoder = new TextDecoder()

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = JSON.parse(line.slice(6))
          onChunk(data)
        }
      }
    }
  },

  uploadImage: async (sessionId, image) => {
    const formData = new FormData()
    formData.append('image', image)
    formData.append('session_id', sessionId)

    const response = await apiClient.post('/api/chat/upload-image.php', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  },
}
