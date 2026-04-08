import useOfflineStore from '../stores/useOfflineStore';
import { apiClient } from '../api/client';

class OfflineSyncManager {
  constructor() {
    this.isInitialized = false;
    this.syncInProgress = false;
  }

  initialize() {
    if (this.isInitialized) return;

    // Listen for network reconnection
    window.addEventListener('network-reconnected', () => {
      this.syncOfflineActions();
    });

    // Listen for visibility change to sync when app becomes visible
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden && navigator.onLine) {
        this.syncOfflineActions();
      }
    });

    this.isInitialized = true;
  }

  async syncOfflineActions() {
    if (this.syncInProgress) {
      console.log('Sync already in progress');
      return;
    }

    const store = useOfflineStore.getState();
    const queue = store.offlineQueue;

    if (queue.length === 0) {
      console.log('No offline actions to sync');
      return;
    }

    console.log(`Syncing ${queue.length} offline actions...`);
    this.syncInProgress = true;
    store.startSync();

    const errors = [];

    for (const action of queue) {
      try {
        await this.executeAction(action);
        store.removeAction(action.id);
        console.log(`Synced action: ${action.type}`);
      } catch (error) {
        console.error(`Failed to sync action ${action.type}:`, error);
        errors.push({
          actionId: action.id,
          type: action.type,
          error: error.message,
        });
      }
    }

    this.syncInProgress = false;
    store.completeSync(errors);

    if (errors.length === 0) {
      console.log('All offline actions synced successfully');
    } else {
      console.warn(`${errors.length} actions failed to sync`);
    }
  }

  async executeAction(action) {
    switch (action.type) {
      case 'UPLOAD_DOCUMENT':
        return this.syncDocumentUpload(action);
      
      case 'SEND_MESSAGE':
        return this.syncChatMessage(action);
      
      case 'UPDATE_DOCUMENT':
        return this.syncDocumentUpdate(action);
      
      case 'CREATE_PROJECT':
        return this.syncProjectCreation(action);
      
      case 'ADD_CITATION':
        return this.syncCitationAdd(action);
      
      default:
        throw new Error(`Unknown action type: ${action.type}`);
    }
  }

  async syncDocumentUpload(action) {
    const formData = new FormData();
    formData.append('file', action.payload.file);
    formData.append('projectId', action.payload.projectId);
    
    const response = await apiClient.post('/api/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    
    return response.data;
  }

  async syncChatMessage(action) {
    const response = await apiClient.post('/api/chat/query', {
      sessionId: action.payload.sessionId,
      message: action.payload.message,
      projectId: action.payload.projectId,
    });
    
    return response.data;
  }

  async syncDocumentUpdate(action) {
    const response = await apiClient.put(
      `/api/documents/${action.payload.documentId}`,
      {
        content: action.payload.content,
        version: action.payload.version,
      }
    );
    
    return response.data;
  }

  async syncProjectCreation(action) {
    const response = await apiClient.post('/api/projects', {
      name: action.payload.name,
      description: action.payload.description,
    });
    
    return response.data;
  }

  async syncCitationAdd(action) {
    const response = await apiClient.post('/api/citations', {
      projectId: action.payload.projectId,
      citation: action.payload.citation,
    });
    
    return response.data;
  }

  // Queue an action for offline sync
  queueAction(type, payload) {
    const store = useOfflineStore.getState();
    store.queueAction({ type, payload });
    console.log(`Queued offline action: ${type}`);
  }

  // Get pending actions count
  getPendingCount() {
    const store = useOfflineStore.getState();
    return store.getPendingCount();
  }

  // Manually trigger sync
  async manualSync() {
    if (!navigator.onLine) {
      throw new Error('Cannot sync while offline');
    }
    await this.syncOfflineActions();
  }
}

// Export singleton instance
export const offlineSyncManager = new OfflineSyncManager();
