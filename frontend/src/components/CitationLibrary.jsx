import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { citationsApi } from '../api/citations'

export default function CitationLibrary({ projectId }) {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedFormat, setSelectedFormat] = useState('APA')
  const queryClient = useQueryClient()

  const { data: citations, isLoading } = useQuery({
    queryKey: ['citations', projectId],
    queryFn: () => citationsApi.getAll(projectId),
    enabled: !!projectId,
  })

  const deleteCitation = useMutation({
    mutationFn: (citationId) => citationsApi.delete(citationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['citations', projectId] })
    },
  })

  const exportCitations = useMutation({
    mutationFn: (format) => citationsApi.export(projectId, format),
    onSuccess: (data) => {
      const blob = new Blob([data], { type: 'text/plain' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `citations.${selectedFormat.toLowerCase()}`
      a.click()
    },
  })

  const filteredCitations = citations?.filter(citation =>
    citation.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    citation.authors?.toLowerCase().includes(searchQuery.toLowerCase())
  ) || []

  const formatCitation = (citation, format) => {
    // Simple formatting - in production, use a proper citation library
    switch (format) {
      case 'APA':
        return `${citation.authors} (${citation.year}). ${citation.title}. ${citation.journal || citation.publisher}.`
      case 'MLA':
        return `${citation.authors}. "${citation.title}." ${citation.journal || citation.publisher}, ${citation.year}.`
      case 'Chicago':
        return `${citation.authors}. "${citation.title}." ${citation.journal || citation.publisher} (${citation.year}).`
      case 'IEEE':
        return `${citation.authors}, "${citation.title}," ${citation.journal || citation.publisher}, ${citation.year}.`
      default:
        return citation.title
    }
  }

  if (isLoading) {
    return <div className="text-center py-8 text-gray-500">Loading citations...</div>
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Citation Library</h2>
        <div className="flex space-x-2">
          <select
            value={selectedFormat}
            onChange={(e) => setSelectedFormat(e.target.value)}
            className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="APA">APA</option>
            <option value="MLA">MLA</option>
            <option value="Chicago">Chicago</option>
            <option value="IEEE">IEEE</option>
          </select>
          <button
            onClick={() => exportCitations.mutate(selectedFormat)}
            className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 text-sm"
          >
            Export
          </button>
        </div>
      </div>

      <input
        type="text"
        placeholder="Search citations..."
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
      />

      {filteredCitations.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <p>No citations found</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredCitations.map((citation) => (
            <div key={citation.id} className="bg-white p-4 rounded-lg shadow">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="font-medium text-gray-900">{citation.title}</h3>
                  <p className="text-sm text-gray-600 mt-1">{citation.authors}</p>
                  <p className="text-sm text-gray-500 mt-1">
                    {citation.journal || citation.publisher} • {citation.year}
                  </p>
                  <div className="mt-3 p-3 bg-gray-50 rounded text-sm font-mono">
                    {formatCitation(citation, selectedFormat)}
                  </div>
                  {citation.doi && (
                    <p className="text-sm text-indigo-600 mt-2">
                      DOI: {citation.doi}
                    </p>
                  )}
                </div>
                <div className="ml-4 flex space-x-2">
                  <button
                    onClick={() => {
                      // Edit citation
                      console.log('Edit citation:', citation.id)
                    }}
                    className="text-indigo-600 hover:text-indigo-800 text-sm"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => {
                      if (window.confirm('Delete this citation?')) {
                        deleteCitation.mutate(citation.id)
                      }
                    }}
                    className="text-red-600 hover:text-red-800 text-sm"
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
