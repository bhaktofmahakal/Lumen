# AI Research Copilot - Frontend

React 18 + TypeScript frontend application for the AI Research Copilot platform.

## Features

- **Authentication**: Login, register, OAuth (Google), password reset
- **Project Management**: Create, view, update, delete projects
- **Document Upload**: Drag-and-drop PDF upload with progress tracking
- **Chat Interface**: AI-powered chat with streaming responses and citations
- **LaTeX Editor**: CodeMirror 6-based editor with real-time preview
- **Citation Library**: Manage citations with multiple format support
- **Real-time Collaboration**: Yjs-based collaborative editing (existing components)

## Tech Stack

- **React 18**: UI framework
- **Vite**: Build tool and dev server
- **TailwindCSS**: Utility-first CSS framework
- **Zustand**: State management
- **React Query**: Data fetching and caching
- **React Router**: Client-side routing
- **Axios**: HTTP client
- **CodeMirror 6**: Code editor
- **PDF.js**: PDF viewing
- **Yjs**: CRDT for collaboration

## Getting Started

### Prerequisites

- Node.js 18+ and npm

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

The app will be available at `http://localhost:5173`

### Build

```bash
npm run build
```

### Preview Production Build

```bash
npm run preview
```

## Environment Variables

Create a `.env` file in the frontend directory:

```
VITE_API_URL=http://localhost:8080
```

## Project Structure

```
frontend/
├── src/
│   ├── api/              # API client and endpoints
│   ├── components/       # Reusable components
│   ├── pages/            # Page components
│   ├── stores/           # Zustand stores
│   ├── hooks/            # Custom React hooks
│   ├── editor/           # CodeMirror extensions
│   ├── collaboration/    # Yjs collaboration components
│   ├── main.jsx          # App entry point
│   ├── App.jsx           # Main app component with routing
│   └── index.css         # Global styles
├── public/               # Static assets
├── index.html            # HTML template
├── vite.config.js        # Vite configuration
└── tailwind.config.js    # TailwindCSS configuration
```

## Key Components

### Authentication
- `Login.jsx`: Login page with email/password and OAuth
- `Register.jsx`: Registration page
- `ProtectedRoute.jsx`: Route wrapper for authenticated pages

### Dashboard
- `Dashboard.jsx`: Project list and management
- `CreateProjectModal.jsx`: Modal for creating new projects

### Project
- `ProjectPage.jsx`: Main project workspace with tabs
- `DocumentUpload.jsx`: Drag-and-drop file upload
- `ChatInterface.jsx`: AI chat with streaming
- `CitationLibrary.jsx`: Citation management
- `PDFViewer.jsx`: PDF document viewer
- `LaTeXEditorWithPreview.jsx`: LaTeX editor with preview

### State Management

- `useAuthStore`: User authentication state
- `useProjectStore`: Project data
- `useDocumentStore`: Document data and upload progress
- `useChatStore`: Chat sessions and messages

### API Hooks

- `useProjects`: Fetch and manage projects
- `useDocuments`: Fetch and upload documents
- React Query for caching and optimistic updates

## Available Scripts

- `npm run dev`: Start development server
- `npm run build`: Build for production
- `npm run preview`: Preview production build
- `npm run lint`: Run ESLint
- `npm run test`: Run tests
- `npm run test:watch`: Run tests in watch mode
