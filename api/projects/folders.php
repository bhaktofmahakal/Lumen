<?php
/**
 * Project Folders Management Endpoint
 * Handles folder creation, listing, updating, and deletion within projects
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

// POST: Create new folder
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $input = json_decode(file_get_contents('php://input'), true);
    
    $project_id = intval($input['project_id'] ?? 0);
    $name = trim($input['name'] ?? '');
    $parent_id = isset($input['parent_id']) ? intval($input['parent_id']) : null;
    
    // Validate required fields
    if (empty($project_id) || empty($name)) {
        http_response_code(400);
        echo json_encode(['error' => 'project_id and name are required']);
        exit;
    }
    
    // Check if user has editor access to project
    $rbac = new RBACMiddleware();
    $access = $rbac->requireProjectAccess($user['user_id'], $project_id, 'editor');
    
    // Validate parent folder if provided
    if ($parent_id !== null) {
        $stmt = $conn->prepare("SELECT id FROM folders WHERE id = ? AND project_id = ? AND deleted_at IS NULL");
        $stmt->bind_param("ii", $parent_id, $project_id);
        $stmt->execute();
        $result = $stmt->get_result();
        
        if ($result->num_rows === 0) {
            http_response_code(404);
            echo json_encode(['error' => 'Parent folder not found']);
            $stmt->close();
            $conn->close();
            exit;
        }
        $stmt->close();
    }
    
    // Create folder
    $stmt = $conn->prepare("INSERT INTO folders (project_id, parent_id, name) VALUES (?, ?, ?)");
    $stmt->bind_param("iis", $project_id, $parent_id, $name);
    
    if ($stmt->execute()) {
        $folder_id = $stmt->insert_id;
        
        http_response_code(201);
        echo json_encode([
            'success' => true,
            'message' => 'Folder created successfully',
            'folder' => [
                'id' => $folder_id,
                'project_id' => $project_id,
                'parent_id' => $parent_id,
                'name' => $name,
                'created_at' => date('Y-m-d H:i:s')
            ]
        ]);
    } else {
        http_response_code(500);
        echo json_encode(['error' => 'Failed to create folder']);
    }
    
    $stmt->close();
    $conn->close();
    exit;
}

// GET: List folders in project
if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    $project_id = intval($_GET['project_id'] ?? 0);
    $parent_id = isset($_GET['parent_id']) ? intval($_GET['parent_id']) : null;
    
    if (empty($project_id)) {
        http_response_code(400);
        echo json_encode(['error' => 'project_id is required']);
        exit;
    }
    
    // Check if user has access to project
    $rbac = new RBACMiddleware();
    $access = $rbac->requireProjectAccess($user['user_id'], $project_id, 'viewer');
    
    // Get folders
    if ($parent_id === null) {
        $stmt = $conn->prepare("
            SELECT id, project_id, parent_id, name, created_at, updated_at
            FROM folders 
            WHERE project_id = ? AND parent_id IS NULL AND deleted_at IS NULL
            ORDER BY name ASC
        ");
        $stmt->bind_param("i", $project_id);
    } else {
        $stmt = $conn->prepare("
            SELECT id, project_id, parent_id, name, created_at, updated_at
            FROM folders 
            WHERE project_id = ? AND parent_id = ? AND deleted_at IS NULL
            ORDER BY name ASC
        ");
        $stmt->bind_param("ii", $project_id, $parent_id);
    }
    
    $stmt->execute();
    $result = $stmt->get_result();
    
    $folders = [];
    while ($row = $result->fetch_assoc()) {
        // Count documents in folder
        $count_stmt = $conn->prepare("SELECT COUNT(*) as doc_count FROM documents WHERE folder_id = ? AND deleted_at IS NULL");
        $count_stmt->bind_param("i", $row['id']);
        $count_stmt->execute();
        $count_result = $count_stmt->get_result();
        $count_data = $count_result->fetch_assoc();
        $count_stmt->close();
        
        $row['document_count'] = $count_data['doc_count'];
        $folders[] = $row;
    }
    
    http_response_code(200);
    echo json_encode([
        'success' => true,
        'folders' => $folders
    ]);
    
    $stmt->close();
    $conn->close();
    exit;
}

// PUT: Update folder
if ($_SERVER['REQUEST_METHOD'] === 'PUT') {
    $input = json_decode(file_get_contents('php://input'), true);
    
    $folder_id = intval($input['id'] ?? 0);
    $name = trim($input['name'] ?? '');
    
    if (empty($folder_id) || empty($name)) {
        http_response_code(400);
        echo json_encode(['error' => 'Folder ID and name are required']);
        exit;
    }
    
    // Get folder's project_id
    $stmt = $conn->prepare("SELECT project_id FROM folders WHERE id = ? AND deleted_at IS NULL");
    $stmt->bind_param("i", $folder_id);
    $stmt->execute();
    $result = $stmt->get_result();
    
    if ($result->num_rows === 0) {
        http_response_code(404);
        echo json_encode(['error' => 'Folder not found']);
        $stmt->close();
        $conn->close();
        exit;
    }
    
    $folder = $result->fetch_assoc();
    $stmt->close();
    
    // Check if user has editor access to project
    $rbac = new RBACMiddleware();
    $access = $rbac->requireProjectAccess($user['user_id'], $folder['project_id'], 'editor');
    
    // Update folder
    $stmt = $conn->prepare("UPDATE folders SET name = ? WHERE id = ?");
    $stmt->bind_param("si", $name, $folder_id);
    
    if ($stmt->execute()) {
        http_response_code(200);
        echo json_encode([
            'success' => true,
            'message' => 'Folder updated successfully'
        ]);
    } else {
        http_response_code(500);
        echo json_encode(['error' => 'Failed to update folder']);
    }
    
    $stmt->close();
    $conn->close();
    exit;
}

// DELETE: Delete folder
if ($_SERVER['REQUEST_METHOD'] === 'DELETE') {
    $input = json_decode(file_get_contents('php://input'), true);
    
    $folder_id = intval($input['id'] ?? 0);
    
    if (empty($folder_id)) {
        http_response_code(400);
        echo json_encode(['error' => 'Folder ID is required']);
        exit;
    }
    
    // Get folder's project_id
    $stmt = $conn->prepare("SELECT project_id FROM folders WHERE id = ? AND deleted_at IS NULL");
    $stmt->bind_param("i", $folder_id);
    $stmt->execute();
    $result = $stmt->get_result();
    
    if ($result->num_rows === 0) {
        http_response_code(404);
        echo json_encode(['error' => 'Folder not found']);
        $stmt->close();
        $conn->close();
        exit;
    }
    
    $folder = $result->fetch_assoc();
    $stmt->close();
    
    // Check if user has editor access to project
    $rbac = new RBACMiddleware();
    $access = $rbac->requireProjectAccess($user['user_id'], $folder['project_id'], 'editor');
    
    // Soft delete folder (documents will have folder_id set to NULL due to ON DELETE SET NULL)
    $stmt = $conn->prepare("UPDATE folders SET deleted_at = NOW() WHERE id = ?");
    $stmt->bind_param("i", $folder_id);
    
    if ($stmt->execute()) {
        http_response_code(200);
        echo json_encode([
            'success' => true,
            'message' => 'Folder deleted successfully'
        ]);
    } else {
        http_response_code(500);
        echo json_encode(['error' => 'Failed to delete folder']);
    }
    
    $stmt->close();
    $conn->close();
    exit;
}

http_response_code(405);
echo json_encode(['error' => 'Method not allowed']);
$conn->close();
