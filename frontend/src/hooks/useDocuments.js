import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { documentsApi } from '../api/documents'
import { useDocumentStore } from '../stores/useDocumentStore'

export const useDocuments = (projectId) => {
  const setDocuments = useDocumentStore((state) => state.setDocuments)

  return useQuery({
    queryKey: ['documents', projectId],
    queryFn: async () => {
      const data = await documentsApi.getAll(projectId)
      setDocuments(data.documents || [])
      return data.documents || []
    },
    enabled: !!projectId,
  })
}

export const useUploadDocument = () => {
  const queryClient = useQueryClient()
  const addDocument = useDocumentStore((state) => state.addDocument)
  const setUploadProgress = useDocumentStore((state) => state.setUploadProgress)
  const clearUploadProgress = useDocumentStore((state) => state.clearUploadProgress)

  return useMutation({
    mutationFn: ({ projectId, file }) => {
      const fileId = `${file.name}-${Date.now()}`
      return documentsApi.upload(projectId, file, (progress) => {
        setUploadProgress(fileId, progress)
      }).finally(() => {
        clearUploadProgress(fileId)
      })
    },
    onSuccess: (data, variables) => {
      addDocument(data.document)
      queryClient.invalidateQueries({ queryKey: ['documents', variables.projectId] })
    },
  })
}

export const useDeleteDocument = () => {
  const queryClient = useQueryClient()
  const removeDocument = useDocumentStore((state) => state.removeDocument)

  return useMutation({
    mutationFn: (documentId) => documentsApi.delete(documentId),
    onSuccess: (_, documentId) => {
      removeDocument(documentId)
      queryClient.invalidateQueries({ queryKey: ['documents'] })
    },
  })
}
