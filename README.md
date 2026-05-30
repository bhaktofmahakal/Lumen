# AI Research Copilot (Lumen)

[![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://reactjs.org)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![PHP](https://img.shields.io/badge/PHP-8.3-777BB4?style=for-the-badge&logo=php&logoColor=white)](https://php.net)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)

AI Research Copilot (Lumen is the repository name) is a multi-service research workspace for academic researchers and research teams. It helps teams ingest papers, ask questions with citations, and draft LaTeX documents with AI assistance. This repository contains the full stack: a React web app (PWA-enabled), a PHP API, Python AI services, and a Yjs collaboration server.

## Product capabilities
- **PDF ingestion with OCR** using PyMuPDF/PyPDF and Tesseract-backed fallbacks.
- **Retrieval-augmented chat** over uploaded documents with a Qdrant vector store.
- **LangGraph multi-agent workflow** for research → drafting → citation → review.
- **LaTeX authoring** via API endpoints (generate, bibliography, compile) and a CodeMirror-based editor with MathJax preview.
- **Real-time collaboration** with Yjs and a dedicated WebSocket server.
- **Project, document, and citation management** with JWT auth and RBAC enforcement.
- **PWA-ready frontend** with Workbox caching for faster repeat visits.

## Architecture

| Service | Responsibility | Tech |
| --- | --- | --- |
| frontend | Web UI, LaTeX editor, PWA | React, Vite, CodeMirror, MathJax, Yjs |
| api | Auth, projects, documents, citations, LaTeX endpoints | PHP 8.3, MySQL, Redis |
| ai-services | RAG, OCR, agent orchestration, LLM routing | FastAPI, LangGraph, Qdrant, LiteLLM |
| collaboration-server | Realtime document sync | Node.js, y-websocket |
| infra | Reverse proxy + data stores | Nginx, Docker Compose, MySQL, Redis, Qdrant |

## Local development
1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```
2. Set the required secrets in `.env` (at least one LLM key such as `GEMINI_API_KEY` or `GROQ_API_KEY`, plus JWT/DB/Redis passwords).
3. Start services:
   ```bash
   ./scripts/setup-infrastructure.sh
   # or: docker-compose up -d
   ```
4. Open:
   - **Web app:** http://localhost (HTTP) or https://localhost (self-signed; accept the browser warning)
   - **AI service docs:** http://localhost:8000/docs
   - **Health:** http://localhost:8000/health

Windows users can use `scripts/setup-infrastructure.ps1` for the same bootstrap flow.

## Production notes
- Replace the self-signed certificates in `nginx/ssl` with real TLS certs.
- Set `APP_ENV=production` and `APP_DEBUG=false`.
- Rotate strong secrets for DB, Redis, JWT, and OAuth client credentials.
- Persist MySQL, Redis, and Qdrant volumes and plan backup/restore.
- Scale stateless services (frontend, api, ai-services, collaboration) independently.

## API surface
- **PHP API:** `/api/auth`, `/api/projects`, `/api/documents`, `/api/chat`, `/api/citations`, `/api/latex`
- **AI service docs:** `/docs` (FastAPI schema)
- **Endpoint references:** `api/*/README.md`

## Repository layout
- `frontend/` — React + PWA web app
- `api/` — PHP REST API
- `ai-services/` — FastAPI AI services (RAG, OCR, LLM routing)
- `collaboration-server/` — Yjs WebSocket server
- `admin-panel/` — Admin UI
- `docker/`, `nginx/` — container and reverse proxy configuration

## License
MIT
