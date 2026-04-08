import { create } from 'zustand'

export const useChatStore = create((set) => ({
  sessions: [],
  currentSession: null,
  messages: [],
  isStreaming: false,
  
  setSessions: (sessions) => set({ sessions }),
  
  setCurrentSession: (session) => set({ 
    currentSession: session,
    messages: session?.messages || []
  }),
  
  addSession: (session) => set((state) => ({
    sessions: [session, ...state.sessions]
  })),
  
  addMessage: (message) => set((state) => ({
    messages: [...state.messages, message]
  })),
  
  updateMessage: (messageId, updates) => set((state) => ({
    messages: state.messages.map(m => 
      m.id === messageId ? { ...m, ...updates } : m
    )
  })),
  
  setStreaming: (isStreaming) => set({ isStreaming }),
  
  clearMessages: () => set({ messages: [] }),
}))
