<?php
/**
 * Project Statistics Endpoint
 * Provides detailed statistics for a project including document count, storage used, etc.
 */

header('Content-Type: application/json');
require_once __DIR__ . '/../../config.php';
require_once __DIR__ . '/../../utilities.php';
require_once __DIR__ . '/../auth/AuthMiddleware.php';
require_once __DIR__ . '/../auth/RBACMiddleware.php';

// Only allow GET requests
if ($_SERVER['REQUEST_METHOD'] !== 'GET') {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
    exit;
}

// Authenticate user
$auth = new AuthMiddleware();
$user = $auth->requireAuth();

$project_id = intval($_GET['project_id'] ?? 0);

if (empty($project_id)) {
    http_response_code(400);
    echo json_encode(['error' => 'project_id is required']);
    exit;
}

// Check if user has access to project
$rbac = new RBACMiddleware();
$access = $rbac->requireProjectAccess($user['user_id'], $project_id, 'viewer');

$conn = getDBConnection();
if (!$conn) {
    http_response_code(500);
    echo json_encode(['error' => 'Database connection failed']);
    exit;
}

// Get project basic info
$stmt = $conn->prepare("
    SELECT id, name, document_count, storage_used, created_at
    FROM projects 
    WHERE id = ? AND deleted_at IS NULL
");
$stmt->bind_param("i", $project_id);
$stmt->execute();
$result = $stmt->get_result();

if ($result->num_rows === 0) {
    http_response_code(404);
    echo json_encode(['error' => 'Project not found']);
    $stmt->close();
    $conn->close();
    exit;
}

$project = $result->fetch_assoc();
$stmt->close();

// Calculate actual document count and storage
$stmt = $conn->prepare("
    SELECT COUNT(*) as actual_count, COALESCE(SUM(file_size), 0) as actual_storage
    FROM documents 
    WHERE project_id = ? AND deleted_at IS NULL
");
$stmt->bind_param("i", $project_id);
$stmt->execute();
$result = $stmt->get_result();
$doc_stats = $result->fetch_assoc();
$stmt->close();

// Update project statistics if they differ
if ($doc_stats['actual_count'] != $project['document_count'] || 
    $doc_stats['actual_storage'] != $project['storage_used']) {
    $update_stmt = $conn->prepare("UPDATE projects SET document_count = ?, storage_used = ? WHERE id = ?");
    $update_stmt->bind_param("iii", $doc_stats['actual_count'], $doc_stats['actual_storage'], $project_id);
    $update_stmt->execute();
    $update_stmt->close();
}

// Get folder count
$stmt = $conn->prepare("SELECT COUNT(*) as folder_count FROM folders WHERE project_id = ? AND deleted_at IS NULL");
$stmt->bind_param("i", $project_id);
$stmt->execute();
$result = $stmt->get_result();
$folder_stats = $result->fetch_assoc();
$stmt->close();

// Get chat session count (check if table has project_id column)
$result = $conn->query("SHOW COLUMNS FROM chat_sessions LIKE 'project_id'");
$has_project_id = $result && $result->num_rows > 0;

if ($has_project_id) {
    $stmt = $conn->prepare("SELECT COUNT(*) as session_count FROM chat_sessions WHERE project_id = ? AND deleted_at IS NULL");
    $stmt->bind_param("i", $project_id);
    $stmt->execute();
    $result = $stmt->get_result();
    $chat_stats = $result->fetch_assoc();
    $stmt->close();
} else {
    $chat_stats = ['session_count' => 0];
}

// Get LaTeX document count
$stmt = $conn->prepare("SELECT COUNT(*) as latex_count FROM latex_documents WHERE project_id = ? AND deleted_at IS NULL");
$stmt->bind_param("i", $project_id);
$stmt->execute();
$result = $stmt->get_result();
$latex_stats = $result->fetch_assoc();
$stmt->close();

// Get collaborator count
$stmt = $conn->prepare("SELECT COUNT(*) as collaborator_count FROM project_collaborators WHERE project_id = ?");
$stmt->bind_param("i", $project_id);
$stmt->execute();
$result = $stmt->get_result();
$collab_stats = $result->fetch_assoc();
$stmt->close();

// Get document type breakdown
$stmt = $conn->prepare("
    SELECT document_type, COUNT(*) as count 
    FROM documents 
    WHERE project_id = ? AND deleted_at IS NULL 
    GROUP BY document_type
");
$stmt->bind_param("i", $project_id);
$stmt->execute();
$result = $stmt->get_result();

$document_types = [];
while ($row = $result->fetch_assoc()) {
    $document_types[$row['document_type']] = $row['count'];
}
$stmt->close();

// Format storage size
function formatBytes($bytes) {
    if ($bytes >= 1073741824) {
        return number_format($bytes / 1073741824, 2) . ' GB';
    } elseif ($bytes >= 1048576) {
        return number_format($bytes / 1048576, 2) . ' MB';
    } elseif ($bytes >= 1024) {
        return number_format($bytes / 1024, 2) . ' KB';
    } else {
        return $bytes . ' bytes';
    }
}

http_response_code(200);
echo json_encode([
    'success' => true,
    'statistics' => [
        'project_id' => $project['id'],
        'project_name' => $project['name'],
        'created_at' => $project['created_at'],
        'document_count' => (int)$doc_stats['actual_count'],
        'storage_used' => (int)$doc_stats['actual_storage'],
        'storage_used_formatted' => formatBytes($doc_stats['actual_storage']),
        'folder_count' => (int)$folder_stats['folder_count'],
        'chat_session_count' => (int)$chat_stats['session_count'],
        'latex_document_count' => (int)$latex_stats['latex_count'],
        'collaborator_count' => (int)$collab_stats['collaborator_count'],
        'document_types' => $document_types
    ]
]);

$conn->close();
