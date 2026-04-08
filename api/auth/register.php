<?php
/**
 * User Registration Endpoint
 * Handles user registration with email/password
 */

header('Content-Type: application/json');
require_once __DIR__ . '/../../config.php';
require_once __DIR__ . '/../../utilities.php';

// Only allow POST requests
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
    exit;
}

// Get JSON input
$input = json_decode(file_get_contents('php://input'), true);

// Validate required fields
$required_fields = ['email', 'password', 'name'];
foreach ($required_fields as $field) {
    if (empty($input[$field])) {
        http_response_code(400);
        echo json_encode(['error' => "Missing required field: $field"]);
        exit;
    }
}

$email = filter_var($input['email'], FILTER_SANITIZE_EMAIL);
$password = $input['password'];
$name = htmlspecialchars($input['name'], ENT_QUOTES, 'UTF-8');

// Validate email format
if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid email format']);
    exit;
}

// Validate password requirements
// Minimum 8 characters, uppercase, lowercase, number, special character
if (strlen($password) < 8) {
    http_response_code(400);
    echo json_encode(['error' => 'Password must be at least 8 characters long']);
    exit;
}

if (!preg_match('/[A-Z]/', $password)) {
    http_response_code(400);
    echo json_encode(['error' => 'Password must contain at least one uppercase letter']);
    exit;
}

if (!preg_match('/[a-z]/', $password)) {
    http_response_code(400);
    echo json_encode(['error' => 'Password must contain at least one lowercase letter']);
    exit;
}

if (!preg_match('/[0-9]/', $password)) {
    http_response_code(400);
    echo json_encode(['error' => 'Password must contain at least one number']);
    exit;
}

if (!preg_match('/[^A-Za-z0-9]/', $password)) {
    http_response_code(400);
    echo json_encode(['error' => 'Password must contain at least one special character']);
    exit;
}

// Connect to database
$conn = getDBConnection();
if (!$conn) {
    http_response_code(500);
    echo json_encode(['error' => 'Database connection failed']);
    exit;
}

// Check if email already exists
$stmt = $conn->prepare("SELECT id FROM users WHERE email = ?");
$stmt->bind_param("s", $email);
$stmt->execute();
$result = $stmt->get_result();

if ($result->num_rows > 0) {
    http_response_code(409);
    echo json_encode(['error' => 'Email already registered']);
    $stmt->close();
    $conn->close();
    exit;
}
$stmt->close();

// Hash password using bcrypt
$password_hash = password_hash($password, PASSWORD_BCRYPT, ['cost' => 12]);

// Generate email verification token
$verification_token = bin2hex(random_bytes(32));

// Insert user into database
$stmt = $conn->prepare("INSERT INTO users (email, password_hash, name, role, subscription_tier) VALUES (?, ?, ?, 'user', 'free')");
$stmt->bind_param("sss", $email, $password_hash, $name);

if ($stmt->execute()) {
    $user_id = $conn->insert_id;
    
    // TODO: Send verification email (implement email service)
    // For now, we'll just return success
    
    http_response_code(201);
    echo json_encode([
        'success' => true,
        'message' => 'User registered successfully. Please check your email for verification.',
        'user_id' => $user_id,
        'email' => $email,
        'name' => $name
    ]);
} else {
    http_response_code(500);
    echo json_encode(['error' => 'Failed to create user: ' . $stmt->error]);
}

$stmt->close();
$conn->close();
