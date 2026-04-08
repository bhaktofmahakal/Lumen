<?php
/**
 * Project Collaborators Management Endpoint
 * Handles listing, updating, and removing collaborators
 */

header('Content-Type: application/json');
require_once __DIR__ . '/../../config.php';
require_once __DIR__ . '/../../utilities.php';
require_once __DIR__ . '/../auth/AuthMiddleware.php';
require_once __DIR__ . '/../auth/RBACMiddleware.php';

// Authenticate user
$auth = new AuthMiddleware();
$user = $auth->requireAuth();

$conn = getDBConnection();
if (!$conn) {
    http_response_code(500);
    echo json_encode(['error' => 'Database connection failed']);
    exit;
}

// GET: List collaborators
if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    $project_id = intval($_GET['project_id'] ?? 0);
    
    if (empty($project_id)) {
        http_response_code(400);
        echo json_encode(['error' => 'project_id is required']);
        exit;
    }
    
    // Check if user has access to project
    $rbac = new RBACMiddleware();
    $access = $rbac->requireProjectAccess($user['user_id'], $project_id, 'viewer');
    
    // Get project owner
    $stmt = $conn->prepare("SELECT u.id, u.email, u.name FROM projects p JOIN users u ON p.user_id = u.id WHERE p.id = ?");
    $stmt->bind_param("i", $project_id);
    $stmt->execute();
    $result = $stmt->get_result();
    $owner = $result->fetch_assoc();
    $stmt->close();
    
    // Get collaborators
    $stmt = $conn->prepare("
        SELECT pc.user_id, pc.role, pc.invited_at, pc.accepted_at, u.email, u.name
        FROM project_collaborators pc
        JOIN users u ON pc.user_id = u.id
        WHERE pc.project_id = ?
        ORDER BY pc.accepted_at DESC, pc.invited_at DESC
    ");
    $stmt->bind_param("i", $project_id);
    $stmt->execute();
    $result = $stmt->get_result();
    
    $collaborators = [];
    while ($row = $result->fetch_assoc()) {
        $collaborators[] = [
            'user_id' => $row['user_id'],
            'email' => $row['email'],
            'name' => $row['name'],
            'role' => $row['role'],
            'invited_at' => $row['invited_at'],
            'accepted_at' => $row['accepted_at'],
            'pending' => empty($row['accepted_at'])
        ];
    }
    
    http_response_code(200);
    echo json_encode([
        'success' => true,
        'owner' => [
            'user_id' => $owner['id'],
            'email' => $owner['email'],
            'name' => $owner['name'],
            'role' => 'owner'
        ],
        'collaborators' => $collaborators
    ]);
    
    $stmt->close();
    $conn->close();
    exit;
}

// DELETE: Remove collaborator
if ($_SERVER['REQUEST_METHOD'] === 'DELETE') {
    $input = json_decode(file_get_contents('php://input'), true);
    
    $project_id = intval($input['project_id'] ?? 0);
    $collaborator_id = intval($input['user_id'] ?? 0);
    
    if (empty($project_id) || empty($collaborator_id)) {
        http_response_code(400);
        echo json_encode(['error' => 'project_id and user_id are required']);
        exit;
    }
    
    // Check if user has admin access to project
    $rbac = new RBACMiddleware();
    $access = $rbac->requireProjectAccess($user['user_id'], $project_id, 'admin');
    
    // Remove collaborator
    $stmt = $conn->prepare("DELETE FROM project_collaborators WHERE project_id = ? AND user_id = ?");
    $stmt->bind_param("ii", $project_id, $collaborator_id);
    
    if ($stmt->execute() && $stmt->affected_rows > 0) {
        http_response_code(200);
        echo json_encode([
            'success' => true,
            'message' => 'Collaborator removed successfully'
        ]);
    } else {
        http_response_code(404);
        echo json_encode(['error' => 'Collaborator not found']);
    }
    
    $stmt->close();
    $conn->close();
    exit;
}

// PUT: Update collaborator role
if ($_SERVER['REQUEST_METHOD'] === 'PUT') {
    $input = json_decode(file_get_contents('php://input'), true);
    
    $project_id = intval($input['project_id'] ?? 0);
    $collaborator_id = intval($input['user_id'] ?? 0);
    $new_role = $input['role'] ?? '';
    
    if (empty($project_id) || empty($collaborator_id) || empty($new_role)) {
        http_response_code(400);
        echo json_encode(['error' => 'project_id, user_id, and role are required']);
        exit;
    }
    
    // Validate role
    $valid_roles = ['viewer', 'editor', 'admin'];
    if (!in_array($new_role, $valid_roles)) {
        http_response_code(400);
        echo json_encode(['error' => 'Invalid role. Must be viewer, editor, or admin']);
        exit;
    }
    
    // Check if user has admin access to project
    $rbac = new RBACMiddleware();
    $access = $rbac->requireProjectAccess($user['user_id'], $project_id, 'admin');
    
    // Update collaborator role
    $stmt = $conn->prepare("UPDATE project_collaborators SET role = ? WHERE project_id = ? AND user_id = ?");
    $stmt->bind_param("sii", $new_role, $project_id, $collaborator_id);
    
    if ($stmt->execute() && $stmt->affected_rows > 0) {
        http_response_code(200);
        echo json_encode([
            'success' => true,
            'message' => 'Collaborator role updated successfully',
            'role' => $new_role
        ]);
    } else {
        http_response_code(404);
        echo json_encode(['error' => 'Collaborator not found or role unchanged']);
    }
    
    $stmt->close();
    $conn->close();
    exit;
}

http_response_code(405);
echo json_encode(['error' => 'Method not allowed']);
$conn->close();
