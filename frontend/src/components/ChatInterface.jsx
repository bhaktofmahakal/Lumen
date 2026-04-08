import React, { useState, useRef, useEffect } from 'react'
import { chatApi } from '../api/chat'
import { useChatStore } from '../stores/useChatStore'

export default function ChatInterface({ sessionId, projectId }) {
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef(null)
  const messages = useChatStore((state) => state.messages)
  const addMessage = useChatStore((state) => state.addMessage)
  const updateMessage = useChatStore((state) => state.updateMessage)
  const isStreaming = useChatStore((state) => state.isStreaming)
  const setStreaming = useChatStore((state) => state.setStreaming)

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: input,
      timestamp: new Date().toISOString(),
    }

    addMessage(userMessage)
    setInput('')
    setIsLoading(true)
    setStreaming(true)

    const assistantMessage = {
      id: Date.now() + 1,
      role: 'assistant',
      content: '',
      citations: [],
      timestamp: new Date().toISOString(),
    }

    addMessage(assistantMessage)

    try {
      await chatApi.streamMessage(sessionId, input, [], (data) => {
        if (data.type === 'token') {
          updateMessage(assistantMessage.id, {
            content: (messages.find(m => m.id === assistantMessage.id)?.content || '') + data.content
          })
        } else if (data.type === 'citation') {
          updateMessage(assistantMessage.id, {
            citations: [...(messages.find(m => m.id === assistantMessage.id)?.citations || []), data.citation]
          })
        } else if (data.type === 'done') {
          setStreaming(false)
          setIsLoading(false)
        }
      })
    } catch (error) {
      console.error('Chat error:', error)
      updateMessage(assistantMessage.id, {
        content: 'Sorry, I encountered an error. Please try again.',
        error: true
      })
      setStreaming(false)
      setIsLoading(false)
    }
  }

  const handleCitationClick = (citation) => {
    // Navigate to document viewer with citation location
    console.log('Citation clicked:', citation)
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 mt-8">
            <p>Start a conversation by asking a question about your documents.</p>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-3xl rounded-lg px-4 py-2 ${
                  message.role === 'user'
                    ? 'bg-indigo-600 text-white'
                    : 'bg-gray-100 text-gray-900'
                }`}
              >
                <div className="whitespace-pre-wrap">{message.content}</div>
                {message.citations && message.citations.length > 0 && (
                  <div className="mt-2 pt-2 border-t border-gray-300 space-y-1">
                    {message.citations.map((citation, idx) => (
                      <button
                        key={idx}
                        onClick={() => handleCitationClick(citation)}
                        className="block text-sm text-indigo-600 hover:text-indigo-800 hover:underline text-left"
                      >
                        [{idx + 1}] {citation.document_title}, p. {citation.page}
                      </button>
                    ))}
                  </div>
                )}
                {message.error && (
                  <div className="mt-2 text-sm text-red-600">
                    Error: Failed to generate response
                  </div>
                )}
              </div>
            </div>
          ))
        )}
        {isStreaming && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg px-4 py-2">
              <div className="flex space-x-2">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="border-t border-gray-200 p-4">
        <form onSubmit={handleSubmit} className="flex space-x-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question about your documents..."
            disabled={isLoading}
            className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
          >
            Send
          </button>
        </form>
      </div>
    </div>
  )
}
