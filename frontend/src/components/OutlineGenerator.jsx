/**
 * Outline Generator Component
 * Requirements: 9.4
 */

import React, { useState } from 'react';
import './OutlineGenerator.css';

const OutlineGenerator = ({ projectId, userId, documents, onOutlineGenerated }) => {
  const [researchTopic, setResearchTopic] = useState('');
  const [documentType, setDocumentType] = useState('article');
  const [selectedDocuments, setSelectedDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [generatedOutline, setGeneratedOutline] = useState(null);

  const documentTypes = [
    { value: 'article', label: 'Research Article' },
    { value: 'thesis', label: 'PhD Thesis' },
    { value: 'dissertation', label: 'Dissertation' },
    { value: 'conference_paper', label: 'Conference Paper' }
  ];

  const handleDocumentToggle = (documentId) => {
    setSelectedDocuments(prev => {
      if (prev.includes(documentId)) {
        return prev.filter(id => id !== documentId);
      } else {
        return [...prev, documentId];
      }
    });
  };

  const handleGenerateOutline = async () => {
    if (!researchTopic.trim()) {
      setError('Please enter a research topic');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response = await fetch('/api/latex/templates/outline/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          research_topic: researchTopic,
          project_id: projectId,
          user_id: userId,
          document_ids: selectedDocuments.length > 0 ? selectedDocuments : null,
          document_type: documentType
        })
      });

      if (!response.ok) {
        throw new Error('Failed to generate outline');
      }

      const data = await response.json();
      setGeneratedOutline(data.outline);

      if (onOutlineGenerated) {
        onOutlineGenerated(data.outline);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const renderOutlineSection = (section, level = 0) => {
    const indent = level * 20;

    return (
      <div key={section.title} className="outline-section" style={{ marginLeft: `${indent}px` }}>
        <div className="outline-section-header">
          <span className="outline-level">
            {level === 0 ? '§' : level === 1 ? '§§' : '§§§'}
          </span>
          <h4 className={`outline-title level-${level}`}>{section.title}</h4>
        </div>
        {section.description && (
          <p className="outline-description">{section.description}</p>
        )}
        {section.subsections && section.subsections.length > 0 && (
          <div className="outline-subsections">
            {section.subsections.map(subsection => renderOutlineSection(subsection, level + 1))}
          </div>
        )}
      </div>
    );
  };

  const handleCopyLatex = () => {
    if (generatedOutline && generatedOutline.latex_content) {
      navigator.clipboard.writeText(generatedOutline.latex_content);
      alert('LaTeX structure copied to clipboard!');
    }
  };

  const handleUseOutline = () => {
    if (generatedOutline && onOutlineGenerated) {
      onOutlineGenerated(generatedOutline);
    }
  };

  return (
    <div className="outline-generator">
      <div className="outline-generator-header">
        <h2>Generate Document Outline</h2>
        <p className="subtitle">
          Create a structured outline based on your research topic and uploaded documents
        </p>
      </div>

      <div className="outline-generator-form">
        <div className="form-group">
          <label htmlFor="research-topic">Research Topic *</label>
          <textarea
            id="research-topic"
            value={researchTopic}
            onChange={(e) => setResearchTopic(e.target.value)}
            placeholder="Describe your research topic in detail..."
            rows={4}
            disabled={loading}
          />
        </div>

        <div className="form-group">
          <label htmlFor="document-type">Document Type</label>
          <select
            id="document-type"
            value={documentType}
            onChange={(e) => setDocumentType(e.target.value)}
            disabled={loading}
          >
            {documentTypes.map(type => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </div>

        {documents && documents.length > 0 && (
          <div className="form-group">
            <label>Source Documents (Optional)</label>
            <p className="help-text">
              Select documents to use as context for outline generation
            </p>
            <div className="document-list">
              {documents.map(doc => (
                <label key={doc.document_id} className="document-checkbox">
                  <input
                    type="checkbox"
                    checked={selectedDocuments.includes(doc.document_id)}
                    onChange={() => handleDocumentToggle(doc.document_id)}
                    disabled={loading}
                  />
                  <span className="document-name">{doc.title || doc.filename}</span>
                </label>
              ))}
            </div>
          </div>
        )}

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        <button
          className="button primary generate-button"
          onClick={handleGenerateOutline}
          disabled={loading || !researchTopic.trim()}
        >
          {loading ? 'Generating Outline...' : 'Generate Outline'}
        </button>
      </div>

      {generatedOutline && (
        <div className="outline-result">
          <div className="outline-result-header">
            <h3>Generated Outline</h3>
            <div className="outline-actions">
              <button
                className="button secondary"
                onClick={handleCopyLatex}
              >
                Copy LaTeX
              </button>
              <button
                className="button primary"
                onClick={handleUseOutline}
              >
                Use This Outline
              </button>
            </div>
          </div>

          <div className="outline-content">
            <div className="outline-metadata">
              <p><strong>Topic:</strong> {generatedOutline.research_topic}</p>
              {generatedOutline.source_document_ids && generatedOutline.source_document_ids.length > 0 && (
                <p><strong>Based on:</strong> {generatedOutline.source_document_ids.length} document(s)</p>
              )}
            </div>

            <div className="outline-structure">
              {generatedOutline.outline_structure.map(section => renderOutlineSection(section))}
            </div>

            {generatedOutline.latex_content && (
              <div className="latex-preview">
                <h4>LaTeX Structure</h4>
                <pre className="latex-code">{generatedOutline.latex_content}</pre>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default OutlineGenerator;
