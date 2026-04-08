/**
 * Collaborative LaTeX Editor with Yjs CRDT
 * Requirements: 11.1, 11.2, 11.9, 7.10
 */

import React, { useEffect, useRef, useState } from 'react'
import { EditorView, basicSetup } from 'codemirror'
import { EditorState } from '@codemirror/state'
import { keymap } from '@codemirror/view'
import { defaultKeymap, indentWithTab } from '@codemirror/commands'
import { foldGutter, foldKeymap } from '@codemirror/language'
import { yCollab } from 'y-codemirror.next'
import { latex } from '../editor/latex-lang'
import { createLatexAutocompletion } from '../editor/latex-completions'
import { 
  createYjsDocument, 
  destroyYjsDocument, 
  getConnectionStatus,
  getCollaborators 
} from '../collaboration/YjsProvider'
import { createOfflineSyncManager } from '../collaboration/OfflineSync'
import './CollaborativeLaTeXEditor.css'

const CollaborativeLaTeXEditor = ({ 
  documentId,
  projectId,
  userId,
  userName,
  userColor = '#' + Math.floor(Math.random()*16777215).toString(16), // Random color
  onCompile,
  onContentChange
}) => {
  const editorRef = useRef(null)
  const viewRef = useRef(null)
  const yjsProvidersRef = useRef(null)
  const offlineSyncRef = useRef(null)
  
  const [connectionStatus, setConnectionStatus] = useState('disconnected')
  const [collaborators, setCollaborators] = useState([])
  const [syncStatus, setSyncStatus] = useState('syncing')
  const [offlineQueueSize, setOfflineQueueSize] = useState(0)
  
  // Initialize Yjs and CodeMirror editor
  useEffect(() => {
    if (!editorRef.current || !documentId) return
    
    // Create Yjs document and providers
    const providers = createYjsDocument(documentId, userId, userName, userColor)
    yjsProvidersRef.current = providers
    
    const { ydoc, ytext, wsProvider, awareness } = providers
    
    // Create offline sync manager (Requirement 11.9)
    const offlineSync = createOfflineSyncManager(documentId, ydoc, wsProvider)
    offlineSyncRef.current = offlineSync
    
    // Update offline queue size periodically
    const updateOfflineStatus = () => {
      const status = offlineSync.getStatus()
      setOfflineQueueSize(status.queuedChanges)
    }
    
    const offlineStatusInterval = setInterval(updateOfflineStatus, 1000)
    
    // Update connection status
    const updateConnectionStatus = () => {
      setConnectionStatus(getConnectionStatus(wsProvider))
    }
    
    wsProvider.on('status', updateConnectionStatus)
    wsProvider.on('sync', (synced) => {
      setSyncStatus(synced ? 'synced' : 'syncing')
    })
    
    // Update collaborators list
    const updateCollaborators = () => {
      setCollaborators(getCollaborators(awareness, userId))
    }
    
    awareness.on('change', updateCollaborators)
    
    // Initial update
    updateConnectionStatus()
    updateCollaborators()
    
    // AI suggestion function
    const getAISuggestions = async (contextText) => {
      try {
        // TODO: Implement API call
        return []
      } catch (error) {
        console.error('Failed to get AI suggestions:', error)
        return []
      }
    }
    
    // Citation fetch function
    const fetchCitations = async (projectId, partial) => {
      try {
        // TODO: Implement API call
        return []
      } catch (error) {
        console.error('Failed to fetch citations:', error)
        return []
      }
    }
    
    // Create CodeMirror editor with Yjs collaboration
    const startState = EditorState.create({
      doc: ytext.toString(),
      extensions: [
        basicSetup,
        latex,
        createLatexAutocompletion({
          projectId,
          fetchCitations,
          getAISuggestions
        }),
        // Yjs collaboration extension (Requirements: 11.1, 11.2)
        yCollab(ytext, awareness, {
          undoManager: new Y.UndoManager(ytext)
        }),
        keymap.of([
          ...defaultKeymap,
          ...foldKeymap,
          indentWithTab,
          {
            key: 'Ctrl-s',
            run: () => {
              handleCompile()
              return true
            }
          }
        ]),
        foldGutter(),
        EditorView.lineWrapping,
        EditorView.updateListener.of((update) => {
          if (update.docChanged) {
            const newContent = update.state.doc.toString()
            onContentChange?.(newContent)
          }
        })
      ]
    })
    
    const view = new EditorView({
      state: startState,
      parent: editorRef.current
    })
    
    viewRef.current = view
    
    // Cleanup
    return () => {
      clearInterval(offlineStatusInterval)
      view.destroy()
      if (offlineSyncRef.current) {
        offlineSyncRef.current.destroy()
      }
      destroyYjsDocument(providers)
    }
  }, [documentId, userId, userName, userColor, projectId])
  
  const handleCompile = () => {
    if (viewRef.current) {
      const currentContent = viewRef.current.state.doc.toString()
      onCompile?.(currentContent)
    }
  }
  
  const getStats = () => {
    if (!viewRef.current) return { lines: 0, chars: 0, words: 0 }
    
    const doc = viewRef.current.state.doc
    const text = doc.toString()
    
    return {
      lines: doc.lines,
      chars: text.length,
      words: text.trim().split(/\s+/).length
    }
  }
  
  const stats = getStats()
  
  return (
    <div className="collaborative-latex-editor">
      <div className="editor-header">
        <div className="header-left">
          <h3>LaTeX Source</h3>
          <div className="connection-status">
            <span className={`status-indicator ${connectionStatus}`}>
              {connectionStatus === 'connected' ? '● Connected' : '○ Disconnected'}
            </span>
            <span className="sync-status">
              {syncStatus === 'synced' ? '✓ Synced' : '⟳ Syncing...'}
            </span>
            {offlineQueueSize > 0 && (
              <span className="offline-queue">
                {offlineQueueSize} change{offlineQueueSize !== 1 ? 's' : ''} queued
              </span>
            )}
          </div>
        </div>
        
        <div className="header-right">
          <div className="editor-stats">
            <span>Lines: {stats.lines}</span>
            <span>Characters: {stats.chars}</span>
            <span>Words: {stats.words}</span>
          </div>
          
          {/* Collaborators list (Requirement 11.2) */}
          {collaborators.length > 0 && (
            <div className="collaborators-list">
              <span className="collaborators-label">
                {collaborators.length} collaborator{collaborators.length !== 1 ? 's' : ''}:
              </span>
              {collaborators.map(collab => (
                <div 
                  key={collab.clientId}
                  className="collaborator-badge"
                  style={{ backgroundColor: collab.color }}
                  title={collab.name}
                >
                  {collab.name.charAt(0).toUpperCase()}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
      
      <div ref={editorRef} className="codemirror-wrapper" />
    </div>
  )
}

export default CollaborativeLaTeXEditor
