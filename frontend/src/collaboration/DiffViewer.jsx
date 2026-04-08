/**
 * Diff Viewer for Version Comparison
 * Requirements: 12.3, 12.4
 */

import React, { useState, useEffect } from 'react'
import './DiffViewer.css'

const DiffViewer = ({ documentId, version1Id, version2Id, onClose }) => {
  const [diffData, setDiffData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [viewMode, setViewMode] = useState('side-by-side') // 'side-by-side' or 'unified'
  
  useEffect(() => {
    loadDiff()
  }, [version1Id, version2Id])
  
  const loadDiff = async () => {
    try {
      const response = await fetch(
        `/api/documents/${documentId}/versions/diff?v1=${version1Id}&v2=${version2Id}`
      )
      const data = await response.json()
      
      if (data.success) {
        setDiffData(data.diff)
      }
    } catch (error) {
      console.error('Failed to load diff:', error)
    } finally {
      setLoading(false)
    }
  }
  
  const renderSideBySide = () => {
    if (!diffData) return null
    
    return (
      <div className="diff-side-by-side">
        <div className="diff-pane diff-pane-left">
          <div className="diff-pane-header">
            Version {diffData.version1.version_number}
            <span className="diff-pane-meta">
              {new Date(diffData.version1.created_at).toLocaleString()}
            </span>
          </div>
          <div className="diff-content">
            {diffData.changes.map((change, index) => (
              <div key={index} className={`diff-line ${change.type}`}>
                <span className="line-number">{change.lineNumber1 || ''}</span>
                <span className="line-content">{change.content1 || ''}</span>
              </div>
            ))}
          </div>
        </div>
        
        <div className="diff-pane diff-pane-right">
          <div className="diff-pane-header">
            Version {diffData.version2.version_number}
            <span className="diff-pane-meta">
              {new Date(diffData.version2.created_at).toLocaleString()}
            </span>
          </div>
          <div className="diff-content">
            {diffData.changes.map((change, index) => (
              <div key={index} className={`diff-line ${change.type}`}>
                <span className="line-number">{change.lineNumber2 || ''}</span>
                <span className="line-content">{change.content2 || ''}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }
  
  const renderUnified = () => {
    if (!diffData) return null
    
    return (
      <div className="diff-unified">
        <div className="diff-pane-header">
          Comparing v{diffData.version1.version_number} → v{diffData.version2.version_number}
        </div>
        <div className="diff-content">
          {diffData.changes.map((change, index) => (
            <div key={index} className={`diff-line ${change.type}`}>
              <span className="line-marker">
                {change.type === 'addition' ? '+' : change.type === 'deletion' ? '-' : ' '}
              </span>
              <span className="line-number">
                {change.lineNumber1 || change.lineNumber2 || ''}
              </span>
              <span className="line-content">
                {change.content1 || change.content2 || ''}
              </span>
            </div>
          ))}
        </div>
      </div>
    )
  }
  
  const getDiffStats = () => {
    if (!diffData) return { additions: 0, deletions: 0, unchanged: 0 }
    
    return diffData.changes.reduce((stats, change) => {
      if (change.type === 'addition') stats.additions++
      else if (change.type === 'deletion') stats.deletions++
      else stats.unchanged++
      return stats
    }, { additions: 0, deletions: 0, unchanged: 0 })
  }
  
  if (loading) {
    return (
      <div className="diff-viewer">
        <div className="diff-loading">Loading diff...</div>
      </div>
    )
  }
  
  if (!diffData) {
    return (
      <div className="diff-viewer">
        <div className="diff-error">Failed to load diff</div>
      </div>
    )
  }
  
  const stats = getDiffStats()
  
  return (
    <div className="diff-viewer">
      <div className="diff-header">
        <div className="diff-title">
          <h3>Version Comparison</h3>
          <button onClick={onClose} className="btn-close">×</button>
        </div>
        
        <div className="diff-controls">
          <div className="diff-stats">
            <span className="stat-addition">+{stats.additions}</span>
            <span className="stat-deletion">-{stats.deletions}</span>
            <span className="stat-unchanged">{stats.unchanged} unchanged</span>
          </div>
          
          <div className="view-mode-toggle">
            <button 
              onClick={() => setViewMode('side-by-side')}
              className={`btn btn-sm ${viewMode === 'side-by-side' ? 'active' : ''}`}
            >
              Side by Side
            </button>
            <button 
              onClick={() => setViewMode('unified')}
              className={`btn btn-sm ${viewMode === 'unified' ? 'active' : ''}`}
            >
              Unified
            </button>
          </div>
        </div>
      </div>
      
      <div className="diff-body">
        {viewMode === 'side-by-side' ? renderSideBySide() : renderUnified()}
      </div>
    </div>
  )
}

export default DiffViewer
