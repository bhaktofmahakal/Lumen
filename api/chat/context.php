<?php
/**
 * Conversation Context Management API
 * Handles loading and managing conversation context
 * Requirements: 4.4
 */

require_once __DIR__ . '/../auth/AuthMiddleware.php';
require_once __DIR__ . '/../../config.php';

header('Content-Type: application/json');

// Enable CORS
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'GET') {
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
    $session_id = $_GET['session_id'] ?? null;
    $limit = isset($_GET['limit']) ? (int)$_GET['limit'] : 20;
    
    if (!$session_id) {
        http_response_code(400);
        echo json_encode(['error' => 'session_id is required']);
        exit;
    }
    
    // Verify session ownership
    $stmt = $db->prepare("
        SELECT cs.id, cs.project_id
        FROM chat_sessions cs
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
    
    // Get recent messages from short-term memory
    $context = getConversationContext($session_id, $session['project_id'], $user['user_id'], $limit);
    
    echo json_encode([
        'success' => true,
        'session_id' => $session_id,
        'project_id' => $session['project_id'],
        'context' => $context
    ]);
    
} catch (Exception $e) {
    error_log("Context retrieval error: " . $e->getMessage());
    http_response_code(500);
    echo json_encode(['error' => 'Internal server error']);
}

/**
 * Get conversation context from memory system
 */
function getConversationContext($session_id, $project_id, $user_id, $limit) {
    $ai_service_url = getenv('AI_SERVICE_URL') ?: 'http://ai-services:8000';
    
    $url = $ai_service_url . '/api/memory/context?' . http_build_query([
        'user_id' => $user_id,
        'session_id' => $session_id,
        'project_id' => $project_id,
        'limit' => $limit
    ]);
    
    $ch = curl_init($url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_TIMEOUT, 10);
    
    $response = curl_exec($ch);
    $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $error = curl_error($ch);
    curl_close($ch);
    
    if ($error || $http_code !== 200) {
        error_log("Memory service error: " . ($error ?: "HTTP $http_code"));
        return [];
    }
    
    $data = json_decode($response, true);
    return $data['context'] ?? [];
}
