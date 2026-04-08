/**
 * LaTeX Auto-completion for CodeMirror 6
 * Provides AI-powered and context-aware suggestions
 * Requirements: 7.2
 */

import { autocompletion } from '@codemirror/autocomplete'

/**
 * LaTeX command completions
 * Organized by category for better suggestions
 */
const latexCommands = {
  // Document structure
  structure: [
    { label: '\\documentclass', type: 'keyword', info: 'Document class declaration' },
    { label: '\\usepackage', type: 'keyword', info: 'Import package' },
    { label: '\\begin', type: 'keyword', info: 'Begin environment' },
    { label: '\\end', type: 'keyword', info: 'End environment' },
    { label: '\\title', type: 'keyword', info: 'Document title' },
    { label: '\\author', type: 'keyword', info: 'Document author' },
    { label: '\\date', type: 'keyword', info: 'Document date' },
    { label: '\\maketitle', type: 'keyword', info: 'Generate title' },
  ],
  
  // Sectioning
  sections: [
    { label: '\\part', type: 'keyword', info: 'Part heading' },
    { label: '\\chapter', type: 'keyword', info: 'Chapter heading' },
    { label: '\\section', type: 'keyword', info: 'Section heading' },
    { label: '\\subsection', type: 'keyword', info: 'Subsection heading' },
    { label: '\\subsubsection', type: 'keyword', info: 'Subsubsection heading' },
    { label: '\\paragraph', type: 'keyword', info: 'Paragraph heading' },
    { label: '\\subparagraph', type: 'keyword', info: 'Subparagraph heading' },
  ],
  
  // Text formatting
  formatting: [
    { label: '\\textbf', type: 'keyword', info: 'Bold text' },
    { label: '\\textit', type: 'keyword', info: 'Italic text' },
    { label: '\\texttt', type: 'keyword', info: 'Typewriter text' },
    { label: '\\emph', type: 'keyword', info: 'Emphasized text' },
    { label: '\\underline', type: 'keyword', info: 'Underlined text' },
    { label: '\\textsc', type: 'keyword', info: 'Small caps' },
  ],
  
  // Math commands
  math: [
    { label: '\\frac', type: 'function', info: 'Fraction' },
    { label: '\\sqrt', type: 'function', info: 'Square root' },
    { label: '\\sum', type: 'function', info: 'Summation' },
    { label: '\\int', type: 'function', info: 'Integral' },
    { label: '\\prod', type: 'function', info: 'Product' },
    { label: '\\lim', type: 'function', info: 'Limit' },
    { label: '\\infty', type: 'constant', info: 'Infinity symbol' },
    { label: '\\partial', type: 'function', info: 'Partial derivative' },
    { label: '\\nabla', type: 'function', info: 'Nabla/gradient' },
  ],
  
  // Greek letters
  greek: [
    { label: '\\alpha', type: 'constant', info: 'Greek letter alpha' },
    { label: '\\beta', type: 'constant', info: 'Greek letter beta' },
    { label: '\\gamma', type: 'constant', info: 'Greek letter gamma' },
    { label: '\\delta', type: 'constant', info: 'Greek letter delta' },
    { label: '\\epsilon', type: 'constant', info: 'Greek letter epsilon' },
    { label: '\\theta', type: 'constant', info: 'Greek letter theta' },
    { label: '\\lambda', type: 'constant', info: 'Greek letter lambda' },
    { label: '\\mu', type: 'constant', info: 'Greek letter mu' },
    { label: '\\pi', type: 'constant', info: 'Greek letter pi' },
    { label: '\\sigma', type: 'constant', info: 'Greek letter sigma' },
    { label: '\\omega', type: 'constant', info: 'Greek letter omega' },
  ],
  
  // Citations and references
  citations: [
    { label: '\\cite', type: 'function', info: 'Citation' },
    { label: '\\citep', type: 'function', info: 'Parenthetical citation' },
    { label: '\\citet', type: 'function', info: 'Textual citation' },
    { label: '\\ref', type: 'function', info: 'Cross-reference' },
    { label: '\\label', type: 'function', info: 'Label for reference' },
    { label: '\\bibitem', type: 'function', info: 'Bibliography item' },
    { label: '\\bibliography', type: 'function', info: 'Bibliography file' },
    { label: '\\bibliographystyle', type: 'function', info: 'Bibliography style' },
  ],
  
  // Environments
  environments: [
    { label: 'document', type: 'type', info: 'Main document environment' },
    { label: 'equation', type: 'type', info: 'Numbered equation' },
    { label: 'align', type: 'type', info: 'Aligned equations' },
    { label: 'figure', type: 'type', info: 'Figure environment' },
    { label: 'table', type: 'type', info: 'Table environment' },
    { label: 'itemize', type: 'type', info: 'Bulleted list' },
    { label: 'enumerate', type: 'type', info: 'Numbered list' },
    { label: 'abstract', type: 'type', info: 'Abstract section' },
    { label: 'theorem', type: 'type', info: 'Theorem environment' },
    { label: 'proof', type: 'type', info: 'Proof environment' },
  ],
}

