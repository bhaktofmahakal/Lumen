# 🎓 AI Research Copilot

[![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://reactjs.org)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![PHP](https://img.shields.io/badge/PHP-8.3-777BB4?style=for-the-badge&logo=php&logoColor=white)](https://php.net)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://typescriptlang.org)

---

<div align="center">
  <img 
    src="./images/main.png" 
    alt="AI Research Copilot - Complete Academic Research Workflow"
    width="100%" 
    style="max-width: 1100px; border-radius: 16px; box-shadow: 0 12px 40px rgba(0,0,0,0.15); margin: 20px 0;"
  >
  
  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=22&duration=3000&pause=1000&color=58A6FF&center=true&vCenter=true&width=700&lines=AI+Research+Copilot;Multi-Agent+AI+System;Complete+Research+Workflow;Reading+%E2%86%92+Understanding+%E2%86%92+Writing" alt="Typing Animation">
</div>

---

**AI Research Copilot** is a comprehensive academic research platform powered by multi-agent AI systems. Built on a modern microservices architecture, it transforms the research workflow from document reading through understanding to academic writing, featuring advanced RAG, real-time collaboration, mobile apps, and an open-source stack.

---

## ✨ Key Highlights

� **Multi-Agent AI System** – Specialized agents (Researcher, Writer, Citation, Reviewer) orchestrated with LangGraph  
📚 **Advanced RAG 2.0** – Semantic search with Qdrant vector store and citation-backed answers  
✍️ **Collaborative LaTeX Editor** – Real-time editing with Yjs, AI assistance, and live preview  
� **Native Mobile Apps** – iOS/Android apps with offline mode and biometric auth  
� **PWA Support** – Installable web app with offline capabilities  
🔄 **Real-time Collaboration** – Multi-user editing with version control and commenting  
� **API Ecosystem** – REST API, webhooks, SDKs (Python, JavaScript, R)  
☁️ **Cloud Integrations** – Google Drive, Dropbox, OneDrive sync  
🌍 **Internationalization** – 8+ languages with voice input/output  
� **Enterprise Security** – ACE framework, RBAC, GDPR compliance  

---

## 📸 Application Screenshots

### 💬 AI Chat Interface
<div align="center">
  <img src="./images/light.png" alt="AI Chat Interface" width="80%" style="border-radius: 12px; border: 1px solid #ddd;" />
</div>

---

### 📝 LaTeX Editor
<div align="center">
  <img src="./images/latex.png" alt="LaTeX Editor" width="80%" style="border-radius: 12px; border: 1px solid #ddd;" />
</div>

---

### 📊 Admin Dashboard
<div align="center">
  <img src="./images/admin.png" alt="Admin Dashboard" width="80%" style="border-radius: 12px; border: 1px solid #ddd;" />
</div>

---

### 🌓 Dark Mode Interface
<div align="center">
  <img src="./images/dark.png" alt="Dark Mode" width="80%" style="border-radius: 12px; border: 1px solid #333;" />
</div>


---

## 🚀 Core Features

### 🤖 Multi-Agent AI System
- **Specialized Agents**: Researcher, Writer, Citation, and Reviewer agents with distinct roles
- **LangGraph Orchestration**: Stateful workflows with conditional routing and human-in-the-loop
- **Memory System**: Mem0-powered memory with hierarchical multi-level retention (HMLR)
- **Intelligent LLM Routing**: LiteLLM for cost-optimized routing across Gemini, Groq, and Ollama
- **Agent Context Engine (ACE)**: Self-improving agents with feedback loops and safety validation

### 📚 Document Processing & RAG
- **PDF Upload & Analysis**: Drag-and-drop upload with OCR, equation extraction, and metadata parsing
- **Semantic Search**: Qdrant vector store with sentence-transformers embeddings
- **Citation Management**: Automatic citation extraction and formatting (APA, MLA, Chicago, IEEE)
- **Multi-Document Chat**: Query across multiple documents with citation-backed answers
- **External Import**: Zotero, Mendeley, and DOI-based import

### ✍️ LaTeX Editor & Writing
- **CodeMirror 6 Editor**: Syntax highlighting, auto-completion, and error detection
- **Real-time Preview**: Live PDF compilation with MathJax rendering
- **AI Writing Assistance**: Outline generation, section writing, and grammar checking
- **Template Library**: Pre-built templates for articles, theses, reports, and presentations
- **Version Control**: Git-like versioning with diff viewer and rollback

### 🔄 Real-time Collaboration
- **Yjs CRDT**: Conflict-free collaborative editing with WebSocket sync
- **Commenting System**: Inline comments with threading and mentions
- **Presence Awareness**: See who's editing in real-time
- **Offline Sync**: Queue changes offline and sync when reconnected

### 📱 Mobile Applications
- **React Native + Expo**: Native iOS and Android apps
- **Biometric Auth**: Face ID, Touch ID, and fingerprint support
- **Offline Mode**: Queue uploads and messages for later sync
- **Camera Scanning**: Scan documents directly from mobile camera
- **Push Notifications**: Real-time alerts for collaboration and updates

### 🌐 PWA & Offline Support
- **Installable Web App**: Add to home screen on any device
- **Service Worker**: Offline caching for core functionality
- **Background Sync**: Automatic sync when connection restored
- **Push Notifications**: Web push for desktop and mobile browsers

### 🔌 API Ecosystem
- **REST API**: OpenAPI/Swagger documented endpoints
- **Webhooks**: Event notifications for integrations
- **SDKs**: Official clients for Python, JavaScript, and R
- **Rate Limiting**: Configurable quotas and throttling
- **API Keys**: Secure authentication with JWT tokens

### ☁️ Cloud Storage Integrations
- **Google Drive**: Two-way sync with OAuth authentication
- **Dropbox**: Automatic backup and file sharing
- **OneDrive**: Enterprise integration with Microsoft 365
- **Export Formats**: PDF, LaTeX, Word, Markdown, BibTeX

### 🌍 Accessibility & i18n
- **Voice Input/Output**: Speech recognition and synthesis
- **Keyboard Navigation**: Full keyboard accessibility
- **Screen Reader Support**: ARIA labels and semantic HTML
- **8+ Languages**: English, Spanish, French, German, Hindi, Chinese, Japanese, Arabic
- **RTL Support**: Right-to-left languages fully supported

### � Analytics & Subscriptions
- **Usage Analytics**: Track document uploads, chat queries, and LaTeX compilations
- **Institutional Dashboards**: Multi-user analytics for organizations
- **Subscription Tiers**: Free, Premium, and Institutional plans
- **Stripe Integration**: Secure payment processing with webhooks
- **Quota Management**: Per-tier limits with usage tracking

### 🔒 Security & Compliance
- **ACE Framework**: AI safety with prompt validation and output filtering
- **Encryption**: AES-256 at rest, TLS 1.3 in transit
- **Authentication**: Email/password, OAuth (Google), SSO, 2FA
- **RBAC**: Role-based access control for projects and documents
- **Compliance**: GDPR, CCPA, FERPA, SOC 2 ready
- **Data Privacy**: User data export and deletion on request

---

## 🧰 Tech Stack

### Frontend
- **React 18** – Modern UI with hooks and concurrent features
- **Vite** – Lightning-fast build tool and dev server
- **TypeScript** – Type-safe JavaScript
- **TailwindCSS** – Utility-first CSS framework
- **Zustand** – Lightweight state management
- **CodeMirror 6** – Advanced code editor
- **Yjs** – CRDT for real-time collaboration
- **PDF.js** – Client-side PDF rendering

### Backend
- **PHP 8.3+** – Web application and REST API
- **FastAPI** – Python async API for AI services
- **MySQL 8.0+** – Relational database
- **Redis** – Caching and session management
- **Nginx** – Reverse proxy with SSL/TLS

### AI/ML Stack
- **LangGraph** – Multi-agent orchestration with stateful workflows
- **Mem0** – Memory system with hierarchical retention
- **LiteLLM** – Unified LLM interface with intelligent routing
- **LlamaIndex** – RAG framework with agentic retrieval
- **Qdrant** – Vector database for semantic search
- **sentence-transformers** – Text embeddings (384d)

### LLM Providers
- **Gemini API** – Google's multimodal LLM
- **Groq API** – Ultra-fast inference
- **Ollama** – Local LLM hosting (optional)

### Infrastructure
- **Docker** – Containerization
- **Docker Compose** – Multi-container orchestration
- **S3/Object Storage** – Document storage
- **WebSocket** – Real-time collaboration server

### Mobile
- **React Native** – Cross-platform mobile framework
- **Expo** – Development and build tooling
- **Expo SecureStore** – Encrypted credential storage
- **Expo Local Authentication** – Biometric auth

---

## 🏗️ Architecture

The platform uses a **microservices architecture** with Docker Compose orchestration:

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Layer                          │
│  React Web App  │  React Native Mobile  │  PWA              │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway Layer                         │
│              Nginx (Load Balancing + SSL/TLS)               │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                   Application Layer                          │
│    PHP Backend (Web + API)  │  Python FastAPI (AI Services) │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    AI Agent Layer                            │
│  LangGraph │ Mem0 │ LiteLLM │ LlamaIndex │ ACE │ EffGen    │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                   LLM Provider Layer                         │
│         Gemini API  │  Groq API  │  Ollama (Local)          │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                      Data Layer                              │
│    MySQL  │  Redis  │  Qdrant  │  S3/Object Storage        │
└─────────────────────────────────────────────────────────────┘
```

### Service Endpoints

| Service | Port | Description |
|---------|------|-------------|
| Nginx (HTTP) | 80 | Web interface |
| Nginx (HTTPS) | 443 | Secure web interface |
| Python AI Service | 8000 | AI/ML API endpoints |
| MySQL | 3306 | Database |
| Redis | 6379 | Cache/Sessions |
| Qdrant | 6333 | Vector store |
| Ollama | 11434 | Local LLM (optional) |
| Collaboration Server | 1234 | WebSocket (Yjs) |

---

## 🚀 Quick Start

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- 8GB RAM minimum (16GB recommended)
- 20GB disk space

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/ai-research-copilot.git
cd ai-research-copilot
```

### 2. Configure Environment
```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API keys
# Required: GEMINI_API_KEY, GROQ_API_KEY
# Optional: OPENAI_API_KEY, ANTHROPIC_API_KEY
```

### 3. Run Setup Script

**Linux/Mac:**
```bash
chmod +x scripts/setup-infrastructure.sh
./scripts/setup-infrastructure.sh
```

**Windows (PowerShell):**
```powershell
.\scripts\setup-infrastructure.ps1
```

### 4. Start Services
```bash
docker-compose up -d
```

### 5. Verify Installation
```bash
# Check all services are healthy
curl http://localhost:8000/health/detailed
```

### 6. Access Application
- **Web App**: https://localhost
- **API Docs**: http://localhost:8000/docs
- **Admin Panel**: https://localhost/admin

### Default Credentials
- **Email**: admin@example.com
- **Password**: admin123 (change immediately!)

---

## 📱 Mobile App Setup

### Prerequisites
- Node.js 18+
- Expo CLI: `npm install -g expo-cli`

### Installation
```bash
cd mobile
npm install
npm start
```

### Run on Device
```bash
# iOS
npm run ios

# Android
npm run android
```

See [mobile/README.md](mobile/README.md) for detailed instructions.

---

## 🔧 Configuration

### Environment Variables

```env
# Database
DB_HOST=mysql
DB_PORT=3306
DB_NAME=ai_research
DB_USER=root
DB_PASSWORD=your_secure_password

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=your_secure_password

# LLM API Keys (at least one required)
GEMINI_API_KEY=your_gemini_key
GROQ_API_KEY=your_groq_key
OPENAI_API_KEY=your_openai_key  # Optional
ANTHROPIC_API_KEY=your_anthropic_key  # Optional

# Ollama (for local LLM)
OLLAMA_HOST=http://ollama:11434

# JWT
JWT_SECRET=your_secure_jwt_secret

# Stripe (for subscriptions)
STRIPE_SECRET_KEY=your_stripe_key
STRIPE_WEBHOOK_SECRET=your_webhook_secret

# S3/Object Storage (optional)
S3_BUCKET=your_bucket
S3_REGION=us-east-1
S3_ACCESS_KEY=your_access_key
S3_SECRET_KEY=your_secret_key

# OAuth (optional)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
```

---

## 📖 API Documentation

The platform provides a comprehensive REST API with OpenAPI/Swagger documentation.

### API Endpoints

**Authentication**
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login with email/password
- `POST /api/auth/oauth-google` - Google OAuth login
- `POST /api/auth/verify-email` - Verify email address

**Projects**
- `GET /api/projects` - List user projects
- `POST /api/projects` - Create new project
- `GET /api/projects/{id}` - Get project details
- `PUT /api/projects/{id}` - Update project
- `DELETE /api/projects/{id}` - Delete project

**Documents**
- `POST /api/documents/upload` - Upload PDF document
- `GET /api/documents/{id}` - Get document details
- `DELETE /api/documents/{id}` - Delete document
- `GET /api/documents/{id}/download` - Download document

**Chat**
- `POST /api/chat/query` - Send chat message
- `GET /api/chat/sessions` - List chat sessions
- `GET /api/chat/sessions/{id}` - Get session messages
- `POST /api/chat/stream` - Stream chat response

**LaTeX**
- `POST /api/latex/compile` - Compile LaTeX document
- `GET /api/latex/templates` - List templates
- `POST /api/latex/export` - Export to PDF/Word

**Citations**
- `GET /api/citations` - List citations
- `POST /api/citations` - Add citation
- `PUT /api/citations/{id}` - Update citation
- `DELETE /api/citations/{id}` - Delete citation

### API Authentication

All API requests require authentication via JWT token:

```bash
# Get token
curl -X POST http://localhost/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}'

# Use token
curl -X GET http://localhost/api/projects \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### SDKs

Official SDKs are available for:
- **Python**: `pip install research-copilot`
- **JavaScript**: `npm install @research-copilot/sdk`
- **R**: `install.packages("researchCopilot")`

See [sdks/](sdks/) for documentation.

---

## 🧪 Testing

### Backend Tests (PHP)
```bash
# Run all tests
docker-compose exec php-backend vendor/bin/phpunit

# Run specific test
docker-compose exec php-backend vendor/bin/phpunit tests/AuthenticationTest.php
```

### AI Services Tests (Python)
```bash
# Run all tests
docker-compose exec python-ai-service pytest

# Run with coverage
docker-compose exec python-ai-service pytest --cov=. --cov-report=html

# Run property-based tests
docker-compose exec python-ai-service pytest tests/test_agent_properties.py
```

### Frontend Tests (React)
```bash
cd frontend
npm test

# Run with coverage
npm test -- --coverage
```

---

## 🔒 Security

### Authentication Methods
- Email/password with bcrypt hashing
- OAuth 2.0 (Google, GitHub)
- SSO (SAML 2.0)
- Two-factor authentication (TOTP)
- Biometric (mobile apps)

### Encryption
- **At Rest**: AES-256 encryption for sensitive data
- **In Transit**: TLS 1.3 for all connections
- **Database**: Encrypted MySQL connections

### Compliance
- **GDPR**: Data export and deletion on request
- **CCPA**: California privacy compliance
- **FERPA**: Educational records protection
- **SOC 2**: Security controls framework

### ACE Framework
The Agent Context Engine provides AI safety through:
- Prompt injection detection
- Output validation and filtering
- Bias detection and mitigation
- Feedback loops for continuous improvement

---

## 📊 Performance & Scalability

### Performance Targets
- **Chat Response**: <5 seconds (p95)
- **LaTeX Compilation**: <10 seconds (p95)
- **Document Upload**: <30 seconds for 50MB PDF
- **Semantic Search**: <2 seconds for 1000 documents

### Scalability
- **Current**: Supports 1,000 concurrent users
- **2030 Target**: 10,000 concurrent users
- **Horizontal Scaling**: Stateless services with load balancing
- **Database**: Read replicas and sharding ready

### Cost Optimization
- **LiteLLM Routing**: 40-60% cost savings through intelligent model selection
- **Caching**: Redis caching reduces API calls by 70%
- **CDN**: Static asset delivery optimization

---

## 🗺️ Roadmap

### 2025 Q1-Q2
- ✅ Multi-agent AI system with LangGraph
- ✅ Advanced RAG with Qdrant
- ✅ Real-time collaboration with Yjs
- ✅ Mobile apps (iOS/Android)
- ✅ PWA with offline support

### 2025 Q3-Q4
- [ ] Advanced analytics and insights
- [ ] LMS integrations (Canvas, Moodle, Blackboard)
- [ ] Notion and Obsidian sync
- [ ] GitHub integration for code documentation
- [ ] Advanced PDF annotation

### 2026+
- [ ] Multi-language expansion (20+ languages)
- [ ] Voice-first research assistant
- [ ] AR/VR research environments
- [ ] Blockchain-based citation verification
- [ ] Quantum-ready encryption

### Vision 2030
- **Users**: 1.5-3M active users
- **Revenue**: $100-200M ARR
- **Market**: Global academic research platform
- **Impact**: Transform research workflows worldwide

---

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

### Development Workflow
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Coding Standards
- **PHP**: PSR-12 coding standard
- **JavaScript/TypeScript**: ESLint + Prettier
- **Python**: PEP 8 with Black formatter
- **Commits**: Conventional Commits format

### Testing Requirements
- Unit tests for all new features
- Integration tests for API endpoints
- Property-based tests for critical logic
- Minimum 80% code coverage

### Documentation
- Update README.md for user-facing changes
- Add JSDoc/PHPDoc comments for public APIs
- Update OpenAPI spec for API changes

---

## 📞 Support & Contact

- **Documentation**: [docs.airesearchcopilot.com](https://docs.airesearchcopilot.com)
- **GitHub Issues**: [Report bugs](https://github.com/yourusername/ai-research-copilot/issues)
- **Discussions**: [Community Q&A](https://github.com/yourusername/ai-research-copilot/discussions)
- **Email**: support@airesearchcopilot.com
- **Discord**: [Join our community](https://discord.gg/airesearchcopilot)

---

## 🙏 Acknowledgments

- **LangChain Team** for LangGraph and agent orchestration
- **Mem0 Team** for memory management framework
- **Qdrant Team** for vector database
- **LiteLLM Team** for unified LLM interface
- **Open Source Community** for countless libraries and tools

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  <strong>"Transforming research from reading to writing with AI"</strong><br>
  Built with ❤️ for researchers worldwide
</p>

---

<p align="center">
  <img src="https://img.shields.io/badge/Made%20with-❤️-red?style=for-the-badge" alt="Made with Love" />
  <img src="https://img.shields.io/badge/AI%20Powered-🤖-blue?style=for-the-badge" alt="AI Powered" />
  <img src="https://img.shields.io/badge/Open%20Source-💎-green?style=for-the-badge" alt="Open Source" />
</p>
