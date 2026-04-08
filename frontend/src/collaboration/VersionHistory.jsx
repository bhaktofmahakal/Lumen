/**
 * Version History Component
 * Requirements: 12.1, 12.2
 */

import React, { useState, useEffect } from 'react'
import './VersionHistory.css'

const VersionHistory = ({ documentId, onRestoreVersion, onCompareVersions }) => {
  const [versions, setVersions] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedVersion, setSelectedVersion] = useState(null)
  const [compareMode, setCompareMode] = useState(false)
  const [compareVersions, setCompareVersions] = useState([])
  
  useEffect(() => {
    loadVersionHistory()
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(loadVersionHistory, 30000)
    return () => clearInterval(interval)
  }, [documentId])
  
  const loadVersionHistory = async () => {
    try {
      const response = await fetch(`/api/documents/${documentId}/versions`)
      const data = await response.json()
      
      if (data.success) {
        setVersions(data.versions || [])
      }
    } catch (error) {
      console.error('Failed to load version history:', error)
    } finally {
      setLoading(false)
    }
  }
  
  const handleRestoreVersion = async (versionId) => {
    if (!confirm('Are you sure you want to restore this version? This will create a new version with the restored content.')) {
      return
    }
    
    try {
      const response = await fetch(`/api/documents/${documentId}/versions/${versionId}/restore`, {
        method: 'POST'
      })
      
      const data = await response.json()
      
      if (data.success) {
        onRestoreVersion?.(data.version)
        loadVersionHistory()
      }
    } catch (error) {
      console.error('Failed to restore version:', error)
      alert('Failed to restore version')
    }
  }
  
  const handleLabelVersion = async (versionId) => {
    const label = prompt('Enter a label for this version:')
    if (!label) return
    
    try {
      const response = await fetch(`/api/documents/${documentId}/versions/${versionId}/label`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ label })
      })
      
      const data = await response.json()
      
      if (data.success) {
        loadVersionHistory()
      }
    } catch (error) {
      console.error('Failed to label version:', error)
    }
  }
  
  const toggleCompareMode = () => {
    setCompareMode(!compareMode)
    setCompareVersions([])
  }
  
  const selectVersionForCompare = (versionId) => {
    if (compareVersions.includes(versionId)) {
      setCompareVersions(compareVersions.filter(id => id !== versionId))
    } else if (compareVersions.length < 2) {
      setCompareVersions([...compareVersions, versionId])
    }
  }
  
  const handleCompare = () => {
    if (compareVersions.length === 2) {
      onCompareVersions?.(compareVersions[0], compareVersions[1])
    }
  }
  
  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diffMs = now - date
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)
    
    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`
    if (diffHours < 24) return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`
    if (diffDays < 7) return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`
    
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString()
  }
  
  if (loading) {
    return <div className="version-history-loading">Loading version history...</div>
  }
  
  return (
    <div className="version-history">
      <div className="version-history-header">
        <h3>Version History</h3>
        <div className="version-history-actions">
          <button 
            onClick={toggleCompareMode}
            className={`btn btn-sm ${compareMode ? 'btn-primary' : 'btn-secondary'}`}
          >
            {compareMode ? 'Cancel Compare' : 'Compare Versions'}
          </button>
          {compareMode && compareVersions.length === 2 && (
            <button 
              onClick={handleCompare}
              className="btn btn-sm btn-primary"
            >
              View Diff
            </button>
          )}
        </div>
      </div>
      
      {compareMode && (
        <div className="compare-mode-info">
          Select 2 versions to compare ({compareVersions.length}/2 selected)
        </div>
      )}
      
      <div className="version-timeline">
        {versions.length === 0 ? (
          <div className="no-versions">
            No version history yet. Versions are auto-saved every 5 minutes.
          </div>
        ) : (
          versions.map((version, index) => (
            <div 
              key={version.id}
              className={`version-item ${selectedVersion === version.id ? 'selected' : ''} ${compareVersions.includes(version.id) ? 'compare-selected' : ''}`}
              onClick={() => compareMode ? selectVersionForCompare(version.id) : setSelectedVersion(version.id)}
            >
              <div className="version-marker">
                {compareMode && (
                  <input 
                    type="checkbox"
                    checked={compareVersions.includes(version.id)}
                    onChange={() => selectVersionForCompare(version.id)}
                    disabled={!compareVersions.includes(version.id) && compareVersions.length >= 2}
                  />
                )}
                <div className="version-dot" />
                {index < versions.length - 1 && <div className="version-line" />}
              </div>
              
              <div className="version-content">
                <div className="version-header">
                  <div className="version-info">
                    <span className="version-number">v{version.version_number}</span>
                    {version.label && (
                      <span className="version-label">{version.label}</span>
                    )}
                    {version.is_auto_save && (
                      <span className="auto-save-badge">Auto-save</span>
                    )}
                  </div>
                  <span className="version-time">{formatTimestamp(version.created_at)}</span>
                </div>
                
                <div className="version-meta">
                  <span className="version-author">{version.user_name}</span>
                  {version.change_summary && (
                    <span className="version-summary">{version.change_summary}</span>
                  )}
                </div>
                
                {selectedVersion === version.id && !compareMode && (
                  <div className="version-actions">
                    <button 
                      onClick={(e) => {
                        e.stopPropagation()
                        handleRestoreVersion(version.id)
                      }}
                      className="btn btn-sm btn-primary"
                    >
                      Restore
                    </button>
                    <button 
                      onClick={(e) => {
                        e.stopPropagation()
                        handleLabelVersion(version.id)
                      }}
                      className="btn btn-sm btn-secondary"
                    >
                      {version.label ? 'Edit Label' : 'Add Label'}
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

export default VersionHistory
