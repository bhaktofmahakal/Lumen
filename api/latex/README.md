# LaTeX API Endpoints

AI-assisted LaTeX writing and compilation endpoints.

## Endpoints

### POST /api/latex/generate

Generate LaTeX-formatted content using AI.

**Requirements:** 8.1, 8.2, 8.3, 8.4, 8.5, 8.6

**Authentication:** Required (JWT token)

**Request Body:**
```json
{
  "prompt": "Write an introduction about transformer architectures",
  "project_id": "project_123",
  "content_type": "section",
  "style": "formal",
  "document_ids": ["doc_1", "doc_2"],
  "existing_content": "\\section{Introduction}\n...",
  "session_id": "session_456"
}
```

**Fields:**
- `prompt` (required): User's writing prompt or refinement request
- `project_id` (required): Project identifier
- `content_type` (optional): Type of content - "section", "paragraph", "equation", "table", "figure" (default: "section")
- `style` (optional): Writing style - "formal", "technical", "concise" (default: "formal")
- `document_ids` (optional): Array of document IDs to use as source material for citations
- `existing_content` (optional): Existing LaTeX content for iterative refinement
- `session_id` (optional): Session identifier for context continuity

**Response:**
```json
{
  "success": true,
  "content": "\\section{Introduction}\n\nTransformer architectures \\cite{doc_1} have revolutionized...",
  "citations": [
    {
      "cite_key": "doc_1",
      "document_id": "doc_1",
      "page": 3,
      "text_excerpt": "Transformers use self-attention mechanism..."
    }
  ],
  "terminology": {
    "transformer": "Neural network architecture using self-attention"
  },
  "generation_time": 2.5
}
```

**Features:**
- **Section Generation:** Generates complete sections with proper LaTeX formatting
- **Citation Integration:** Automatically inserts citations from source documents
- **Style Customization:** Adapts writing style based on user preferences
- **Equation Generation:** Creates properly formatted LaTeX equations
- **Table/Figure Generation:** Generates LaTeX table and figure environments
- **Iterative Refinement:** Refines existing content based on feedback
- **Terminology Consistency:** Maintains consistent terminology across document

**Example Usage:**

Generate a section:
```bash
curl -X POST http://localhost/api/latex/generate \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Write a literature review on transformer architectures",
    "project_id": "project_123",
    "content_type": "section",
    "style": "formal",
    "document_ids": ["doc_1", "doc_2"]
  }'
```

Generate an equation:
```bash
curl -X POST http://localhost/api/latex/generate \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Generate the attention mechanism equation",
    "project_id": "project_123",
    "content_type": "equation",
    "style": "technical"
  }'
```

Refine existing content:
```bash
curl -X POST http://localhost/api/latex/generate \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Add more details about the attention mechanism",
    "project_id": "project_123",
    "existing_content": "\\section{Introduction}\nTransformers are neural networks...",
    "document_ids": ["doc_1"]
  }'
```

---

### POST /api/latex/bibliography

Generate BibTeX entries and formatted bibliography.

**Requirements:** 8.8

**Authentication:** Required (JWT token)

**Request Body:**
```json
{
  "citation_ids": ["doc_1", "doc_2", "doc_3"],
  "project_id": "project_123",
  "style": "APA"
}
```

**Fields:**
- `citation_ids` (required): Array of citation/document IDs
- `project_id` (required): Project identifier
- `style` (optional): Citation style - "APA", "MLA", "Chicago", "IEEE" (default: "APA")

**Response:**
```json
{
  "success": true,
  "bibtex_entries": [
    "@article{doc_1,\n  author = {Author, A.},\n  title = {Document Title},\n  journal = {Journal Name},\n  year = {2024},\n  volume = {1},\n  pages = {1--10}\n}"
  ],
  "formatted_bibliography": "Author, A. (2024). Document Title. Journal Name, 1, 1-10.\n\nAuthor, B. (2024). Another Title. Conference Proceedings, 100-110."
}
```

**Example Usage:**
```bash
curl -X POST http://localhost/api/latex/bibliography \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "citation_ids": ["doc_1", "doc_2"],
    "project_id": "project_123",
    "style": "IEEE"
  }'
```

---

### POST /api/latex/compile

Compile LaTeX document to PDF.

**Requirements:** 7.3, 7.4, 7.5

**Authentication:** Required (JWT token)

**Request Body:**
```json
{
  "content": "\\documentclass{article}\n\\begin{document}\nHello World\n\\end{document}",
  "project_id": "project_123",
  "document_id": "doc_123"
}
```

**Response:**
```json
{
  "success": true,
  "pdf_url": "/latex-output/doc_123.pdf",
  "warnings": ["Package hyperref Warning: ..."],
  "compilation_time": 1.2
}
```

**Error Response with AI Fixes:**
```json
{
  "success": false,
  "errors": [
    {
      "type": "latex_error",
      "line": 5,
      "message": "Undefined control sequence"
    }
  ],
  "ai_fixes": [
    {
      "error_type": "latex_error",
      "line": 5,
      "original_error": "Undefined control sequence",
      "suggested_fix": "\\usepackage{amsmath}",
      "explanation": "The command requires the amsmath package..."
    }
  ],
  "compilation_time": 0.8
}
```

---

## Implementation Details

### Backend Architecture

The LaTeX API consists of two layers:

1. **PHP Layer** (`api/latex/*.php`):
   - Handles authentication and authorization
   - Validates request parameters
   - Proxies requests to Python FastAPI service
   - Returns responses to frontend

2. **Python Layer** (`ai-services/latex_api.py`):
   - Implements AI writing assistance logic
   - Integrates with LLM router for content generation
   - Manages memory system for context and preferences
   - Handles LaTeX compilation with error parsing
   - Generates AI-powered error fixes

### AI Writing Assistant Features

**Context Gathering:**
- Retrieves relevant memories from short-term, long-term, and episodic layers
- Fetches source passages from uploaded documents via RAG
- Extracts terminology for consistency

**Style Customization:**
- Formal: Academic language with precise terminology
- Technical: Detailed explanations for expert readers
- Concise: Direct and brief while maintaining clarity

**Content Types:**
- **Section/Paragraph:** Structured academic writing with citations
- **Equation:** Properly formatted LaTeX math environments
- **Table:** LaTeX tabular environments with booktabs
- **Figure:** Figure environments with includegraphics

**Memory Integration:**
- Stores generated content in short-term memory for session context
- Stores terminology in long-term memory for project consistency
- Retrieves user style preferences from episodic memory

### Citation Management

- Automatically inserts `\cite{}` commands for source material
- Extracts citation metadata (document ID, page number, excerpt)
- Maintains citation integrity during refinement
- Generates BibTeX entries in multiple formats

### Error Handling

- Validates LaTeX content for security (prevents shell injection)
- Parses compilation errors with line numbers
- Generates AI-powered fix suggestions
- Provides clear error messages

---

## Testing

Run tests for LaTeX API:
```bash
cd ai-services
pytest tests/test_latex_api.py -v
```

---

## Configuration

Environment variables:
- `PYTHON_API_URL`: Python FastAPI service URL (default: http://localhost:8000)
- `REDIS_HOST`: Redis host for caching (default: localhost)
- `REDIS_PORT`: Redis port (default: 6379)

---

## Future Enhancements

- [ ] Real-time collaboration on generated content
- [ ] Multi-language content generation
- [ ] Advanced equation recognition from images
- [ ] Template-based content generation
- [ ] Citation metadata enrichment from external APIs
- [ ] Custom style guide support
- [ ] Version control for generated content
