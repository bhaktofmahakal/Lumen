/**
 * Unit tests for LaTeX Editor Component
 * Requirements: 7.1, 20.3
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import LaTeXEditor from '../LaTeXEditor'

describe('LaTeXEditor Component', () => {
  let mockOnCompile
  let mockOnContentChange
  
  beforeEach(() => {
    mockOnCompile = vi.fn()
    mockOnContentChange = vi.fn()
    
    // Mock localStorage
    global.localStorage = {
      getItem: vi.fn(),
      setItem: vi.fn(),
      removeItem: vi.fn(),
      clear: vi.fn()
    }
  })
  
  afterEach(() => {
    vi.clearAllMocks()
  })
  
  it('should render editor with initial content', () => {
    const initialContent = '\\documentclass{article}\\begin{document}Test\\end{document}'
    
    render(
      <LaTeXEditor 
        initialContent={initialContent}
        onCompile={mockOnCompile}
        onContentChange={mockOnContentChange}
        projectId="test-project"
      />
    )
    
    expect(screen.getByText('LaTeX Source')).toBeInTheDocument()
    expect(screen.getByText(/Lines:/)).toBeInTheDocument()
    expect(screen.getByText(/Characters:/)).toBeInTheDocument()
  })
  
  it('should display line numbers', () => {
    render(
      <LaTeXEditor 
        initialContent="Line 1\nLine 2\nLine 3"
        projectId="test-project"
      />
    )
    
    // CodeMirror 6 should render line numbers
    const editor = document.querySelector('.cm-editor')
    expect(editor).toBeInTheDocument()
    
    const lineNumbers = document.querySelector('.cm-lineNumbers')
    expect(lineNumbers).toBeInTheDocument()
  })
  
  it('should support code folding', () => {
    const content = `\\begin{document}
\\section{Introduction}
Content here
\\end{document}`
    
    render(
      <LaTeXEditor 
        initialContent={content}
        projectId="test-project"
      />
    )
    
    // Check for fold gutter
    const foldGutter = document.querySelector('.cm-foldGutter')
    expect(foldGutter).toBeInTheDocument()
  })
  
  it('should call onContentChange when content changes', async () => {
    const user = userEvent.setup()
    
    render(
      <LaTeXEditor 
        initialContent=""
        onContentChange={mockOnContentChange}
        projectId="test-project"
      />
    )
    
    const editor = document.querySelector('.cm-content')
    await user.click(editor)
    await user.keyboard('\\section{Test}')
    
    await waitFor(() => {
      expect(mockOnContentChange).toHaveBeenCalled()
    })
  })
  
  it('should trigger auto-save after 30 seconds', async () => {
    vi.useFakeTimers()
    
    render(
      <LaTeXEditor 
        initialContent="Test content"
        onContentChange={mockOnContentChange}
        projectId="test-project"
      />
    )
    
    // Simulate content change
    const editor = document.querySelector('.cm-content')
    await userEvent.click(editor)
    await userEvent.keyboard(' modified')
    
    // Fast-forward 30 seconds
    vi.advanceTimersByTime(30000)
    
    await waitFor(() => {
      expect(localStorage.setItem).toHaveBeenCalledWith(
        'latex_backup_test-project',
        expect.any(String)
      )
    })
    
    vi.useRealTimers()
  })
  
  it('should display auto-save status', () => {
    render(
      <LaTeXEditor 
        initialContent="Test"
        projectId="test-project"
      />
    )
    
    const saveStatus = screen.getByText(/Saved/)
    expect(saveStatus).toBeInTheDocument()
  })
  
  it('should handle Ctrl+S keyboard shortcut for compilation', async () => {
    const user = userEvent.setup()
    
    render(
      <LaTeXEditor 
        initialContent="\\documentclass{article}\\begin{document}Test\\end{document}"
        onCompile={mockOnCompile}
        projectId="test-project"
      />
    )
    
    const editor = document.querySelector('.cm-content')
    await user.click(editor)
    await user.keyboard('{Control>}s{/Control}')
    
    await waitFor(() => {
      expect(mockOnCompile).toHaveBeenCalled()
    })
  })
  
  it('should display correct statistics', () => {
    const content = 'Line 1\nLine 2\nLine 3'
    
    render(
      <LaTeXEditor 
        initialContent={content}
        projectId="test-project"
      />
    )
    
    expect(screen.getByText(/Lines: 3/)).toBeInTheDocument()
    expect(screen.getByText(/Characters: \d+/)).toBeInTheDocument()
    expect(screen.getByText(/Words: \d+/)).toBeInTheDocument()
  })
  
  it('should apply LaTeX syntax highlighting', () => {
    const content = '\\documentclass{article}\\section{Test}'
    
    render(
      <LaTeXEditor 
        initialContent={content}
        projectId="test-project"
      />
    )
    
    // Check that CodeMirror applied syntax highlighting classes
    const editor = document.querySelector('.cm-editor')
    expect(editor).toBeInTheDocument()
    
    // LaTeX keywords should be highlighted
    const keywords = document.querySelectorAll('.cm-keyword')
    expect(keywords.length).toBeGreaterThan(0)
  })
})
