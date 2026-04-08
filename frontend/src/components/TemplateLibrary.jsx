/**
 * Template Library Component
 * Requirements: 9.1, 9.2, 9.3, 9.5
 */

import React, { useState, useEffect } from 'react';
import './TemplateLibrary.css';

const TemplateLibrary = ({ onSelectTemplate, userId, projectId }) => {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedType, setSelectedType] = useState('all');
  const [showCustomization, setShowCustomization] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [customization, setCustomization] = useState({});

  const templateTypes = [
    { value: 'all', label: 'All Templates' },
    { value: 'article', label: 'Article' },
    { value: 'thesis', label: 'Thesis' },
    { value: 'dissertation', label: 'Dissertation' },
    { value: 'conference_paper', label: 'Conference Paper' },
    { value: 'poster', label: 'Poster' },
    { value: 'presentation', label: 'Presentation' },
    { value: 'custom', label: 'Custom' }
  ];

  useEffect(() => {
    fetchTemplates();
  }, [selectedType, userId]);

  const fetchTemplates = async () => {
    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams({
        user_id: userId,
        include_builtin: 'true',
        include_custom: 'true'
      });

      if (selectedType !== 'all') {
        params.append('template_type', selectedType);
      }

      const response = await fetch(`/api/latex/templates/list?${params}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch templates');
      }

      const data = await response.json();
      setTemplates(data.templates || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleTemplateClick = async (template) => {
    try {
      // Fetch full template content
      const response = await fetch(`/api/latex/templates/${template.template_id}?user_id=${userId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch template details');
      }

      const data = await response.json();
      setSelectedTemplate(data.template);

      // Initialize customization with default settings
      if (data.template.default_settings) {
        setCustomization(data.template.default_settings);
      }

      setShowCustomization(true);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleCustomizationChange = (key, value) => {
    setCustomization(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const handleApplyTemplate = async () => {
    try {
      // Customize template with user settings
      const response = await fetch('/api/latex/templates/customize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          template_id: selectedTemplate.template_id,
          user_id: userId,
          customization: customization
        })
      });

      if (!response.ok) {
        throw new Error('Failed to customize template');
      }

      const data = await response.json();
      
      // Pass customized content to parent
      if (onSelectTemplate) {
        onSelectTemplate({
          ...selectedTemplate,
          content: data.content,
          customization: customization
        });
      }

      setShowCustomization(false);
    } catch (err) {
      setError(err.message);
    }
  };

  const renderCustomizationOptions = () => {
    if (!selectedTemplate || !selectedTemplate.customization_options) {
      return null;
    }

    const options = selectedTemplate.customization_options;

    return (
      <div className="customization-options">
        {Object.entries(options).map(([key, values]) => (
          <div key={key} className="customization-field">
            <label>{key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</label>
            <select
              value={customization[key] || ''}
              onChange={(e) => handleCustomizationChange(key, e.target.value)}
            >
              {values.map(value => (
                <option key={value} value={value}>{value}</option>
              ))}
            </select>
          </div>
        ))}
      </div>
    );
  };

  if (loading) {
    return <div className="template-library loading">Loading templates...</div>;
  }

  if (error) {
    return (
      <div className="template-library error">
        <p>Error: {error}</p>
        <button onClick={fetchTemplates}>Retry</button>
      </div>
    );
  }

  return (
    <div className="template-library">
      <div className="template-header">
        <h2>LaTeX Templates</h2>
        <div className="template-filters">
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="template-type-filter"
          >
            {templateTypes.map(type => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="template-grid">
        {templates.map(template => (
          <div
            key={template.template_id}
            className={`template-card ${template.is_builtin ? 'builtin' : 'custom'}`}
            onClick={() => handleTemplateClick(template)}
          >
            <div className="template-card-header">
              <h3>{template.name}</h3>
              {template.is_builtin && <span className="badge builtin">Built-in</span>}
              {template.journal_name && <span className="badge journal">{template.journal_name}</span>}
              {template.conference_name && <span className="badge conference">{template.conference_name}</span>}
            </div>
            <p className="template-description">{template.description}</p>
            <div className="template-meta">
              <span className="template-type">{template.template_type.replace(/_/g, ' ')}</span>
              <span className="template-usage">Used {template.usage_count} times</span>
            </div>
          </div>
        ))}
      </div>

      {templates.length === 0 && (
        <div className="no-templates">
          <p>No templates found for the selected type.</p>
        </div>
      )}

      {showCustomization && selectedTemplate && (
        <div className="customization-modal">
          <div className="customization-modal-content">
            <div className="customization-modal-header">
              <h3>Customize Template: {selectedTemplate.name}</h3>
              <button
                className="close-button"
                onClick={() => setShowCustomization(false)}
              >
                ×
              </button>
            </div>

            <div className="customization-modal-body">
              <div className="template-preview">
                <h4>Template Description</h4>
                <p>{selectedTemplate.description}</p>
                {selectedTemplate.placeholder_content && (
                  <div className="placeholder-guidance">
                    <h4>Guidance</h4>
                    <p>{selectedTemplate.placeholder_content}</p>
                  </div>
                )}
              </div>

              <div className="customization-form">
                <h4>Customization Options</h4>
                {renderCustomizationOptions()}
              </div>
            </div>

            <div className="customization-modal-footer">
              <button
                className="button secondary"
                onClick={() => setShowCustomization(false)}
              >
                Cancel
              </button>
              <button
                className="button primary"
                onClick={handleApplyTemplate}
              >
                Apply Template
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TemplateLibrary;
