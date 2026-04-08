<?php
/**
 * User Login Endpoint
 * Handles user authentication and JWT token generation
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

// Get JSON input
$input = json_decode(file_get_contents('php://input'), true);

// Validate required fields
if (empty($input['email']) || empty($input['password'])) {
    http_response_code(400);
    echo json_encode(['error' => 'Email and password are required']);
    exit;
}

$email = filter_var($input['email'], FILTER_SANITIZE_EMAIL);
$password = $input['password'];

// Validate email format
if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid email format']);
    exit;
}

// Connect to database
$conn = getDBConnection();
if (!$conn) {
    http_response_code(500);
    echo json_encode(['error' => 'Database connection failed']);
    exit;
}

// Fetch user by email
$stmt = $conn->prepare("SELECT id, email, password_hash, name, role, subscription_tier, email_verified_at, two_factor_enabled FROM users WHERE email = ? AND deleted_at IS NULL");
$stmt->bind_param("s", $email);
$stmt->execute();
$result = $stmt->get_result();

if ($result->num_rows === 0) {
    http_response_code(401);
    echo json_encode(['error' => 'Invalid email or password']);
    $stmt->close();
    $conn->close();
    exit;
}

$user = $result->fetch_assoc();
$stmt->close();

// Verify password
if (!password_verify($password, $user['password_hash'])) {
    http_response_code(401);
    echo json_encode(['error' => 'Invalid email or password']);
    $conn->close();
    exit;
}

// Check if email is verified
if (empty($user['email_verified_at'])) {
    http_response_code(403);
    echo json_encode([
        'error' => 'Email not verified',
        'message' => 'Please verify your email before logging in'
    ]);
    $conn->close();
    exit;
}

// Check if 2FA is enabled
if ($user['two_factor_enabled']) {
    // TODO: Implement 2FA verification flow
    // For now, we'll skip 2FA and proceed with login
}

// Generate JWT token
$jwt_handler = new JWTHandler();
$token = $jwt_handler->generateToken([
    'user_id' => $user['id'],
    'email' => $user['email'],
    'role' => $user['role'],
    'subscription_tier' => $user['subscription_tier']
]);

// Create session record
$session_id = bin2hex(random_bytes(32));
$ip_address = $_SERVER['REMOTE_ADDR'] ?? null;
$user_agent = $_SERVER['HTTP_USER_AGENT'] ?? null;
$payload = json_encode(['token' => $token]);

$stmt = $conn->prepare("INSERT INTO sessions (id, user_id, ip_address, user_agent, payload) VALUES (?, ?, ?, ?, ?)");
$stmt->bind_param("sisss", $session_id, $user['id'], $ip_address, $user_agent, $payload);
$stmt->execute();
$stmt->close();

// Start PHP session for backward compatibility
session_start();
$_SESSION['user_id'] = $user['id'];
$_SESSION['email'] = $user['email'];
$_SESSION['role'] = $user['role'];
$_SESSION['session_id'] = $session_id;

$conn->close();

// Return success response with token
http_response_code(200);
echo json_encode([
    'success' => true,
    'message' => 'Login successful',
    'token' => $token,
    'session_id' => $session_id,
    'user' => [
        'id' => $user['id'],
        'email' => $user['email'],
        'name' => $user['name'],
        'role' => $user['role'],
        'subscription_tier' => $user['subscription_tier']
    ]
]);
