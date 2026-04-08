<?php
/**
 * User Logout Endpoint
 * Handles user logout and session cleanup
 */

header('Content-Type: application/json');
require_once __DIR__ . '/../../config.php';
require_once __DIR__ . '/../../utilities.php';
require_once __DIR__ . '/JWTHandler.php';

// Only allow POST requests
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
    exit;
}

// Get token from header
$jwt_handler = new JWTHandler();
$token = $jwt_handler->getTokenFromHeader();

if ($token) {
    $payload = $jwt_handler->validateToken($token);
    
    if ($payload && isset($payload['user_id'])) {
        // Connect to database
        $conn = getDBConnection();
        
        if ($conn) {
            // Delete session from database
            $stmt = $conn->prepare("DELETE FROM sessions WHERE user_id = ?");
            $stmt->bind_param("i", $payload['user_id']);
            $stmt->execute();
            $stmt->close();
            $conn->close();
        }
    }
}

// Destroy PHP session
session_start();
session_destroy();

http_response_code(200);
echo json_encode([
    'success' => true,
    'message' => 'Logged out successfully'
]);
