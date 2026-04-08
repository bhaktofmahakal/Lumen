/**
 * PDF Viewer Component using PDF.js
 * Requirements: 7.8
 */

import React, { useEffect, useRef, useState } from 'react'
import * as pdfjsLib from 'pdfjs-dist'
import './PDFViewer.css'

// Configure PDF.js worker
pdfjsLib.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.js`

const PDFViewer = ({ pdfUrl, onPageChange, syncScroll = false }) => {
  const canvasRef = useRef(null)
  const containerRef = useRef(null)
  const [pdfDoc, setPdfDoc] = useState(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(0)
  const [scale, setScale] = useState(1.0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  
  // Load PDF document
  useEffect(() => {
    if (!pdfUrl) return
    
    setLoading(true)
    setError(null)
    
    const loadPDF = async () => {
      try {
        const loadingTask = pdfjsLib.getDocument(pdfUrl)
        const pdf = await loadingTask.promise
        
        setPdfDoc(pdf)
        setTotalPages(pdf.numPages)
        setCurrentPage(1)
        setLoading(false)
      } catch (err) {
        console.error('Error loading PDF:', err)
        setError('Failed to load PDF')
        setLoading(false)
      }
    }
    
    loadPDF()
    
    return () => {
      if (pdfDoc) {
        pdfDoc.destroy()
      }
    }
  }, [pdfUrl])
  
  // Render current page
  useEffect(() => {
    if (!pdfDoc || !canvasRef.current) return
    
    const renderPage = async () => {
      try {
        const page = await pdfDoc.getPage(currentPage)
        const canvas = canvasRef.current
        const context = canvas.getContext('2d')
        
        const viewport = page.getViewport({ scale })
        
        canvas.height = viewport.height
        canvas.width = viewport.width
        
        const renderContext = {
          canvasContext: context,
          viewport: viewport
        }
        
        await page.render(renderContext).promise
        
        // Notify parent of page change
        if (onPageChange) {
          onPageChange(currentPage, totalPages)
        }
      } catch (err) {
        console.error('Error rendering page:', err)
        setError('Failed to render page')
      }
    }
    
    renderPage()
  }, [pdfDoc, currentPage, scale])
  
  // Navigation functions
  const goToPage = (pageNum) => {
    if (pageNum >= 1 && pageNum <= totalPages) {
      setCurrentPage(pageNum)
    }
  }
  
  const nextPage = () => goToPage(currentPage + 1)
  const prevPage = () => goToPage(currentPage - 1)
  
  // Zoom functions
  const zoomIn = () => setScale(prev => Math.min(prev + 0.25, 3.0))
  const zoomOut = () => setScale(prev => Math.max(prev - 0.25, 0.5))
  const resetZoom = () => setScale(1.0)
  
  if (loading) {
    return (
      <div className="pdf-viewer-container">
        <div className="pdf-loading">Loading PDF...</div>
      </div>
    )
  }
  
  if (error) {
    return (
      <div className="pdf-viewer-container">
        <div className="pdf-error">{error}</div>
      </div>
    )
  }
  
  if (!pdfUrl) {
    return (
      <div className="pdf-viewer-container">
        <div className="pdf-placeholder">
          <p>No PDF to display</p>
          <p className="pdf-placeholder-hint">Compile your LaTeX document to see the preview</p>
        </div>
      </div>
    )
  }
  
  return (
    <div className="pdf-viewer-container" ref={containerRef}>
      <div className="pdf-toolbar">
        <div className="pdf-nav-controls">
          <button 
            onClick={prevPage} 
            disabled={currentPage <= 1}
            className="pdf-btn"
          >
            ← Previous
          </button>
          <span className="pdf-page-info">
            Page {currentPage} of {totalPages}
          </span>
          <button 
            onClick={nextPage} 
            disabled={currentPage >= totalPages}
            className="pdf-btn"
          >
            Next →
          </button>
        </div>
        
        <div className="pdf-zoom-controls">
          <button onClick={zoomOut} className="pdf-btn">−</button>
          <span className="pdf-zoom-level">{Math.round(scale * 100)}%</span>
          <button onClick={zoomIn} className="pdf-btn">+</button>
          <button onClick={resetZoom} className="pdf-btn">Reset</button>
        </div>
      </div>
      
      <div className="pdf-canvas-container">
        <canvas ref={canvasRef} className="pdf-canvas" />
      </div>
    </div>
  )
}

export default PDFViewer
