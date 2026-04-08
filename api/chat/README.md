# Chat Interface and API Endpoints

This module implements the chat interface and API endpoints for the AI Research Copilot platform, providing multi-document chat with RAG-powered responses, streaming support, and conversation context management.

## Requirements Implemented

- **Requirement 4.1**: AI-Powered Chat Interface with Agentic Retrieval
- **Requirement 4.2**: Citation-Backed AI Responses
- **Requirement 4.3**: Multi-Document Semantic Search
- **Requirement 4.4**: Conversation Context Management
- **Requirement 4.6**: Streaming Responses
- **Requirement 4.7**: Follow-up Question Handling
- **Requirement 4.10**: Image Upload for Questions

## API Endpoints

### 1. Session Management (`sessions.php`)

#### Create Session
```http
POST /api/chat/sessions
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "project_id": 123,
  "title": "Research Discussion"
}
```

**Response:**
```json
{
  "success": true,
  "session": {
    "id": 456,
    "project_id": 123,
    "user_id": 789,
    "title": "Research Discussion",
    "message_count": 0,
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-15T10:30:00Z"
  }
}
```

#### List Sessions
```http
GET /api/chat/sessions?project_id=123
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "success": true,
  "sessions": [
    {
      "id": 456,
      "project_id": 123,
      "title": "Research Discussion",
      "message_count": 10,
      "created_at": "2025-01-15T10:30:00Z",
      "updated_at": "2025-01-15T11:45:00Z",
      "project_name": "My Research Project"
    }
  ],
  "count": 1
}
```

#### Get Session with Messages
```http
GET /api/chat/sessions/456
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "success": true,
  "session": {
    "id": 456,
    "project_id": 123,
    "title": "Research Discussion",
    "message_count": 2,
    "messages": [
      {
        "id": 1,
        "role": "user",
        "content": "What is machine learning?",
        "citations": null,
        "metadata": null,
        "created_at": "2025-01-15T10:31:00Z"
      },
      {
        "id": 2,
        "role": "assistant",
        "content": "Machine learning is a subset of AI [1].",
        "citations": [
          {
            "document_id": "doc_123",
            "document_title": "Introduction to ML",
            "page_number": 5,
            "inline_marker": "[1]"
          }
        ],
        "metadata": {
          "model": "gemini-1.5-flash",
          "total_time": 2.5,
          "cost": 0.001
        },
        "created_at": "2025-01-15T10:31:05Z"
      }
    ]
  }
}
```

#### Delete Session
```http
DELETE /api/chat/sessions/456
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "success": true,
  "message": "Session deleted successfully"
}
```

### 2. Chat Query (`query.php`)

#### Submit Query
```http
POST /api/chat/query
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "session_id": 456,
  "query": "What are the key findings in transformer architectures?",
  "document_ids": ["doc_123", "doc_456"],
  "use_voice_rag": false,
  "verify_citations": true
}
```

**Response:**
```json
{
  "success": true,
  "message_id": 789,
  "response": "Transformer architectures introduced self-attention mechanisms [1] which enable parallel processing [2].",
  "citations": [
    {
      "document_id": "doc_123",
      "document_title": "Attention Is All You Need",
      "authors": ["Vaswani et al."],
      "page_number": 3,
      "inline_marker": "[1]",
      "text_excerpt": "The Transformer model architecture relies entirely on self-attention..."
    },
    {
      "document_id": "doc_456",
      "document_title": "BERT: Pre-training of Deep Bidirectional Transformers",
      "page_number": 7,
      "inline_marker": "[2]",
      "text_excerpt": "Unlike recurrent models, transformers allow for parallel computation..."
    }
  ],
  "metadata": {
    "model": "gemini-1.5-flash",
    "total_time": 3.2,
    "input_tokens": 1500,
    "output_tokens": 250,
    "cost": 0.0015,
    "retrieval_metadata": {
      "method": "agentic",
      "sub_queries": ["transformer architecture", "self-attention mechanism"],
      "total_candidates": 25,
      "final_results": 10
    },
    "verification": {
      "total_citations": 2,
      "verified_citations": 2,
      "accuracy_score": 1.0
    }
  }
}
```

### 3. Streaming Query (`stream.php`)

#### Submit Streaming Query
```http
POST /api/chat/stream
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "session_id": 456,
  "query": "Explain neural networks",
  "use_voice_rag": true
}
```

**Response (Server-Sent Events):**
```
event: status
data: {"message":"Processing query..."}

event: status
data: {"message":"Retrieving relevant documents..."}

event: retrieval
data: {"document_count":5,"metadata":{"method":"voice_rag","fast_latency":0.8,"confidence":0.85}}

event: status
data: {"message":"Generating response..."}

event: token
data: {"content":"Neural networks are "}

event: token
data: {"content":"computational models inspired by "}

event: token
data: {"content":"biological neural networks [1]."}

event: citations
data: {"citations":[{"document_id":"doc_123","inline_marker":"[1]"}]}

event: complete
data: {"model":"gemini-1.5-flash","input_tokens":1200,"output_tokens":180,"cost":0.001}
```

### 4. Conversation Context (`context.php`)

#### Get Conversation Context
```http
GET /api/chat/context?session_id=456&limit=20
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "success": true,
  "session_id": 456,
  "project_id": 123,
  "context": [
    {
      "id": "mem_123",
      "score": 0.95,
      "messages": [
        {"role": "user", "content": "What is deep learning?"},
        {"role": "assistant", "content": "Deep learning is..."}
      ],
      "metadata": {
        "timestamp": "2025-01-15T10:30:00Z",
        "session_id": "456"
      }
    }
  ]
}
```

### 5. Image Upload (`upload-image.php`)

