/**
 * Yjs Provider for Real-Time Collaboration
 * Requirements: 11.1, 7.10
 */

import * as Y from 'yjs'
import { WebsocketProvider } from 'y-websocket'
import { IndexeddbPersistence } from 'y-indexeddb'

/**
 * Create and configure Yjs document with providers
 * @param {string} documentId - Unique document identifier
 * @param {string} userId - Current user ID
 * @param {string} userName - Current user name
 * @param {string} userColor - User color for cursor/selection
 * @returns {Object} Yjs document and providers
 */
export function createYjsDocument(documentId, userId, userName, userColor) {
  // Create Yjs document
  const ydoc = new Y.Doc()
  
  // Get or create text type for the document
  const ytext = ydoc.getText('codemirror')
  
  // Configure WebSocket provider for real-time sync
  const wsUrl = process.env.VITE_WS_URL || 'ws://localhost:1234'
  const wsProvider = new WebsocketProvider(wsUrl, documentId, ydoc, {
    connect: true,
    // Awareness protocol for cursor/selection sharing
    awareness: {
      user: {
        id: userId,
        name: userName,
        color: userColor,
        colorLight: userColor + '33' // Add transparency
      }
    }
  })
  
  // Configure IndexedDB persistence for offline support (Requirement 11.9)
  const indexeddbProvider = new IndexeddbPersistence(documentId, ydoc)
  
  // Wait for IndexedDB to sync
  indexeddbProvider.whenSynced.then(() => {
    console.log('Loaded content from IndexedDB')
  })
  
  // Connection status handlers
  wsProvider.on('status', event => {
    console.log('WebSocket status:', event.status) // 'connected' | 'disconnected'
  })
  
  wsProvider.on('sync', synced => {
    console.log('Sync status:', synced)
  })
  
  return {
    ydoc,
    ytext,
    wsProvider,
    indexeddbProvider,
    awareness: wsProvider.awareness
  }
}

/**
 * Destroy Yjs providers and clean up
 * @param {Object} providers - Providers object from createYjsDocument
 */
export function destroyYjsDocument(providers) {
  if (providers.wsProvider) {
    providers.wsProvider.destroy()
  }
  if (providers.indexeddbProvider) {
    providers.indexeddbProvider.destroy()
  }
  if (providers.ydoc) {
    providers.ydoc.destroy()
  }
}

/**
 * Get connection status
 * @param {WebsocketProvider} wsProvider - WebSocket provider
 * @returns {string} Connection status
 */
export function getConnectionStatus(wsProvider) {
  return wsProvider.wsconnected ? 'connected' : 'disconnected'
}

/**
 * Get list of active collaborators
 * @param {Object} awareness - Awareness instance
 * @param {string} currentUserId - Current user ID to exclude
 * @returns {Array} List of collaborators
 */
export function getCollaborators(awareness, currentUserId) {
  const collaborators = []
  
  awareness.getStates().forEach((state, clientId) => {
    if (state.user && state.user.id !== currentUserId) {
      collaborators.push({
        clientId,
        userId: state.user.id,
        name: state.user.name,
        color: state.user.color,
        cursor: state.cursor,
        selection: state.selection
      })
    }
  })
  
  return collaborators
}

/**
 * Update user cursor position in awareness
 * @param {Object} awareness - Awareness instance
 * @param {number} position - Cursor position
 */
export function updateCursor(awareness, position) {
  const localState = awareness.getLocalState()
  awareness.setLocalStateField('cursor', {
    position,
    timestamp: Date.now()
  })
}

/**
 * Update user selection in awareness
 * @param {Object} awareness - Awareness instance
 * @param {Object} selection - Selection object with from and to
 */
export function updateSelection(awareness, selection) {
  const localState = awareness.getLocalState()
  awareness.setLocalStateField('selection', {
    from: selection.from,
    to: selection.to,
    timestamp: Date.now()
  })
}

/**
 * Clear user cursor and selection
 * @param {Object} awareness - Awareness instance
 */
export function clearCursorAndSelection(awareness) {
  awareness.setLocalStateField('cursor', null)
  awareness.setLocalStateField('selection', null)
}

/**
 * Generate random user color
 * @returns {string} Hex color code
 */
export function generateUserColor() {
  const colors = [
    '#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', 
    '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E2',
    '#F8B739', '#52B788', '#E76F51', '#2A9D8F'
  ]
  return colors[Math.floor(Math.random() * colors.length)]
}
