<?php
/**
 * Document Comments API
 * Requirements: 11.5, 11.6
 */

require_once __DIR__ . '/../auth/AuthMiddleware.php';
require_once __DIR__ . '/../../config/database.php';

header('Content-Type: application/json');

// Authenticate user
$auth = new AuthMiddleware();
$user = $auth->authenticate();

if (!$user) {
    http_response_code(401);
    echo json_encode(['error' => 'Unauthorized']);
    exit;
}

$method = $_SERVER['REQUEST_METHOD'];
$path = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
$pathParts = explode('/', trim($path, '/'));

// Extract document ID from path
$documentId = $pathParts[2] ?? null;

if (!$documentId) {
    http_response_code(400);
    echo json_encode(['error' => 'Document ID required']);
    exit;
}

try {
    $db = Database::getInstance()->getConnection();
    
    switch ($method) {
        case 'GET':
            // Get all comments for document
            getComments($db, $documentId, $user);
            break;
            
        case 'POST':
            // Add new comment
            addComment($db, $documentId, $user);
            break;
            
        case 'DELETE':
            // Delete comment
            $commentId = $pathParts[4] ?? null;
            if ($commentId) {
                deleteComment($db, $commentId, $user);
            } else {
                http_response_code(400);
                echo json_encode(['error' => 'Comment ID required']);
            }
            break;
            
        default:
            http_response_code(405);
            echo json_encode(['error' => 'Method not allowed']);
    }
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(['error' => 'Server error: ' . $e->getMessage()]);
}

/**
 * Get all comments for a document
 */
function getComments($db, $documentId, $user) {
    // Verify user has access to document
    $stmt = $db->prepare("
        SELECT d.id 
        FROM documents d
        JOIN projects p ON d.project_id = p.id
        LEFT JOIN project_collaborators pc ON p.id = pc.project_id
        WHERE d.id = ? AND (p.user_id = ? OR pc.user_id = ?)
    ");
    $stmt->execute([$documentId, $user['id'], $user['id']]);
    
    if (!$stmt->fetch()) {
        http_response_code(403);
        echo json_encode(['error' => 'Access denied']);
        return;
    }
    
    // Get comments with replies
    $stmt = $db->prepare("
        SELECT 
            c.id,
            c.user_id,
            u.name as user_name,
            c.line_number,
            c.content,
            c.resolved,
            c.resolved_by,
            c.resolved_at,
            c.created_at,
            c.updated_at
        FROM document_comments c
        JOIN users u ON c.user_id = u.id
        WHERE c.document_id = ?
        ORDER BY c.line_number ASC, c.created_at DESC
    ");
    $stmt->execute([$documentId]);
    $comments = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    // Get replies for each comment
    foreach ($comments as &$comment) {
        $stmt = $db->prepare("
            SELECT 
                r.id,
                r.user_id,
                u.name as user_name,
                r.content,
                r.created_at
            FROM comment_replies r
            JOIN users u ON r.user_id = u.id
            WHERE r.comment_id = ?
            ORDER BY r.created_at ASC
        ");
        $stmt->execute([$comment['id']]);
        $comment['replies'] = $stmt->fetchAll(PDO::FETCH_ASSOC);
    }
    
    echo json_encode([
        'success' => true,
        'comments' => $comments
    ]);
}

/**
 * Add new comment
 */
function addComment($db, $documentId, $user) {
    $input = json_decode(file_get_contents('php://input'), true);
    
    $projectId = $input['project_id'] ?? null;
    $lineNumber = $input['line_number'] ?? null;
    $content = $input['content'] ?? null;
    $mentions = $input['mentions'] ?? [];
    
    if (!$lineNumber || !$content) {
        http_response_code(400);
        echo json_encode(['error' => 'Line number and content required']);
        return;
    }
    
    // Verify user has access to document
    $stmt = $db->prepare("
        SELECT d.id, d.project_id
        FROM documents d
        JOIN projects p ON d.project_id = p.id
        LEFT JOIN project_collaborators pc ON p.id = pc.project_id
        WHERE d.id = ? AND (p.user_id = ? OR pc.user_id = ?)
    ");
    $stmt->execute([$documentId, $user['id'], $user['id']]);
    $document = $stmt->fetch(PDO::FETCH_ASSOC);
    
    if (!$document) {
        http_response_code(403);
        echo json_encode(['error' => 'Access denied']);
        return;
    }
    
    // Insert comment
    $stmt = $db->prepare("
        INSERT INTO document_comments 
        (document_id, user_id, line_number, content, created_at, updated_at)
        VALUES (?, ?, ?, ?, NOW(), NOW())
    ");
    $stmt->execute([$documentId, $user['id'], $lineNumber, $content]);
    $commentId = $db->lastInsertId();
    
    // Send notifications for mentions (Requirement 11.6)
    if (!empty($mentions)) {
        sendMentionNotifications($db, $commentId, $mentions, $user, $document['project_id']);
    }
    
    // Get the created comment
    $stmt = $db->prepare("
        SELECT 
            c.id,
            c.user_id,
            u.name as user_name,
            c.line_number,
            c.content,
            c.resolved,
            c.created_at
        FROM document_comments c
        JOIN users u ON c.user_id = u.id
        WHERE c.id = ?
    ");
    $stmt->execute([$commentId]);
    $comment = $stmt->fetch(PDO::FETCH_ASSOC);
    $comment['replies'] = [];
    
    echo json_encode([
        'success' => true,
        'comment' => $comment
    ]);
}

/**
 * Delete comment
 */
function deleteComment($db, $commentId, $user) {
    // Verify user owns the comment
    $stmt = $db->prepare("
        SELECT user_id FROM document_comments WHERE id = ?
    ");
    $stmt->execute([$commentId]);
    $comment = $stmt->fetch(PDO::FETCH_ASSOC);
    
    if (!$comment) {
        http_response_code(404);
        echo json_encode(['error' => 'Comment not found']);
        return;
    }
    
    if ($comment['user_id'] != $user['id']) {
        http_response_code(403);
        echo json_encode(['error' => 'Access denied']);
        return;
    }
    
    // Delete comment and replies
    $stmt = $db->prepare("DELETE FROM comment_replies WHERE comment_id = ?");
    $stmt->execute([$commentId]);
    
    $stmt = $db->prepare("DELETE FROM document_comments WHERE id = ?");
    $stmt->execute([$commentId]);
    
    echo json_encode(['success' => true]);
}

/**
 * Send notifications for mentions
 */
function sendMentionNotifications($db, $commentId, $mentions, $fromUser, $projectId) {
    foreach ($mentions as $username) {
        // Find user by username
        $stmt = $db->prepare("SELECT id FROM users WHERE username = ?");
        $stmt->execute([$username]);
        $mentionedUser = $stmt->fetch(PDO::FETCH_ASSOC);
        
        if ($mentionedUser) {
            // Create notification
            $stmt = $db->prepare("
                INSERT INTO notifications 
                (user_id, type, title, message, link, created_at)
                VALUES (?, 'mention', ?, ?, ?, NOW())
            ");
            $stmt->execute([
                $mentionedUser['id'],
                'Mentioned in comment',
                $fromUser['name'] . ' mentioned you in a comment',
                '/projects/' . $projectId . '/comments/' . $commentId
            ]);
        }
    }
}