#### Upload Image for OCR
```http
POST /api/chat/upload-image
Authorization: Bearer <jwt_token>
Content-Type: multipart/form-data

image: <file>
session_id: 456
query: "What does this diagram show?"
```

**Response:**
```json
{
  "success": true,
  "extracted_text": "Neural Network Architecture\nInput Layer -> Hidden Layers -> Output Layer",
  "combined_query": "What does this diagram show?\n\n[Image content]: Neural Network Architecture\nInput Layer -> Hidden Layers -> Output Layer",
  "message": "Image processed successfully"
}
```

## Python AI Service Endpoints

### RAG Query (`ai-services/chat_api.py`)

#### Execute RAG Query
```http
POST http://ai-services:8000/api/rag/query
Content-Type: application/json

{
  "query": "What is machine learning?",
  "project_id": "123",
  "document_ids": ["doc_123"],
  "use_voice_rag": false,
  "verify_citations": true,
  "session_id": "456",
  "user_id": "789"
}
```

#### Execute Streaming RAG Query
```http
POST http://ai-services:8000/api/rag/query/stream
Content-Type: application/json

{
  "query": "Explain transformers",
  "project_id": "123",
  "use_voice_rag": true
}
```

### OCR Service (`ai-services/ocr_service.py`)

#### Extract Text from Image
```http
POST http://ai-services:8000/api/ocr/extract
Content-Type: application/json

{
  "image_base64": "<base64_encoded_image>",
  "mime_type": "image/jpeg"
}
```

**Response:**
```json
{
  "text": "Extracted text from image",
  "confidence": 0.92
}
```

### Memory Context (`ai-services/memory_api.py`)

#### Get Conversation Context
```http
GET http://ai-services:8000/api/memory/context?user_id=789&session_id=456&project_id=123&limit=20
```

## Architecture

### Request Flow

1. **User submits query** → PHP endpoint (`query.php` or `stream.php`)
2. **PHP validates** session ownership and stores user message
3. **PHP calls Python AI service** → RAG query endpoint
4. **Python loads context** from memory system (Mem0)
5. **Python executes RAG** → Retrieval + Generation + Citation
6. **Python stores in memory** → Short-term memory (session context)
7. **Python returns response** → PHP endpoint
8. **PHP stores assistant message** with citations and metadata
9. **PHP returns to client** → JSON or SSE stream

### Integration Points

- **Database**: MySQL for session and message persistence
- **Memory System**: Mem0 with HMLR for conversation context
- **RAG System**: LlamaIndex with VoiceAgentRAG for retrieval
- **LLM Router**: LiteLLM for intelligent provider selection
- **OCR**: Tesseract for image text extraction

## Features

### 1. Session Management (Task 11.1)
- Create/get/list/delete chat sessions
- Associate sessions with projects and users
- Track message counts and timestamps
- Soft delete for data retention

### 2. RAG Integration (Task 11.2)
- Semantic search across project documents
- Query decomposition for complex questions
- Citation extraction and verification
- Cost tracking and performance metrics

### 3. Streaming Responses (Task 11.3)
- Server-Sent Events (SSE) for real-time updates
- Progressive token streaming
- Status updates during processing
- Citation streaming when available

### 4. Context Management (Task 11.4)
- Load recent messages from short-term memory
- Include conversation context in prompts
- Update memory after each exchange
- HMLR routing for intelligent retrieval

### 5. Image Upload (Task 11.5)
- Support JPEG, PNG, WebP formats
- OCR text extraction with Tesseract
- Combine image context with query
- 10MB file size limit

### 6. Follow-up Handling (Task 11.6)
- Maintain conversation context across turns
- Resolve pronouns and references
- Support clarification questions
- Context-aware response generation

## Testing

Run the test suite:
```bash
vendor/bin/phpunit tests/ChatInterfaceTest.php --testdox
```

Tests cover:
- Session creation and management
- Message storage with citations
- Conversation context retrieval
- Follow-up question handling

## Database Schema

### chat_sessions
```sql
CREATE TABLE chat_sessions (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    project_id BIGINT UNSIGNED NOT NULL,
    user_id BIGINT UNSIGNED NOT NULL,
    title VARCHAR(255) NULL,
    message_count INT UNSIGNED DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### chat_messages
```sql
CREATE TABLE chat_messages (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    session_id BIGINT UNSIGNED NOT NULL,
    role ENUM('user', 'assistant', 'system') NOT NULL,
    content TEXT NOT NULL,
    citations JSON NULL,
    metadata JSON NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
);
```

## Configuration

### Environment Variables

```env
# AI Service URL
AI_SERVICE_URL=http://ai-services:8000

# Database
DB_HOST=mysql
DB_PORT=3306
DB_NAME=ai_research_copilot
DB_USER=root
DB_PASSWORD=secret

# Redis (for memory and caching)
REDIS_HOST=redis
REDIS_PORT=6379
```

## Error Handling

All endpoints return consistent error responses:

```json
{
  "error": "Error message",
  "details": "Additional details (optional)"
}
```

HTTP Status Codes:
- `200 OK`: Success
- `201 Created`: Resource created
- `400 Bad Request`: Invalid input
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Access denied
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

## Performance

- **Query Response Time**: < 5 seconds for 100 documents
- **Streaming Latency**: < 1 second for cached queries (VoiceAgentRAG)
- **Context Loading**: < 500ms for 20 messages
- **Image OCR**: < 3 seconds for standard images

## Security

- JWT authentication required for all endpoints
- Session ownership verification
- Project access control via RBAC
- Input validation and sanitization
- SQL injection prevention (prepared statements)
- File type and size validation for uploads

## Future Enhancements

- WebSocket support for bidirectional streaming
- Multi-modal support (audio, video)
- Real-time collaboration on chat sessions
- Export chat history to PDF/Markdown
- Advanced search within chat history
- Chat session templates
