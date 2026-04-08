import React, { useCallback, useState } from 'react'
import { useUploadDocument } from '../hooks/useDocuments'
import { useDocumentStore } from '../stores/useDocumentStore'

export default function DocumentUpload({ projectId }) {
  const uploadDocument = useUploadDocument()
  const uploadProgress = useDocumentStore((state) => state.uploadProgress)
  const [dragActive, setDragActive] = useState(false)
  const [uploadErrors, setUploadErrors] = useState({})

  const handleDrag = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }, [])

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    const files = Array.from(e.dataTransfer.files)
    handleFiles(files)
  }, [projectId])

  const handleChange = (e) => {
    const files = Array.from(e.target.files)
    handleFiles(files)
  }

  const handleFiles = async (files) => {
    const pdfFiles = files.filter(file => file.type === 'application/pdf')
    
    if (pdfFiles.length !== files.length) {
      alert('Only PDF files are supported')
    }

    for (const file of pdfFiles) {
      if (file.size > 50 * 1024 * 1024) {
        setUploadErrors(prev => ({
          ...prev,
          [file.name]: 'File size exceeds 50MB limit'
        }))
        continue
      }

      try {
        await uploadDocument.mutateAsync({ projectId, file })
        setUploadErrors(prev => {
          const { [file.name]: _, ...rest } = prev
          return rest
        })
      } catch (error) {
        setUploadErrors(prev => ({
          ...prev,
          [file.name]: error.response?.data?.message || 'Upload failed'
        }))
      }
    }
  }

  const retryUpload = async (fileName) => {
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = '.pdf'
    input.onchange = (e) => {
      const file = e.target.files[0]
      if (file && file.name === fileName) {
        handleFiles([file])
      }
    }
    input.click()
  }

  return (
    <div className="space-y-4">
      <div
        className={`relative border-2 border-dashed rounded-lg p-8 text-center ${
          dragActive ? 'border-indigo-500 bg-indigo-50' : 'border-gray-300'
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <svg
          className="mx-auto h-12 w-12 text-gray-400"
          stroke="currentColor"
          fill="none"
          viewBox="0 0 48 48"
        >
          <path
            d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
            strokeWidth={2}
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
        <div className="mt-4">
          <label htmlFor="file-upload" className="cursor-pointer">
            <span className="text-indigo-600 hover:text-indigo-500 font-medium">
              Upload files
            </span>
            <input
              id="file-upload"
              name="file-upload"
              type="file"
              className="sr-only"
              multiple
              accept=".pdf"
              onChange={handleChange}
            />
          </label>
          <span className="text-gray-500"> or drag and drop</span>
        </div>
        <p className="text-xs text-gray-500 mt-2">PDF files up to 50MB</p>
      </div>

      {Object.keys(uploadProgress).length > 0 && (
        <div className="space-y-2">
          {Object.entries(uploadProgress).map(([fileId, progress]) => (
            <div key={fileId} className="bg-white p-4 rounded-lg shadow">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">
                  {fileId.split('-')[0]}
                </span>
                <span className="text-sm text-gray-500">{progress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-indigo-600 h-2 rounded-full transition-all"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      )}

      {Object.keys(uploadErrors).length > 0 && (
        <div className="space-y-2">
          {Object.entries(uploadErrors).map(([fileName, error]) => (
            <div key={fileName} className="bg-red-50 p-4 rounded-lg">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-red-800">{fileName}</p>
                  <p className="text-sm text-red-600">{error}</p>
                </div>
                <button
                  onClick={() => retryUpload(fileName)}
                  className="text-sm text-red-600 hover:text-red-800 font-medium"
                >
                  Retry
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
