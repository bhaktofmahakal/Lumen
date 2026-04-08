/**
 * MathJax 3 Equation Preview Component
 * Requirements: 7.12
 */

import React, { useEffect, useRef, useState } from 'react'
import './MathPreview.css'

// Load MathJax dynamically
const loadMathJax = () => {
  return new Promise((resolve, reject) => {
    if (window.MathJax) {
      resolve(window.MathJax)
      return
    }
    
    // Configure MathJax
    window.MathJax = {
      tex: {
        inlineMath: [['$', '$'], ['\\(', '\\)']],
        displayMath: [['$$', '$$'], ['\\[', '\\]']],
        processEscapes: true,
        processEnvironments: true,
        packages: {'[+]': ['ams', 'newcommand', 'configmacros']}
      },
      svg: {
        fontCache: 'global'
      },
      startup: {
        ready: () => {
          window.MathJax.startup.defaultReady()
          resolve(window.MathJax)
        }
      }
    }
    
    // Load MathJax script
    const script = document.createElement('script')
    script.src = 'https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js'
    script.async = true
    script.onload = () => {
      // MathJax will call startup.ready when ready
    }
    script.onerror = () => {
      reject(new Error('Failed to load MathJax'))
    }
    
    document.head.appendChild(script)
  })
}

const MathPreview = ({ content, inline = false }) => {
  const containerRef = useRef(null)
  const [mathJax, setMathJax] = useState(null)
  const [error, setError] = useState(null)
  
  // Load MathJax on mount
  useEffect(() => {
    loadMathJax()
      .then(mj => setMathJax(mj))
      .catch(err => {
        console.error('Failed to load MathJax:', err)
        setError('Failed to load math renderer')
      })
  }, [])
  
  // Render math when content or MathJax changes
  useEffect(() => {
    if (!mathJax || !containerRef.current || !content) return
    
    const renderMath = async () => {
      try {
        // Clear previous content
        containerRef.current.innerHTML = ''
        
        // Create element with math content
        const mathElement = document.createElement(inline ? 'span' : 'div')
        mathElement.textContent = content
        containerRef.current.appendChild(mathElement)
        
        // Typeset the math
        await mathJax.typesetPromise([containerRef.current])
      } catch (err) {
        console.error('MathJax rendering error:', err)
        setError('Failed to render equation')
      }
    }
    
    renderMath()
  }, [content, mathJax, inline])
  
  if (error) {
    return <div className="math-preview-error">{error}</div>
  }
  
  if (!content) {
    return <div className="math-preview-empty">No equation to preview</div>
  }
  
  return (
    <div 
      ref={containerRef} 
      className={`math-preview ${inline ? 'math-preview-inline' : 'math-preview-display'}`}
    />
  )
}

/**
 * Extract equations from LaTeX content
 * Requirements: 7.12
 */
export const extractEquations = (latexContent) => {
  const equations = []
  
  // Extract display equations ($$...$$)
  const displayPattern = /\$\$([\s\S]*?)\$\$/g
  let match
  
  while ((match = displayPattern.exec(latexContent)) !== null) {
    equations.push({
      type: 'display',
      content: match[1].trim(),
      start: match.index,
      end: match.index + match[0].length
    })
  }
  
  // Extract display equations (\[...\])
  const displayPattern2 = /\\\[([\s\S]*?)\\\]/g
  while ((match = displayPattern2.exec(latexContent)) !== null) {
    equations.push({
      type: 'display',
      content: match[1].trim(),
      start: match.index,
      end: match.index + match[0].length
    })
  }
  
  // Extract equation environments
  const equationPattern = /\\begin\{equation\*?\}([\s\S]*?)\\end\{equation\*?\}/g
  while ((match = equationPattern.exec(latexContent)) !== null) {
    equations.push({
      type: 'equation',
      content: match[1].trim(),
      start: match.index,
      end: match.index + match[0].length
    })
  }
  
  // Extract align environments
  const alignPattern = /\\begin\{align\*?\}([\s\S]*?)\\end\{align\*?\}/g
  while ((match = alignPattern.exec(latexContent)) !== null) {
    equations.push({
      type: 'align',
      content: match[1].trim(),
      start: match.index,
      end: match.index + match[0].length
    })
  }
  
  // Extract inline equations ($...$)
  const inlinePattern = /\$([^\$]+?)\$/g
  while ((match = inlinePattern.exec(latexContent)) !== null) {
    // Skip if part of display equation
    const isPartOfDisplay = equations.some(eq => 
      match.index >= eq.start && match.index < eq.end
    )
    
    if (!isPartOfDisplay) {
      equations.push({
        type: 'inline',
        content: match[1].trim(),
        start: match.index,
        end: match.index + match[0].length
      })
    }
  }
  
  // Sort by position
  equations.sort((a, b) => a.start - b.start)
  
  return equations
}

/**
 * Live equation preview panel
 * Shows all equations from the current document
 * Requirements: 7.12
 */
export const EquationPreviewPanel = ({ latexContent }) => {
  const [equations, setEquations] = useState([])
  
  useEffect(() => {
    if (latexContent) {
      const extracted = extractEquations(latexContent)
      setEquations(extracted)
    } else {
      setEquations([])
    }
  }, [latexContent])
  
  if (equations.length === 0) {
    return (
      <div className="equation-preview-panel">
        <div className="equation-preview-empty">
          No equations found in document
        </div>
      </div>
    )
  }
  
  return (
    <div className="equation-preview-panel">
      <h3 className="equation-preview-title">Equations ({equations.length})</h3>
      <div className="equation-list">
        {equations.map((eq, index) => (
          <div key={index} className="equation-item">
            <div className="equation-type-badge">
              {eq.type}
            </div>
            <MathPreview 
              content={eq.type === 'inline' ? `$${eq.content}$` : `$$${eq.content}$$`}
              inline={eq.type === 'inline'}
            />
          </div>
        ))}
      </div>
    </div>
  )
}

export default MathPreview
