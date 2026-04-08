<?php
/**
 * Chat Session Management API
 * Handles create/get/list/delete session endpoints
 * Requirements: 4.1
 */

require_once __DIR__ . '/../auth/AuthMiddleware.php';
require_once __DIR__ . '/../../config.php';

header('Content-Type: application/json');

// Enable CORS
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

// Authenticate user
$auth = new AuthMiddleware();
$user = $auth->requireAuth();

// Database connection
$db = getDBConnection();

$method = $_SERVER['REQUEST_METHOD'];
$path_parts = explode('/', trim($_SERVER['PATH_INFO'] ?? '', '/'));

try {
    switch ($method) {
        case 'POST':
            // Create new chat session
            createSession($db, $user);
            break;
            
        case 'GET':
            if (empty($path_parts[0])) {
                // List all sessions for user
                listSessions($db, $user);
            } else {
                // Get specific session
                getSession($db, $user, $path_parts[0]);
            }
            break;
            
        case 'DELETE':
            if (!empty($path_parts[0])) {
                // Delete specific session
                deleteSession($db, $user, $path_parts[0]);
            } else {
                http_response_code(400);
                echo json_encode(['error' => 'Session ID required']);
            }
            break;
            
        default:
            http_response_code(405);
            echo json_encode(['error' => 'Method not allowed']);
    }
} catch (Exception $e) {
    error_log("Chat session error: " . $e->getMessage());
    http_response_code(500);
    echo json_encode(['error' => 'Internal server error']);
}

/**
 * Create new chat session
 */
function createSession($db, $user) {
    $input = json_decode(file_get_contents('php://input'), true);
    
    if (!isset($input['project_id'])) {
        http_response_code(400);
        echo json_encode(['error' => 'project_id is required']);
        return;
    }
    
    $project_id = $input['project_id'];
    $title = $input['title'] ?? null;
    
    // Verify user has access to project
    $stmt = $db->prepare("
        SELECT p.id 
        FROM projects p
        LEFT JOIN project_collaborators pc ON p.id = pc.project_id
        WHERE p.id = ? 
        AND (p.user_id = ? OR (pc.user_id = ? AND pc.accepted_at IS NOT NULL))
        AND p.deleted_at IS NULL
    ");
    $stmt->bind_param('iii', $project_id, $user['user_id'], $user['user_id']);
    $stmt->execute();
    $result = $stmt->get_result();
    
    if ($result->num_rows === 0) {
        http_response_code(403);
        echo json_encode(['error' => 'Access denied to project']);
        return;
    }
    
    // Create session
    $stmt = $db->prepare("
        INSERT INTO chat_sessions (project_id, user_id, title)
        VALUES (?, ?, ?)
    ");
    $stmt->bind_param('iis', $project_id, $user['user_id'], $title);
    
    if ($stmt->execute()) {
        $session_id = $db->insert_id;
        
        // Fetch created session
        $stmt = $db->prepare("
            SELECT id, project_id, user_id, title, message_count, created_at, updated_at
            FROM chat_sessions
            WHERE id = ?
        ");
        $stmt->bind_param('i', $session_id);
        $stmt->execute();
        $result = $stmt->get_result();
        $session = $result->fetch_assoc();
        
        http_response_code(201);
        echo json_encode([
            'success' => true,
            'session' => $session
        ]);
    } else {
        http_response_code(500);
        echo json_encode(['error' => 'Failed to create session']);
    }
}

/**
 * List all sessions for user
 */
function listSessions($db, $user) {
    $project_id = $_GET['project_id'] ?? null;
    
    if ($project_id) {
        // List sessions for specific project
        $stmt = $db->prepare("
            SELECT cs.id, cs.project_id, cs.user_id, cs.title, cs.message_count, 
                   cs.created_at, cs.updated_at, p.name as project_name
            FROM chat_sessions cs
            JOIN projects p ON cs.project_id = p.id
            WHERE cs.project_id = ? 
            AND cs.user_id = ?
            AND cs.deleted_at IS NULL
            ORDER BY cs.updated_at DESC
        ");
        $stmt->bind_param('ii', $project_id, $user['user_id']);
    } else {
        // List all sessions for user
        $stmt = $db->prepare("
            SELECT cs.id, cs.project_id, cs.user_id, cs.title, cs.message_count, 
                   cs.created_at, cs.updated_at, p.name as project_name
            FROM chat_sessions cs
            JOIN projects p ON cs.project_id = p.id
            WHERE cs.user_id = ?
            AND cs.deleted_at IS NULL
            ORDER BY cs.updated_at DESC
        ");
        $stmt->bind_param('i', $user['user_id']);
    }
    
    $stmt->execute();
    $result = $stmt->get_result();
    
    $sessions = [];
    while ($row = $result->fetch_assoc()) {
        $sessions[] = $row;
    }
    
    echo json_encode([
        'success' => true,
        'sessions' => $sessions,
        'count' => count($sessions)
    ]);
}

/**
 * Get specific session with messages
 */
function getSession($db, $user, $session_id) {
    // Fetch session
    $stmt = $db->prepare("
        SELECT cs.id, cs.project_id, cs.user_id, cs.title, cs.message_count, 
               cs.created_at, cs.updated_at, p.name as project_name
        FROM chat_sessions cs
        JOIN projects p ON cs.project_id = p.id
        WHERE cs.id = ? 
        AND cs.user_id = ?
        AND cs.deleted_at IS NULL
    ");
    $stmt->bind_param('ii', $session_id, $user['user_id']);
    $stmt->execute();
    $result = $stmt->get_result();
    
    if ($result->num_rows === 0) {
        http_response_code(404);
        echo json_encode(['error' => 'Session not found']);
        return;
    }
    
    $session = $result->fetch_assoc();
    
    // Fetch messages
    $stmt = $db->prepare("
        SELECT id, role, content, citations, metadata, created_at
        FROM chat_messages
        WHERE session_id = ?
        ORDER BY created_at ASC
    ");
    $stmt->bind_param('i', $session_id);
    $stmt->execute();
    $result = $stmt->get_result();
    
    $messages = [];
    while ($row = $result->fetch_assoc()) {
        // Decode JSON fields
        $row['citations'] = $row['citations'] ? json_decode($row['citations'], true) : null;
        $row['metadata'] = $row['metadata'] ? json_decode($row['metadata'], true) : null;
        $messages[] = $row;
    }
    
    $session['messages'] = $messages;
    
    echo json_encode([
        'success' => true,
        'session' => $session
    ]);
}

/**
 * Delete session
 */
function deleteSession($db, $user, $session_id) {
    // Verify ownership
    $stmt = $db->prepare("
        SELECT id FROM chat_sessions
        WHERE id = ? AND user_id = ? AND deleted_at IS NULL
    ");
    $stmt->bind_param('ii', $session_id, $user['user_id']);
    $stmt->execute();
    $result = $stmt->get_result();
    
    if ($result->num_rows === 0) {
        http_response_code(404);
        echo json_encode(['error' => 'Session not found']);
        return;
    }
    
    // Soft delete session
    $stmt = $db->prepare("
        UPDATE chat_sessions 
        SET deleted_at = NOW()
        WHERE id = ?
    ");
    $stmt->bind_param('i', $session_id);
    
    if ($stmt->execute()) {
        echo json_encode([
            'success' => true,
            'message' => 'Session deleted successfully'
        ]);
    } else {
        http_response_code(500);
        echo json_encode(['error' => 'Failed to delete session']);
    }
}
