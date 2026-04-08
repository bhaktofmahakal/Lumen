/**
 * Offline Support and Synchronization
 * Requirements: 11.9, 20.9
 */

import * as Y from 'yjs'

/**
 * Queue manager for offline changes
 */
class OfflineQueue {
  constructor(documentId) {
    this.documentId = documentId
    this.queueKey = `offline_queue_${documentId}`
    this.queue = this.loadQueue()
  }
  
  /**
   * Load queue from localStorage
   */
  loadQueue() {
    try {
      const stored = localStorage.getItem(this.queueKey)
      return stored ? JSON.parse(stored) : []
    } catch (error) {
      console.error('Failed to load offline queue:', error)
      return []
    }
  }
  
  /**
   * Save queue to localStorage
   */
  saveQueue() {
    try {
      localStorage.setItem(this.queueKey, JSON.stringify(this.queue))
    } catch (error) {
      console.error('Failed to save offline queue:', error)
    }
  }
  
  /**
   * Add change to queue
   */
  enqueue(change) {
    this.queue.push({
      ...change,
      timestamp: Date.now(),
      id: Math.random().toString(36).substr(2, 9)
    })
    this.saveQueue()
  }
  
  /**
   * Get all queued changes
   */
  getAll() {
    return [...this.queue]
  }
  
  /**
   * Clear queue
   */
  clear() {
    this.queue = []
    localStorage.removeItem(this.queueKey)
  }
  
  /**
   * Get queue size
   */
  size() {
    return this.queue.length
  }
}

/**
 * Offline sync manager
 */
export class OfflineSyncManager {
  constructor(documentId, ydoc, wsProvider) {
    this.documentId = documentId
    this.ydoc = ydoc
    this.wsProvider = wsProvider
    this.queue = new OfflineQueue(documentId)
    this.isOnline = navigator.onLine
    this.syncInProgress = false
    
    this.setupEventListeners()
  }
  
  /**
   * Set up online/offline event listeners
   */
  setupEventListeners() {
    // Listen for online/offline events
    window.addEventListener('online', () => this.handleOnline())
    window.addEventListener('offline', () => this.handleOffline())
    
    // Listen for WebSocket connection status
    this.wsProvider.on('status', ({ status }) => {
      if (status === 'connected') {
        this.handleOnline()
      } else if (status === 'disconnected') {
        this.handleOffline()
      }
    })
    
    // Listen for document changes when offline
    this.ydoc.on('update', (update, origin) => {
      if (!this.isOnline && origin !== 'offline-queue') {
        this.queueChange(update)
      }
    })
  }
  
  /**
   * Handle going online
   */
  async handleOnline() {
    console.log('Connection restored, syncing queued changes...')
    this.isOnline = true
    
    // Sync queued changes
    await this.syncQueuedChanges()
  }
  
  /**
   * Handle going offline
   */
  handleOffline() {
    console.log('Connection lost, queuing changes...')
    this.isOnline = false
  }
  
  /**
   * Queue a change when offline
   */
  queueChange(update) {
    this.queue.enqueue({
      update: Array.from(update),
      type: 'document_update'
    })
    console.log(`Queued change (${this.queue.size()} total)`)
  }
  
  /**
   * Sync all queued changes
   */
  async syncQueuedChanges() {
    if (this.syncInProgress || this.queue.size() === 0) {
      return
    }
    
    this.syncInProgress = true
    
    try {
      const changes = this.queue.getAll()
      console.log(`Syncing ${changes.length} queued changes...`)
      
      // Apply queued changes to the document
      // Yjs CRDT will automatically handle conflict resolution
      for (const change of changes) {
        if (change.type === 'document_update') {
          const update = new Uint8Array(change.update)
          Y.applyUpdate(this.ydoc, update, 'offline-queue')
        }
      }
      
      // Clear queue after successful sync
      this.queue.clear()
      console.log('Sync complete')
      
      return { success: true, synced: changes.length }
    } catch (error) {
      console.error('Sync failed:', error)
      return { success: false, error: error.message }
    } finally {
      this.syncInProgress = false
    }
  }
  
  /**
   * Get sync status
   */
  getStatus() {
    return {
      isOnline: this.isOnline,
      queuedChanges: this.queue.size(),
      syncInProgress: this.syncInProgress
    }
  }
  
  /**
   * Clean up
   */
  destroy() {
    window.removeEventListener('online', this.handleOnline)
    window.removeEventListener('offline', this.handleOffline)
  }
}

/**
 * Create offline sync manager
 */
export function createOfflineSyncManager(documentId, ydoc, wsProvider) {
  return new OfflineSyncManager(documentId, ydoc, wsProvider)
}
