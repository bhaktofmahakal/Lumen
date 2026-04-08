<?php
/**
 * Chat Query API
 * Handles chat queries with RAG system integration
 * Requirements: 4.1, 4.2, 4.3
 */

require_once __DIR__ . '/../auth/AuthMiddleware.php';
require_once __DIR__ . '/../../config.php';

header('Content-Type: application/json');

// Enable CORS
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
    exit;
}

// Authenticate user
$auth = new AuthMiddleware();
$user = $auth->requireAuth();

// Database connection
$db = getDBConnection();

try {
    $input = json_decode(file_get_contents('php://input'), true);
    
    // Validate input
    if (!isset($input['session_id']) || !isset($input['query'])) {
        http_response_code(400);
        echo json_encode(['error' => 'session_id and query are required']);
        exit;
    }
    
    $session_id = $input['session_id'];
    $query = trim($input['query']);
    $document_ids = $input['document_ids'] ?? null;
    $use_voice_rag = $input['use_voice_rag'] ?? false;
    $verify_citations = $input['verify_citations'] ?? true;
    
    if (empty($query)) {
        http_response_code(400);
        echo json_encode(['error' => 'Query cannot be empty']);
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
        http_response_code(404);
        echo json_encode(['error' => 'Session not found']);
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
    
    // Call Python AI service for RAG query
    $rag_response = callRAGService($project_id, $query, $document_ids, $use_voice_rag, $verify_citations);
    
    if (!$rag_response['success']) {
        http_response_code(500);
        echo json_encode([
            'error' => 'Failed to generate response',
            'details' => $rag_response['error'] ?? 'Unknown error'
        ]);
        exit;
    }
    
    $response_text = $rag_response['data']['response'];
    $citations = $rag_response['data']['citations'] ?? [];
    $metadata = [
        'model' => $rag_response['data']['model'] ?? null,
        'total_time' => $rag_response['data']['total_time'] ?? null,
        'input_tokens' => $rag_response['data']['input_tokens'] ?? null,
        'output_tokens' => $rag_response['data']['output_tokens'] ?? null,
        'cost' => $rag_response['data']['cost'] ?? null,
        'retrieval_metadata' => $rag_response['data']['retrieval_metadata'] ?? null,
        'verification' => $rag_response['data']['verification'] ?? null
    ];
    
    // Store assistant message
    $citations_json = json_encode($citations);
    $metadata_json = json_encode($metadata);
    
    $stmt = $db->prepare("
        INSERT INTO chat_messages (session_id, role, content, citations, metadata)
        VALUES (?, 'assistant', ?, ?, ?)
    ");
    $stmt->bind_param('isss', $session_id, $response_text, $citations_json, $metadata_json);
    $stmt->execute();
    $assistant_message_id = $db->insert_id();
    
    // Update session message count and timestamp
    $stmt = $db->prepare("
        UPDATE chat_sessions 
        SET message_count = message_count + 2,
            updated_at = NOW()
        WHERE id = ?
    ");
    $stmt->bind_param('i', $session_id);
    $stmt->execute();
    
    // Return response
    echo json_encode([
        'success' => true,
        'message_id' => $assistant_message_id,
        'response' => $response_text,
        'citations' => $citations,
        'metadata' => $metadata
    ]);
    
} catch (Exception $e) {
    error_log("Chat query error: " . $e->getMessage());
    http_response_code(500);
    echo json_encode(['error' => 'Internal server error']);
}

/**
 * Call Python AI service for RAG query
 */
function callRAGService($project_id, $query, $document_ids, $use_voice_rag, $verify_citations) {
    $ai_service_url = getenv('AI_SERVICE_URL') ?: 'http://ai-services:8000';
    
    $payload = [
        'query' => $query,
        'project_id' => (string)$project_id,
        'document_ids' => $document_ids,
        'use_voice_rag' => $use_voice_rag,
        'verify_citations' => $verify_citations
    ];
    
    $ch = curl_init($ai_service_url . '/api/rag/query');
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($payload));
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'Content-Type: application/json'
    ]);
    curl_setopt($ch, CURLOPT_TIMEOUT, 60); // 60 second timeout
    
    $response = curl_exec($ch);
    $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $error = curl_error($ch);
    curl_close($ch);
    
    if ($error) {
        error_log("RAG service error: " . $error);
        return ['success' => false, 'error' => $error];
    }
    
    if ($http_code !== 200) {
        error_log("RAG service returned HTTP $http_code: " . $response);
        return ['success' => false, 'error' => "HTTP $http_code"];
    }
    
    $data = json_decode($response, true);
    
    if (!$data) {
        error_log("Failed to decode RAG service response");
        return ['success' => false, 'error' => 'Invalid response format'];
    }
    
    return ['success' => true, 'data' => $data];
}
