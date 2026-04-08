<?php
/**
 * Chat Streaming API
 * Handles streaming responses using Server-Sent Events (SSE)
 * Requirements: 4.6
 */

require_once __DIR__ . '/../auth/AuthMiddleware.php';
require_once __DIR__ . '/../../config.php';

// Set headers for SSE
header('Content-Type: text/event-stream');
header('Cache-Control: no-cache');
header('Connection: keep-alive');
header('X-Accel-Buffering: no');

// Enable CORS
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    sendSSE('error', ['error' => 'Method not allowed']);
    exit;
}

// Authenticate user
$auth = new AuthMiddleware();
$user = $auth->authenticate();

if (!$user) {
    sendSSE('error', ['error' => 'Authentication required']);
    exit;
}

// Database connection
$db = getDBConnection();

try {
    $input = json_decode(file_get_contents('php://input'), true);
    
    // Validate input
    if (!isset($input['session_id']) || !isset($input['query'])) {
        sendSSE('error', ['error' => 'session_id and query are required']);
        exit;
    }
    
    $session_id = $input['session_id'];
    $query = trim($input['query']);
    $document_ids = $input['document_ids'] ?? null;
    $use_voice_rag = $input['use_voice_rag'] ?? false;
    $verify_citations = $input['verify_citations'] ?? true;
    
    if (empty($query)) {
        sendSSE('error', ['error' => 'Query cannot be empty']);
        exit;
    }
    
    // Verify session ownership and get project_id
    $stmt = $db->prepare("
        SELECT cs.project_id, p.name as project_name
        FROM chat_sessions cs
        JOIN projects p ON cs.project_id = p.id
        WHERE cs.id = ? AND cs.user_id = ? AND cs.deleted_at IS NULL
    ");
    $stmt->bind_param('ii', $session_id, $user['user_id']);
    $stmt->execute();
    $result = $stmt->get_result();
    
    if ($result->num_rows === 0) {
        sendSSE('error', ['error' => 'Session not found']);
        exit;
    }
    
    $session = $result->fetch_assoc();
    $project_id = $session['project_id'];
    
    // Store user message
    $stmt = $db->prepare("
        INSERT INTO chat_messages (session_id, role, content)
        VALUES (?, 'user', ?)
    ");
    $stmt->bind_param('is', $session_id, $query);
    $stmt->execute();
    $user_message_id = $db->insert_id;
    
    // Send initial status
    sendSSE('status', ['message' => 'Processing query...']);
    
    // Call Python AI service for streaming RAG query
    streamRAGService($project_id, $query, $document_ids, $use_voice_rag, $verify_citations, $user['user_id'], $session_id);
    
    // Update session message count
    $stmt = $db->prepare("
        UPDATE chat_sessions 
        SET message_count = message_count + 2,
            updated_at = NOW()
        WHERE id = ?
    ");
    $stmt->bind_param('i', $session_id);
    $stmt->execute();
    
} catch (Exception $e) {
    error_log("Chat streaming error: " . $e->getMessage());
    sendSSE('error', ['error' => 'Internal server error']);
}

/**
 * Send Server-Sent Event
 */
function sendSSE($type, $data) {
    echo "event: $type\n";
    echo "data: " . json_encode($data) . "\n\n";
    
    // Flush output buffer
    if (ob_get_level() > 0) {
        ob_flush();
    }
    flush();
}

/**
 * Stream RAG service response
 */
function streamRAGService($project_id, $query, $document_ids, $use_voice_rag, $verify_citations, $user_id, $session_id) {
    global $db;
    
    $ai_service_url = getenv('AI_SERVICE_URL') ?: 'http://ai-services:8000';
    
    $payload = [
        'query' => $query,
        'project_id' => (string)$project_id,
        'document_ids' => $document_ids,
        'use_voice_rag' => $use_voice_rag,
        'verify_citations' => $verify_citations,
        'session_id' => (string)$session_id,
        'user_id' => (string)$user_id
    ];
    
    $ch = curl_init($ai_service_url . '/api/rag/query/stream');
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($payload));
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'Content-Type: application/json'
    ]);
    curl_setopt($ch, CURLOPT_TIMEOUT, 120); // 2 minute timeout
    
    // Stream response
    $response_text = '';
    $citations = [];
    $metadata = [];
    
    curl_setopt($ch, CURLOPT_WRITEFUNCTION, function($ch, $data) use (&$response_text, &$citations, &$metadata) {
        $lines = explode("\n", $data);
        
        foreach ($lines as $line) {
            $line = trim($line);
            if (empty($line)) continue;
            
            $event = json_decode($line, true);
            if (!$event) continue;
            
            $type = $event['type'] ?? 'unknown';
            
            switch ($type) {
                case 'status':
                    sendSSE('status', ['message' => $event['message']]);
                    break;
                    
                case 'retrieval_complete':
                    sendSSE('retrieval', [
                        'document_count' => $event['document_count'],
                        'metadata' => $event['metadata']
                    ]);
                    break;
                    
                case 'token':
                    $response_text .= $event['content'];
                    sendSSE('token', ['content' => $event['content']]);
                    break;
                    
                case 'citations':
                    $citations = $event['citations'];
                    sendSSE('citations', ['citations' => $citations]);
                    break;
                    
                case 'verification':
                    sendSSE('verification', ['verification' => $event['verification']]);
                    break;
                    
                case 'complete':
                    $metadata = [
                        'model' => $event['model'],
                        'input_tokens' => $event['input_tokens'],
                        'output_tokens' => $event['output_tokens'],
                        'cost' => $event['cost']
                    ];
                    sendSSE('complete', $metadata);
                    break;
                    
                case 'error':
                    sendSSE('error', ['error' => $event['error']]);
                    break;
            }
        }
        
        return strlen($data);
    });
    
    curl_exec($ch);
    $error = curl_error($ch);
    curl_close($ch);
    
    if ($error) {
        error_log("RAG streaming error: " . $error);
        sendSSE('error', ['error' => $error]);
        return;
    }
    
    // Store assistant message in database
    if (!empty($response_text)) {
        $citations_json = json_encode($citations);
        $metadata_json = json_encode($metadata);
        
        $stmt = $db->prepare("
            INSERT INTO chat_messages (session_id, role, content, citations, metadata)
            VALUES (?, 'assistant', ?, ?, ?)
        ");
        $stmt->bind_param('isss', $session_id, $response_text, $citations_json, $metadata_json);
        $stmt->execute();
    }
}
