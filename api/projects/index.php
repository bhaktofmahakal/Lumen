<?php
/**
 * Project CRUD Operations Endpoint
 * Handles create, list, get, update, and delete operations for projects
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

// POST: Create new project
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $input = json_decode(file_get_contents('php://input'), true);
    
    $name = trim($input['name'] ?? '');
    $description = trim($input['description'] ?? '');
    $visibility = $input['visibility'] ?? 'private';
    
    // Validate required fields
    if (empty($name)) {
        http_response_code(400);
        echo json_encode(['error' => 'Project name is required']);
        exit;
    }
    
    // Validate visibility
    $valid_visibility = ['private', 'shared', 'public'];
    if (!in_array($visibility, $valid_visibility)) {
        http_response_code(400);
        echo json_encode(['error' => 'Invalid visibility. Must be private, shared, or public']);
        exit;
    }
    
    // Create project
    $stmt = $conn->prepare("INSERT INTO projects (user_id, name, description, visibility) VALUES (?, ?, ?, ?)");
    $stmt->bind_param("isss", $user['user_id'], $name, $description, $visibility);
    
    if ($stmt->execute()) {
        $project_id = $stmt->insert_id;
        
        http_response_code(201);
        echo json_encode([
            'success' => true,
            'message' => 'Project created successfully',
            'project' => [
                'id' => $project_id,
                'name' => $name,
                'description' => $description,
                'visibility' => $visibility,
                'document_count' => 0,
                'storage_used' => 0,
                'created_at' => date('Y-m-d H:i:s')
            ]
        ]);
    } else {
        http_response_code(500);
        echo json_encode(['error' => 'Failed to create project']);
    }
    
    $stmt->close();
    $conn->close();
    exit;
}

// GET: List projects or get single project
if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    $project_id = intval($_GET['id'] ?? 0);
    
    // Get single project
    if ($project_id > 0) {
        // Check if user has access to project
        $rbac = new RBACMiddleware();
        $access = $rbac->requireProjectAccess($user['user_id'], $project_id, 'viewer');
        
        $stmt = $conn->prepare("
            SELECT id, user_id, name, description, visibility, document_count, storage_used, 
                   created_at, updated_at, archived_at
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
        
        http_response_code(200);
        echo json_encode([
            'success' => true,
            'project' => $project
        ]);
        
        $stmt->close();
        $conn->close();
        exit;
    }
    
    // List all projects for user
    $stmt = $conn->prepare("
        SELECT p.id, p.user_id, p.name, p.description, p.visibility, p.document_count, 
               p.storage_used, p.created_at, p.updated_at, p.archived_at,
               CASE WHEN p.user_id = ? THEN 'owner' ELSE pc.role END as user_role
        FROM projects p
        LEFT JOIN project_collaborators pc ON p.id = pc.project_id AND pc.user_id = ?
        WHERE (p.user_id = ? OR pc.user_id = ?) AND p.deleted_at IS NULL
        ORDER BY p.updated_at DESC
    ");
    $stmt->bind_param("iiii", $user['user_id'], $user['user_id'], $user['user_id'], $user['user_id']);
    $stmt->execute();
    $result = $stmt->get_result();
    
    $projects = [];
    while ($row = $result->fetch_assoc()) {
        $projects[] = $row;
    }
    
    http_response_code(200);
    echo json_encode([
        'success' => true,
        'projects' => $projects
    ]);
    
    $stmt->close();
    $conn->close();
    exit;
}

// PUT: Update project
if ($_SERVER['REQUEST_METHOD'] === 'PUT') {
    $input = json_decode(file_get_contents('php://input'), true);
    
    $project_id = intval($input['id'] ?? 0);
    
    if (empty($project_id)) {
        http_response_code(400);
        echo json_encode(['error' => 'Project ID is required']);
        exit;
    }
    
    // Check if user has admin access to project
    $rbac = new RBACMiddleware();
    $access = $rbac->requireProjectAccess($user['user_id'], $project_id, 'admin');
    
    // Build update query dynamically
    $updates = [];
    $params = [];
    $types = '';
    
    if (isset($input['name']) && !empty(trim($input['name']))) {
        $updates[] = "name = ?";
        $params[] = trim($input['name']);
        $types .= 's';
    }
    
    if (isset($input['description'])) {
        $updates[] = "description = ?";
        $params[] = trim($input['description']);
        $types .= 's';
    }
    
    if (isset($input['visibility'])) {
        $valid_visibility = ['private', 'shared', 'public'];
        if (!in_array($input['visibility'], $valid_visibility)) {
            http_response_code(400);
            echo json_encode(['error' => 'Invalid visibility']);
            exit;
        }
        $updates[] = "visibility = ?";
        $params[] = $input['visibility'];
        $types .= 's';
    }
    
    if (empty($updates)) {
        http_response_code(400);
        echo json_encode(['error' => 'No fields to update']);
        exit;
    }
    
    // Add project_id to params
    $params[] = $project_id;
    $types .= 'i';
    
    $sql = "UPDATE projects SET " . implode(', ', $updates) . " WHERE id = ? AND deleted_at IS NULL";
    $stmt = $conn->prepare($sql);
    $stmt->bind_param($types, ...$params);
    
    if ($stmt->execute() && $stmt->affected_rows > 0) {
        http_response_code(200);
        echo json_encode([
            'success' => true,
            'message' => 'Project updated successfully'
        ]);
    } else {
        http_response_code(404);
        echo json_encode(['error' => 'Project not found or no changes made']);
    }
    
    $stmt->close();
    $conn->close();
    exit;
}

// DELETE: Delete project (soft delete)
if ($_SERVER['REQUEST_METHOD'] === 'DELETE') {
    $input = json_decode(file_get_contents('php://input'), true);
    
    $project_id = intval($input['id'] ?? 0);
    
    if (empty($project_id)) {
        http_response_code(400);
        echo json_encode(['error' => 'Project ID is required']);
        exit;
    }
    
    // Check if user is project owner (only owner can delete)
    $stmt = $conn->prepare("SELECT user_id FROM projects WHERE id = ? AND deleted_at IS NULL");
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
    if ($project['user_id'] !== $user['user_id']) {
        http_response_code(403);
        echo json_encode(['error' => 'Only project owner can delete the project']);
        $stmt->close();
        $conn->close();
        exit;
    }
    $stmt->close();
    
    // Soft delete project
    $stmt = $conn->prepare("UPDATE projects SET deleted_at = NOW() WHERE id = ?");
    $stmt->bind_param("i", $project_id);
    
    if ($stmt->execute()) {
        http_response_code(200);
        echo json_encode([
            'success' => true,
            'message' => 'Project deleted successfully'
        ]);
    } else {
        http_response_code(500);
        echo json_encode(['error' => 'Failed to delete project']);
    }
    
    $stmt->close();
    $conn->close();
    exit;
}

http_response_code(405);
echo json_encode(['error' => 'Method not allowed']);
$conn->close();
