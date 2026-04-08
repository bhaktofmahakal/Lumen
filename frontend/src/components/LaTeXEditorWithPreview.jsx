/**
 * LaTeX Editor with Real-Time PDF Preview
 * Requirements: 7.8
 */

import React, { useState, useCallback, useRef, useEffect } from 'react'
import LaTeXEditor from './LaTeXEditor'
import PDFViewer from './PDFViewer'
import './LaTeXEditorWithPreview.css'

const LaTeXEditorWithPreview = ({ projectId, documentId, initialContent = '' }) => {
  const [content, setContent] = useState(initialContent)
  const [pdfUrl, setPdfUrl] = useState(null)
  const [compiling, setCompiling] = useState(false)
  const [compilationErrors, setCompilationErrors] = useState(null)
  const [compilationWarnings, setCompilationWarnings] = useState(null)
  const [aiFixSuggestions, setAiFixSuggestions] = useState(null)
  const [showErrors, setShowErrors] = useState(false)
  const [splitRatio, setSplitRatio] = useState(50) // Percentage for editor width
  const [autoCompile, setAutoCompile] = useState(false)
  const autoCompileTimerRef = useRef(null)
  
  // Handle content changes
  const handleContentChange = useCallback((newContent) => {
    setContent(newContent)
    
    // Auto-compile if enabled
    if (autoCompile) {
      // Clear existing timer
      if (autoCompileTimerRef.current) {
        clearTimeout(autoCompileTimerRef.current)
      }
      
      // Set new timer for 3 seconds after last change
      autoCompileTimerRef.current = setTimeout(() => {
        handleCompile(newContent)
      }, 3000)
    }
  }, [autoCompile])
  
  // Compile LaTeX document
  const handleCompile = async (contentToCompile = content) => {
    setCompiling(true)
    setCompilationErrors(null)
    setCompilationWarnings(null)
    setAiFixSuggestions(null)
    setShowErrors(false)
    
    try {
      const response = await fetch('/api/latex/compile', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content: contentToCompile,
          project_id: projectId,
          document_id: documentId
        })
      })
      
      const result = await response.json()
      
      if (result.success) {
        setPdfUrl(result.pdf_url)
        
        // Show warnings if any
        if (result.warnings && result.warnings.length > 0) {
          setCompilationWarnings(result.warnings)
        }
      } else {
        // Compilation failed
        setCompilationErrors(result.errors)
        setAiFixSuggestions(result.ai_fixes)
        setShowErrors(true)
      }
    } catch (error) {
      console.error('Compilation error:', error)
      setCompilationErrors([{
        type: 'network_error',
        message: 'Failed to connect to compilation service'
      }])
      setShowErrors(true)
    } finally {
      setCompiling(false)
    }
  }
  
  // Apply AI fix suggestion
  const applyAIFix = (fix) => {
    // TODO: Implement smart fix application
    // For now, just show the suggestion
    alert(`Suggested fix:\n\n${fix.suggested_fix}\n\nExplanation:\n${fix.explanation}`)
  }
  
  // Handle split pane resize
  const handleMouseDown = (e) => {
    e.preventDefault()
    
    const startX = e.clientX
    const startRatio = splitRatio
    
    const handleMouseMove = (e) => {
      const deltaX = e.clientX - startX
      const containerWidth = e.target.parentElement.offsetWidth
      const deltaRatio = (deltaX / containerWidth) * 100
      const newRatio = Math.max(20, Math.min(80, startRatio + deltaRatio))
      setSplitRatio(newRatio)
    }
    
    const handleMouseUp = () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }
    
    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)
  }
  
  return (
    <div className="latex-editor-with-preview">
      <div className="editor-toolbar">
        <div className="toolbar-left">
          <button 
            onClick={() => handleCompile()} 
            disabled={compiling}
            className="btn btn-primary"
          >
            {compiling ? 'Compiling...' : 'Compile (Ctrl+S)'}
          </button>
          
          <label className="auto-compile-toggle">
            <input 
              type="checkbox" 
              checked={autoCompile}
              onChange={(e) => setAutoCompile(e.target.checked)}
            />
            Auto-compile
          </label>
        </div>
        
        <div className="toolbar-right">
          {compilationErrors && (
            <button 
              onClick={() => setShowErrors(!showErrors)}
              className="btn btn-error"
            >
              {compilationErrors.length} Error{compilationErrors.length !== 1 ? 's' : ''}
            </button>
          )}
          
          {compilationWarnings && (
            <span className="warning-badge">
              {compilationWarnings.length} Warning{compilationWarnings.length !== 1 ? 's' : ''}
            </span>
          )}
        </div>
      </div>
      
      {showErrors && compilationErrors && (
        <div className="error-panel">
          <div className="error-panel-header">
            <h3>Compilation Errors</h3>
            <button onClick={() => setShowErrors(false)} className="btn-close">×</button>
          </div>
          
          <div className="error-list">
            {compilationErrors.map((error, index) => (
              <div key={index} className="error-item">
                <div className="error-header">
                  <span className="error-type">{error.type}</span>
                  {error.line && <span className="error-line">Line {error.line}</span>}
                </div>
                <div className="error-message">{error.message}</div>
                
                {/* AI Fix Suggestion (Requirement 7.5) */}
                {aiFixSuggestions && aiFixSuggestions[index] && (
                  <div className="ai-fix-suggestion">
                    <div className="ai-fix-header">
                      <span className="ai-badge">AI Suggestion</span>
                      <button 
                        onClick={() => applyAIFix(aiFixSuggestions[index])}
                        className="btn btn-sm btn-ai"
                      >
                        Apply Fix
                      </button>
                    </div>
                    <div className="ai-fix-explanation">
                      {aiFixSuggestions[index].explanation}
                    </div>
                    <pre className="ai-fix-code">
                      {aiFixSuggestions[index].suggested_fix}
                    </pre>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
      
      <div className="split-view">
        <div className="editor-pane" style={{ width: `${splitRatio}%` }}>
          <LaTeXEditor
            initialContent={initialContent}
            onCompile={handleCompile}
            onContentChange={handleContentChange}
            projectId={projectId}
          />
        </div>
        
        <div 
          className="split-divider" 
          onMouseDown={handleMouseDown}
        />
        
        <div className="preview-pane" style={{ width: `${100 - splitRatio}%` }}>
          <div className="preview-header">
            <h3>PDF Preview</h3>
          </div>
          <PDFViewer pdfUrl={pdfUrl} syncScroll={true} />
        </div>
      </div>
    </div>
  )
}

export default LaTeXEditorWithPreview