/**
 * Get all LaTeX commands as flat array
 */
function getAllCommands() {
  return Object.values(latexCommands).flat()
}

/**
 * Context-aware completion function
 * Requirements: 7.2
 */
export function latexCompletions(context) {
  const word = context.matchBefore(/\\[a-zA-Z]*/)
  
  if (!word) return null
  if (word.from === word.to && !context.explicit) return null
  
  // Get all available commands
  let options = getAllCommands()
  
  // Context-aware filtering
  const line = context.state.doc.lineAt(context.pos)
  const lineText = line.text
  
  // If inside \begin{}, suggest environments
  if (lineText.includes('\\begin{') && !lineText.includes('}')) {
    options = latexCommands.environments
  }
  
  // If inside \cite{}, suggest citations (will be enhanced with project library)
  if (lineText.includes('\\cite') && lineText.includes('{') && !lineText.includes('}')) {
    // TODO: Fetch citations from project library via API
    options = [
      { label: 'smith2023', type: 'variable', info: 'Smith et al. (2023)' },
      { label: 'jones2022', type: 'variable', info: 'Jones & Brown (2022)' },
    ]
  }
  
  return {
    from: word.from,
    options: options,
    validFor: /^\\[a-zA-Z]*$/
  }
}

/**
 * Citation auto-completion from project library
 * Requirements: 7.2
 * 
 * @param {string} projectId - Current project ID
 * @param {Function} fetchCitations - Function to fetch citations from API
 */
export function createCitationCompletions(projectId, fetchCitations) {
  return async (context) => {
    const word = context.matchBefore(/\\cite[pt]?\{[^}]*/)
    
    if (!word) return null
    
    // Extract the partial citation key
    const match = word.text.match(/\\cite[pt]?\{([^}]*)/)
    if (!match) return null
    
    const partial = match[1]
    
    try {
      // Fetch citations from project library
      const citations = await fetchCitations(projectId, partial)
      
      const options = citations.map(cit => ({
        label: cit.key,
        type: 'variable',
        info: `${cit.authors} (${cit.year}): ${cit.title}`,
        apply: cit.key
      }))
      
      return {
        from: word.from + word.text.lastIndexOf('{') + 1,
        options: options,
        validFor: /^[a-zA-Z0-9_-]*$/
      }
    } catch (error) {
      console.error('Failed to fetch citations:', error)
      return null
    }
  }
}

/**
 * AI-powered completion suggestions
 * Requirements: 7.2
 * 
 * @param {Function} getAISuggestions - Function to get AI suggestions from API
 */
export function createAICompletions(getAISuggestions) {
  return async (context) => {
    // Only trigger on explicit completion request (Ctrl+Space)
    if (!context.explicit) return null
    
    // Get surrounding context
    const line = context.state.doc.lineAt(context.pos)
    const linesBefore = []
    
    // Get previous 5 lines for context
    for (let i = 1; i <= 5 && line.number - i > 0; i++) {
      const prevLine = context.state.doc.line(line.number - i)
      linesBefore.unshift(prevLine.text)
    }
    
    const contextText = linesBefore.join('\n') + '\n' + line.text.slice(0, context.pos - line.from)
    
    try {
      // Get AI suggestions based on context
      const suggestions = await getAISuggestions(contextText)
      
      if (!suggestions || suggestions.length === 0) return null
      
      const options = suggestions.map(sugg => ({
        label: sugg.text,
        type: 'text',
        info: 'AI suggestion',
        apply: sugg.text,
        boost: 99 // Prioritize AI suggestions
      }))
      
      return {
        from: context.pos,
        options: options
      }
    } catch (error) {
      console.error('Failed to get AI suggestions:', error)
      return null
    }
  }
}

/**
 * Create autocomplete extension with all completion sources
 * Requirements: 7.2
 */
export function createLatexAutocompletion(config = {}) {
  const completionSources = [latexCompletions]
  
  // Add citation completions if project ID and fetch function provided
  if (config.projectId && config.fetchCitations) {
    completionSources.push(
      createCitationCompletions(config.projectId, config.fetchCitations)
    )
  }
  
  // Add AI completions if function provided
  if (config.getAISuggestions) {
    completionSources.push(
      createAICompletions(config.getAISuggestions)
    )
  }
  
  return autocompletion({
    override: completionSources,
    activateOnTyping: true,
    maxRenderedOptions: 10
  })
}
