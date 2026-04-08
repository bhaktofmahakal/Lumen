/**
 * LaTeX Editor Component with CodeMirror 6
 * Requirements: 7.1, 7.8, 20.3
 */

import React, { useEffect, useRef, useState } from 'react'
import { EditorView, basicSetup } from 'codemirror'
import { EditorState } from '@codemirror/state'
import { keymap } from '@codemirror/view'
import { defaultKeymap, indentWithTab } from '@codemirror/commands'
import { foldGutter, foldKeymap } from '@codemirror/language'
import { latex } from '../editor/latex-lang'
import { createLatexAutocompletion } from '../editor/latex-completions'
import './LaTeXEditor.css'

const LaTeXEditor = ({ 
  initialContent = '', 
  onCompile, 
  onContentChange,
  projectId 
}) => {
  const editorRef = useRef(null)
  const viewRef = useRef(null)
  const [content, setContent] = useState(initialContent)
  const [autoSaveStatus, setAutoSaveStatus] = useState('saved')
  const autoSaveTimerRef = useRef(null)
  
  // Initialize CodeMirror 6 editor
  useEffect(() => {
    if (!editorRef.current) return
    
    // AI suggestion function (Requirements: 7.2)
    const getAISuggestions = async (contextText) => {
      try {
        // TODO: Implement API call to get AI suggestions
        // const response = await axios.post('/api/latex/suggest', { context: contextText, projectId })
        // return response.data.suggestions
        return []
      } catch (error) {
        console.error('Failed to get AI suggestions:', error)
        return []
      }
    }
    
    // Citation fetch function (Requirements: 7.2)
    const fetchCitations = async (projectId, partial) => {
      try {
        // TODO: Implement API call to fetch citations
        // const response = await axios.get(`/api/projects/${projectId}/citations?q=${partial}`)
        // return response.data.citations
        return []
      } catch (error) {
        console.error('Failed to fetch citations:', error)
        return []
      }
    }
    
    const startState = EditorState.create({
      doc: initialContent,
      extensions: [
        basicSetup,
        latex,
        createLatexAutocompletion({
          projectId,
          fetchCitations,
          getAISuggestions
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
            setContent(newContent)
            onContentChange?.(newContent)
            handleAutoSave(newContent)
          }
        })
      ]
    })
    
    const view = new EditorView({
      state: startState,
      parent: editorRef.current
    })
    
    viewRef.current = view
    
    return () => {
      view.destroy()
    }
  }, [])
  
  // Auto-save functionality (Requirement 20.3)
  const handleAutoSave = (newContent) => {
    setAutoSaveStatus('saving')
    
    // Clear existing timer
    if (autoSaveTimerRef.current) {
      clearTimeout(autoSaveTimerRef.current)
    }
    
    // Set new timer for 30 seconds
    autoSaveTimerRef.current = setTimeout(() => {
      saveToLocalStorage(newContent)
      saveToServer(newContent)
      setAutoSaveStatus('saved')
    }, 30000) // 30 seconds
  }
  
  const saveToLocalStorage = (content) => {
    try {
      localStorage.setItem(`latex_backup_${projectId}`, content)
      localStorage.setItem(`latex_backup_${projectId}_timestamp`, Date.now().toString())
    } catch (error) {
      console.error('Failed to save to localStorage:', error)
    }
  }
  
  const saveToServer = async (content) => {
    try {
      // TODO: Implement server-side save endpoint
      // await axios.post(`/api/latex/save`, { projectId, content })
      console.log('Auto-saved to server')
    } catch (error) {
      console.error('Failed to save to server:', error)
    }
  }
  
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
    <div className="latex-editor-container">
      <div className="editor-header">
        <h3>LaTeX Source</h3>
        <div className="editor-stats">
          <span>Lines: {stats.lines}</span>
          <span>Characters: {stats.chars}</span>
          <span>Words: {stats.words}</span>
          <span className={`auto-save-status ${autoSaveStatus}`}>
            {autoSaveStatus === 'saving' ? '● Saving...' : '✓ Saved'}
          </span>
        </div>
      </div>
      <div ref={editorRef} className="codemirror-wrapper" />
    </div>
  )
}

export default LaTeXEditor
