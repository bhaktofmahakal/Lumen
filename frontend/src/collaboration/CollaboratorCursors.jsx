/**
 * Collaborator Cursors and Selections Display
 * Requirements: 11.2
 */

import React from 'react'
import './CollaboratorCursors.css'

const CollaboratorCursors = ({ collaborators }) => {
  if (!collaborators || collaborators.length === 0) {
    return null
  }
  
  return (
    <div className="collaborator-cursors-container">
      {collaborators.map(collab => (
        <div key={collab.clientId}>
          {/* Cursor indicator */}
          {collab.cursor && (
            <div 
              className="collaborator-cursor"
              style={{
                borderColor: collab.color,
                top: `${collab.cursor.position}px`
              }}
            >
              <div 
                className="collaborator-cursor-label"
                style={{ backgroundColor: collab.color }}
              >
                {collab.name}
              </div>
            </div>
          )}
          
          {/* Selection highlight */}
          {collab.selection && (
            <div 
              className="collaborator-selection"
              style={{
                backgroundColor: collab.color + '33', // Add transparency
                top: `${collab.selection.from}px`,
                height: `${collab.selection.to - collab.selection.from}px`
              }}
            />
          )}
        </div>
      ))}
    </div>
  )
}

export default CollaboratorCursors
