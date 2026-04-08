/**
 * Commenting System for Collaborative Editing
 * Requirements: 11.5, 11.6
 */

import React, { useState, useEffect, useRef } from 'react'
import './CommentingSystem.css'

const CommentingSystem = ({ 
  documentId, 
  projectId, 
  userId, 
  userName,
  onMention 
}) => {
  const [comments, setComments] = useState([])
  const [activeComment, setActiveComment] = useState(null)
  const [newCommentText, setNewCommentText] = useState('')
  const [selectedLine, setSelectedLine] = useState(null)
  const [showCommentBox, setShowCommentBox] = useState(false)
  const commentInputRef = useRef(null)
  
  // Load comments from server
  useEffect(() => {
    loadComments()
  }, [documentId])
  
  const loadComments = async () => {
    try {
      const response = await fetch(`/api/documents/${documentId}/comments`)
      const data = await response.json()
      setComments(data.comments || [])
    } catch (error) {
      console.error('Failed to load comments:', error)
    }
  }
  
  // Add new comment (Requirement 11.5)
  const addComment = async () => {
    if (!newCommentText.trim() || selectedLine === null) return
    
    try {
      const response = await fetch(`/api/documents/${documentId}/comments`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          project_id: projectId,
          user_id: userId,
          user_name: userName,
          line_number: selectedLine,
          content: newCommentText,
          mentions: extractMentions(newCommentText)
        })
      })
      
      const data = await response.json()
      
      if (data.success) {
        setComments([...comments, data.comment])
        setNewCommentText('')
        setShowCommentBox(false)
        
        // Send notifications for mentions (Requirement 11.6)
        const mentions = extractMentions(newCommentText)
        if (mentions.length > 0 && onMention) {
          onMention(mentions, data.comment)
        }
      }
    } catch (error) {
      console.error('Failed to add comment:', error)
    }
  }
  
  // Extract @mentions from text (Requirement 11.6)
  const extractMentions = (text) => {
    const mentionRegex = /@(\w+)/g
    const mentions = []
    let match
    
    while ((match = mentionRegex.exec(text)) !== null) {
      mentions.push(match[1])
    }
    
    return mentions
  }
  
  // Highlight mentions in text
  const highlightMentions = (text) => {
    return text.replace(/@(\w+)/g, '<span class="mention">@$1</span>')
  }
  
  // Reply to comment
  const replyToComment = async (commentId, replyText) => {
    try {
      const response = await fetch(`/api/documents/${documentId}/comments/${commentId}/replies`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          user_id: userId,
          user_name: userName,
          content: replyText,
          mentions: extractMentions(replyText)
        })
      })
      
      const data = await response.json()
      
      if (data.success) {
        // Update comments with new reply
        setComments(comments.map(comment => 
          comment.id === commentId 
            ? { ...comment, replies: [...(comment.replies || []), data.reply] }
            : comment
        ))
        
        // Send notifications for mentions
        const mentions = extractMentions(replyText)
        if (mentions.length > 0 && onMention) {
          onMention(mentions, data.reply)
        }
      }
    } catch (error) {
      console.error('Failed to add reply:', error)
    }
  }
  
  // Resolve comment
  const resolveComment = async (commentId) => {
    try {
      const response = await fetch(`/api/documents/${documentId}/comments/${commentId}/resolve`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          user_id: userId,
          resolved: true
        })
      })
      
      const data = await response.json()
      
      if (data.success) {
        setComments(comments.map(comment => 
          comment.id === commentId 
            ? { ...comment, resolved: true, resolved_by: userName, resolved_at: new Date() }
            : comment
        ))
      }
    } catch (error) {
      console.error('Failed to resolve comment:', error)
    }
  }
  
  // Delete comment
  const deleteComment = async (commentId) => {
    try {
      const response = await fetch(`/api/documents/${documentId}/comments/${commentId}`, {
        method: 'DELETE'
      })
      
      const data = await response.json()
      
      if (data.success) {
        setComments(comments.filter(comment => comment.id !== commentId))
      }
    } catch (error) {
      console.error('Failed to delete comment:', error)
    }
  }
  
  // Open comment box for specific line
  const openCommentBox = (lineNumber) => {
    setSelectedLine(lineNumber)
    setShowCommentBox(true)
    setTimeout(() => commentInputRef.current?.focus(), 100)
  }
  
  // Get comments for specific line
  const getCommentsForLine = (lineNumber) => {
    return comments.filter(comment => comment.line_number === lineNumber && !comment.resolved)
  }
  
  return (
    <div className="commenting-system">
      <div className="comments-header">
        <h3>Comments</h3>
        <span className="comment-count">
          {comments.filter(c => !c.resolved).length} active
        </span>
      </div>
      
      {showCommentBox && (
        <div className="new-comment-box">
          <div className="comment-box-header">
            <span>Comment on line {selectedLine}</span>
            <button 
              onClick={() => setShowCommentBox(false)}
              className="btn-close"
            >
              ×
            </button>
          </div>
          
          <textarea
            ref={commentInputRef}
            value={newCommentText}
            onChange={(e) => setNewCommentText(e.target.value)}
            placeholder="Add a comment... Use @username to mention someone"
            className="comment-input"
            rows={3}
          />
          
          <div className="comment-box-actions">
            <button 
              onClick={addComment}
              className="btn btn-primary"
              disabled={!newCommentText.trim()}
            >
              Add Comment
            </button>
            <button 
              onClick={() => setShowCommentBox(false)}
              className="btn btn-secondary"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
      
      <div className="comments-list">
        {comments.length === 0 ? (
          <div className="no-comments">
            No comments yet. Click on a line number to add a comment.
          </div>
        ) : (
          comments.map(comment => (
            <div 
              key={comment.id} 
              className={`comment-item ${comment.resolved ? 'resolved' : ''}`}
            >
              <div className="comment-header">
                <div className="comment-author">
                  <strong>{comment.user_name}</strong>
                  <span className="comment-line">Line {comment.line_number}</span>
                </div>
                <div className="comment-actions">
                  {!comment.resolved && (
                    <>
                      <button 
                        onClick={() => resolveComment(comment.id)}
                        className="btn-icon"
                        title="Resolve"
                      >
                        ✓
                      </button>
                      {comment.user_id === userId && (
                        <button 
                          onClick={() => deleteComment(comment.id)}
                          className="btn-icon"
                          title="Delete"
                        >
                          🗑
                        </button>
                      )}
                    </>
                  )}
                </div>
              </div>
              
              <div 
                className="comment-content"
                dangerouslySetInnerHTML={{ __html: highlightMentions(comment.content) }}
              />
              
              <div className="comment-meta">
                {new Date(comment.created_at).toLocaleString()}
                {comment.resolved && (
                  <span className="resolved-badge">
                    Resolved by {comment.resolved_by}
                  </span>
                )}
              </div>
              
              {comment.replies && comment.replies.length > 0 && (
                <div className="comment-replies">
                  {comment.replies.map(reply => (
                    <div key={reply.id} className="reply-item">
                      <div className="reply-author">
                        <strong>{reply.user_name}</strong>
                      </div>
                      <div 
                        className="reply-content"
                        dangerouslySetInnerHTML={{ __html: highlightMentions(reply.content) }}
                      />
                      <div className="reply-meta">
                        {new Date(reply.created_at).toLocaleString()}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  )
}

export default CommentingSystem
