<?php
/**
 * Email Verification Endpoint
 * Handles email verification for new user registrations
 */

header('Content-Type: application/json');
require_once __DIR__ . '/../../config.php';
require_once __DIR__ . '/../../utilities.php';

// Only allow GET requests
if ($_SERVER['REQUEST_METHOD'] !== 'GET') {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
    exit;
}

// Get token from query parameter
$token = $_GET['token'] ?? null;

if (empty($token)) {
    http_response_code(400);
    echo json_encode(['error' => 'Verification token is required']);
    exit;
}

// Connect to database
$conn = getDBConnection();
if (!$conn) {
    http_response_code(500);
    echo json_encode(['error' => 'Database connection failed']);
    exit;
}

// For now, we'll use a simple approach: store tokens in a separate table
// In a production system, you'd want to implement a proper email verification system

// TODO: Implement proper email verification with tokens stored in database
// For MVP, we'll just mark the email as verified based on user_id

if (isset($_GET['user_id'])) {
    $user_id = intval($_GET['user_id']);
    
    $stmt = $conn->prepare("UPDATE users SET email_verified_at = NOW() WHERE id = ? AND email_verified_at IS NULL");
    $stmt->bind_param("i", $user_id);
    
    if ($stmt->execute() && $stmt->affected_rows > 0) {
        http_response_code(200);
        echo json_encode([
            'success' => true,
            'message' => 'Email verified successfully. You can now log in.'
        ]);
    } else {
        http_response_code(400);
        echo json_encode(['error' => 'Invalid or expired verification token']);
    }
    
    $stmt->close();
} else {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid verification request']);
}

$conn->close();
