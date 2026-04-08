/**
 * LaTeX Language Support for CodeMirror 6
 * Provides syntax highlighting for LaTeX commands and environments
 * Requirements: 7.1
 */

import { StreamLanguage } from '@codemirror/language'

const latexMode = {
  startState: function() {
    return {
      inMathMode: false,
      inComment: false,
      inEnvironment: null
    }
  },
  
  token: function(stream, state) {
    // Handle comments
    if (stream.match(/^%.*$/)) {
      return 'comment'
    }
    
    // Handle math mode delimiters
    if (stream.match(/^\$\$/)) {
      state.inMathMode = !state.inMathMode
      return 'keyword'
    }
    
    if (stream.match(/^\$/)) {
      state.inMathMode = !state.inMathMode
      return 'keyword'
    }
    
    // Handle LaTeX commands
    if (stream.match(/^\\[a-zA-Z@]+/)) {
      const cmd = stream.current()
      
      // Document class and packages
      if (['\\documentclass', '\\usepackage', '\\RequirePackage'].includes(cmd)) {
        return 'keyword strong'
      }
      
      // Sectioning commands
      if (['\\part', '\\chapter', '\\section', '\\subsection', '\\subsubsection', 
           '\\paragraph', '\\subparagraph'].includes(cmd)) {
        return 'heading'
      }
      
      // Math commands
      if (['\\frac', '\\sqrt', '\\sum', '\\int', '\\prod', '\\lim', '\\infty',
           '\\alpha', '\\beta', '\\gamma', '\\delta', '\\epsilon', '\\theta',
           '\\lambda', '\\mu', '\\pi', '\\sigma', '\\omega'].includes(cmd)) {
        return 'atom'
      }
      
      // Text formatting
      if (['\\textbf', '\\textit', '\\texttt', '\\emph', '\\underline'].includes(cmd)) {
        return 'strong'
      }
      
      // Citations and references
      if (['\\cite', '\\ref', '\\label', '\\bibitem', '\\bibliography'].includes(cmd)) {
        return 'link'
      }
      
      return 'keyword'
    }
    
    // Handle environment names
    if (stream.match(/^\\begin\{([^}]+)\}/)) {
      state.inEnvironment = RegExp.$1
      return 'keyword strong'
    }
    
    if (stream.match(/^\\end\{([^}]+)\}/)) {
      state.inEnvironment = null
      return 'keyword strong'
    }
    
    // Handle braces
    if (stream.match(/^[{}]/)) {
      return 'bracket'
    }
    
    // Handle brackets
    if (stream.match(/^[\[\]]/)) {
      return 'bracket'
    }
    
    // Math mode content
    if (state.inMathMode) {
      if (stream.match(/^[0-9]+/)) {
        return 'number'
      }
      if (stream.match(/^[a-zA-Z]+/)) {
        return 'variable-2'
      }
    }
    
    // Default: advance one character
    stream.next()
    return null
  }
}

export const latex = StreamLanguage.define(latexMode)
