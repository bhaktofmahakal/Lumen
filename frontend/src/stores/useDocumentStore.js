import { create } from 'zustand'

export const useDocumentStore = create((set) => ({
  documents: [],
  currentDocument: null,
  uploadProgress: {},
  
  setDocuments: (documents) => set({ documents }),
  
  setCurrentDocument: (document) => set({ currentDocument: document }),
  
  addDocument: (document) => set((state) => ({
    documents: [document, ...state.documents]
  })),
  
  updateDocument: (documentId, updates) => set((state) => ({
    documents: state.documents.map(d => 
      d.id === documentId ? { ...d, ...updates } : d
    ),
    currentDocument: state.currentDocument?.id === documentId 
      ? { ...state.currentDocument, ...updates }
      : state.currentDocument
  })),
  
  removeDocument: (documentId) => set((state) => ({
    documents: state.documents.filter(d => d.id !== documentId),
    currentDocument: state.currentDocument?.id === documentId 
      ? null 
      : state.currentDocument
  })),
  
  setUploadProgress: (fileId, progress) => set((state) => ({
    uploadProgress: { ...state.uploadProgress, [fileId]: progress }
  })),
  
  clearUploadProgress: (fileId) => set((state) => {
    const { [fileId]: _, ...rest } = state.uploadProgress
    return { uploadProgress: rest }
  }),
}))
