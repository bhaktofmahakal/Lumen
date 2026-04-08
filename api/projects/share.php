<?php
/**
 * Project Sharing Endpoint
 * Handles inviting collaborators to projects with role assignment
 */

header('Content-Type: application/json');
require_once __DIR__ . '/../../config.php';
require_once __DIR__ . '/../../utilities.php';
require_once __DIR__ . '/../auth/AuthMiddleware.php';
require_once __DIR__ . '/../auth/RBACMiddleware.php';

// Only allow POST requests
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
    exit;
}

// Authenticate user
$auth = new AuthMiddleware();
$user = $auth->requireAuth();

// Get JSON input
$input = json_decode(file_get_contents('php://input'), true);

// Validate required fields
if (empty($input['project_id']) || empty($input['email']) || empty($input['role'])) {
    http_response_code(400);
    echo json_encode(['error' => 'project_id, email, and role are required']);
    exit;
}

$project_id = intval($input['project_id']);
$invitee_email = filter_var($input['email'], FILTER_SANITIZE_EMAIL);
$role = $input['role'];

// Validate email
if (!filter_var($invitee_email, FILTER_VALIDATE_EMAIL)) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid email format']);
    exit;
}

// Validate role
$valid_roles = ['viewer', 'editor', 'admin'];
if (!in_array($role, $valid_roles)) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid role. Must be viewer, editor, or admin']);
    exit;
}

// Check if user has admin access to project
$rbac = new RBACMiddleware();
$access = $rbac->requireProjectAccess($user['user_id'], $project_id, 'admin');

// Connect to database
$conn = getDBConnection();
if (!$conn) {
    http_response_code(500);
    echo json_encode(['error' => 'Database connection failed']);
    exit;
}

// Find invitee user by email
$stmt = $conn->prepare("SELECT id, email, name FROM users WHERE email = ? AND deleted_at IS NULL");
$stmt->bind_param("s", $invitee_email);
$stmt->execute();
$result = $stmt->get_result();

if ($result->num_rows === 0) {
    http_response_code(404);
    echo json_encode(['error' => 'User not found with this email']);
    $stmt->close();
    $conn->close();
    exit;
}

$invitee = $result->fetch_assoc();
$invitee_id = $invitee['id'];
$stmt->close();

// Check if user is trying to invite themselves
if ($invitee_id === $user['user_id']) {
    http_response_code(400);
    echo json_encode(['error' => 'Cannot invite yourself to the project']);
    $conn->close();
    exit;
}

// Check if invitee is already a collaborator
$stmt = $conn->prepare("SELECT id, role, accepted_at FROM project_collaborators WHERE project_id = ? AND user_id = ?");
$stmt->bind_param("ii", $project_id, $invitee_id);
$stmt->execute();
$result = $stmt->get_result();

if ($result->num_rows > 0) {
    $existing = $result->fetch_assoc();
    
    if ($existing['accepted_at']) {
        // Update role if already accepted
        $stmt = $conn->prepare("UPDATE project_collaborators SET role = ? WHERE project_id = ? AND user_id = ?");
        $stmt->bind_param("sii", $role, $project_id, $invitee_id);
        $stmt->execute();
        
        http_response_code(200);
        echo json_encode([
            'success' => true,
            'message' => 'Collaborator role updated',
            'collaborator' => [
                'user_id' => $invitee_id,
                'email' => $invitee_email,
                'name' => $invitee['name'],
                'role' => $role
            ]
        ]);
    } else {
        // Resend invitation
        http_response_code(200);
        echo json_encode([
            'success' => true,
            'message' => 'Invitation already sent',
            'collaborator' => [
                'user_id' => $invitee_id,
                'email' => $invitee_email,
                'name' => $invitee['name'],
                'role' => $role,
                'pending' => true
            ]
        ]);
    }
    
    $stmt->close();
    $conn->close();
    exit;
}
$stmt->close();

// Create new invitation
$stmt = $conn->prepare("INSERT INTO project_collaborators (project_id, user_id, role, invited_by, accepted_at) VALUES (?, ?, ?, ?, NOW())");
$stmt->bind_param("iisi", $project_id, $invitee_id, $role, $user['user_id']);

if ($stmt->execute()) {
    // TODO: Send email notification to invitee
    
    http_response_code(201);
    echo json_encode([
        'success' => true,
        'message' => 'Collaborator invited successfully',
        'collaborator' => [
            'user_id' => $invitee_id,
            'email' => $invitee_email,
            'name' => $invitee['name'],
            'role' => $role
        ]
    ]);
} else {
    http_response_code(500);
    echo json_encode(['error' => 'Failed to create invitation']);
}

$stmt->close();
$conn->close();
