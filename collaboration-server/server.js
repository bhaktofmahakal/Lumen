/**
 * WebSocket Server for Real-Time Collaboration
 * Requirements: 11.1, 11.2
 * 
 * This server handles Yjs document synchronization and awareness protocol
 * for real-time collaborative editing.
 */

import { WebSocketServer } from 'ws'
import * as Y from 'yjs'
import { setupWSConnection, setPersistence, docs } from 'y-websocket/bin/utils.js'
import dotenv from 'dotenv'

dotenv.config()

const PORT = process.env.COLLAB_PORT || 1234
const HOST = process.env.COLLAB_HOST || '0.0.0.0'

// Create WebSocket server
const wss = new WebSocketServer({ 
  port: PORT,
  host: HOST
})

console.log(`Collaboration WebSocket server running on ws://${HOST}:${PORT}`)

// Optional: Set up persistence to save documents
// This can be extended to save to MySQL or Redis
const persistence = {
  bindState: async (docName, ydoc) => {
    // Load document from database if exists
    console.log(`Loading document: ${docName}`)
    // TODO: Implement database loading
  },
  writeState: async (docName, ydoc) => {
    // Save document to database
    console.log(`Saving document: ${docName}`)
    // TODO: Implement database saving
  }
}

setPersistence(persistence)

// Handle WebSocket connections
wss.on('connection', (conn, req) => {
  const url = new URL(req.url, `http://${req.headers.host}`)
  const docName = url.pathname.slice(1) // Remove leading slash
  
  console.log(`New connection for document: ${docName}`)
  
  // Set up Yjs WebSocket connection
  setupWSConnection(conn, req, { docName })
  
  conn.on('close', () => {
    console.log(`Connection closed for document: ${docName}`)
  })
  
  conn.on('error', (error) => {
    console.error(`WebSocket error for document ${docName}:`, error)
  })
})

// Graceful shutdown
process.on('SIGINT', () => {
  console.log('\nShutting down collaboration server...')
  
  // Close all connections
  wss.clients.forEach(client => {
    client.close()
  })
  
  wss.close(() => {
    console.log('Server closed')
    process.exit(0)
  })
})

// Health check endpoint (for monitoring)
wss.on('listening', () => {
  console.log('Server is ready to accept connections')
  console.log(`Active documents: ${docs.size}`)
})

// Log active documents every 30 seconds
setInterval(() => {
  console.log(`Active documents: ${docs.size}`)
  console.log(`Active connections: ${wss.clients.size}`)
}, 30000)
