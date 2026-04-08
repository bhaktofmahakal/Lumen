import React, { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useProject } from '../hooks/useProjects'
import { useDocuments } from '../hooks/useDocuments'
import DocumentUpload from '../components/DocumentUpload'
import ChatInterface from '../components/ChatInterface'
import CitationLibrary from '../components/CitationLibrary'
import PDFViewer from '../components/PDFViewer'
import LaTeXEditorWithPreview from '../components/LaTeXEditorWithPreview'

export default function ProjectPage() {
  const { projectId } = useParams()
  const { data: project, isLoading: projectLoading } = useProject(projectId)
  const { data: documents, isLoading: documentsLoading } = useDocuments(projectId)
  const [activeTab, setActiveTab] = useState('documents')
  const [selectedDocument, setSelectedDocument] = useState(null)
  const [chatSessionId, setChatSessionId] = useState(null)

  if (projectLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-gray-500">Loading project...</div>
      </div>
    )
  }

  if (!project) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-gray-500">Project not found</div>
      </div>
    )
  }

  const tabs = [
    { id: 'documents', name: 'Documents', icon: '📄' },
    { id: 'chat', name: 'Chat', icon: '💬' },
    { id: 'editor', name: 'LaTeX Editor', icon: '📝' },
    { id: 'citations', name: 'Citations', icon: '📚' },
  ]

  return (
    <div className="h-screen flex flex-col">
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <h1 className="text-2xl font-bold text-gray-900">{project.name}</h1>
        {project.description && (
          <p className="text-sm text-gray-600 mt-1">{project.description}</p>
        )}
      </div>

      <div className="flex-1 flex overflow-hidden">
        <div className="w-64 bg-gray-50 border-r border-gray-200 overflow-y-auto">
          <nav className="p-4 space-y-2">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`w-full text-left px-4 py-2 rounded-lg transition-colors ${
                  activeTab === tab.id
                    ? 'bg-indigo-600 text-white'
                    : 'text-gray-700 hover:bg-gray-200'
                }`}
              >
                <span className="mr-2">{tab.icon}</span>
                {tab.name}
              </button>
            ))}
          </nav>

          {activeTab === 'documents' && (
            <div className="p-4 border-t border-gray-200">
              <h3 className="text-sm font-medium text-gray-700 mb-2">Documents</h3>
              {documentsLoading ? (
                <p className="text-sm text-gray-500">Loading...</p>
              ) : documents && documents.length > 0 ? (
                <div className="space-y-2">
                  {documents.map((doc) => (
                    <button
                      key={doc.id}
                      onClick={() => setSelectedDocument(doc)}
                      className={`w-full text-left px-3 py-2 rounded text-sm ${
                        selectedDocument?.id === doc.id
                          ? 'bg-indigo-100 text-indigo-700'
                          : 'hover:bg-gray-200'
                      }`}
                    >
                      {doc.title || doc.filename}
                    </button>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-500">No documents yet</p>
              )}
            </div>
          )}
        </div>

        <div className="flex-1 overflow-hidden">
          {activeTab === 'documents' && (
            <div className="h-full p-6 overflow-y-auto">
              <DocumentUpload projectId={projectId} />
              {selectedDocument && (
                <div className="mt-6">
                  <PDFViewer pdfUrl={selectedDocument.url} />
                </div>
              )}
            </div>
          )}

          {activeTab === 'chat' && (
            <div className="h-full">
              <ChatInterface sessionId={chatSessionId} projectId={projectId} />
            </div>
          )}

          {activeTab === 'editor' && (
            <div className="h-full">
              <LaTeXEditorWithPreview projectId={projectId} />
            </div>
          )}

          {activeTab === 'citations' && (
            <div className="h-full p-6 overflow-y-auto">
              <CitationLibrary projectId={projectId} />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
