import { create } from 'zustand';

const useOfflineStore = create((set, get) => ({
  // Offline queue for actions
  offlineQueue: [],
  
  // Sync status
  isSyncing: false,
  lastSyncTime: null,
  syncErrors: [],
  
  // Add action to offline queue
  queueAction: (action) => {
    set((state) => ({
      offlineQueue: [
        ...state.offlineQueue,
        {
          id: Date.now() + Math.random(),
          timestamp: Date.now(),
          ...action,
        },
      ],
    }));
  },
  
  // Remove action from queue
  removeAction: (actionId) => {
    set((state) => ({
      offlineQueue: state.offlineQueue.filter((a) => a.id !== actionId),
    }));
  },
  
  // Clear all queued actions
  clearQueue: () => {
    set({ offlineQueue: [], syncErrors: [] });
  },
  
  // Get pending actions count
  getPendingCount: () => {
    return get().offlineQueue.length;
  },
  
  // Start sync process
  startSync: () => {
    set({ isSyncing: true, syncErrors: [] });
  },
  
  // Complete sync process
  completeSync: (errors = []) => {
    set({
      isSyncing: false,
      lastSyncTime: Date.now(),
      syncErrors: errors,
    });
  },
  
  // Add sync error
  addSyncError: (error) => {
    set((state) => ({
      syncErrors: [...state.syncErrors, error],
    }));
  },
}));

export default useOfflineStore;
