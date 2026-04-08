<?php
/**
 * OAuth Callback Handler
 * Handles OAuth callback from Google and creates/links user accounts
 */

session_start();
require_once __DIR__ . '/../../config.php';
require_once __DIR__ . '/../../utilities.php';
require_once __DIR__ . '/JWTHandler.php';

// Google OAuth configuration
$google_client_id = getenv('GOOGLE_CLIENT_ID') ?: '';
$google_client_secret = getenv('GOOGLE_CLIENT_SECRET') ?: '';
$redirect_uri = getenv('APP_URL') . '/api/auth/oauth-callback.php';

// Validate state token for CSRF protection
$state = $_GET['state'] ?? '';
$session_state = $_SESSION['oauth_state'] ?? '';

if (empty($state) || $state !== $session_state) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid state parameter']);
    exit;
}

// Get authorization code
$code = $_GET['code'] ?? '';

if (empty($code)) {
    http_response_code(400);
    echo json_encode(['error' => 'Authorization code not provided']);
    exit;
}

// Exchange authorization code for access token
$token_url = 'https://oauth2.googleapis.com/token';
$token_data = [
    'code' => $code,
    'client_id' => $google_client_id,
    'client_secret' => $google_client_secret,
    'redirect_uri' => $redirect_uri,
    'grant_type' => 'authorization_code'
];

$ch = curl_init($token_url);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_POSTFIELDS, http_build_query($token_data));
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
$token_response = curl_exec($ch);
curl_close($ch);

$token_result = json_decode($token_response, true);

if (!isset($token_result['access_token'])) {
    http_response_code(500);
    echo json_encode(['error' => 'Failed to obtain access token']);
    exit;
}

$access_token = $token_result['access_token'];

// Get user info from Google
$userinfo_url = 'https://www.googleapis.com/oauth2/v2/userinfo';
$ch = curl_init($userinfo_url);
curl_setopt($ch, CURLOPT_HTTPHEADER, ['Authorization: Bearer ' . $access_token]);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
$userinfo_response = curl_exec($ch);
curl_close($ch);

$userinfo = json_decode($userinfo_response, true);

if (!isset($userinfo['email'])) {
    http_response_code(500);
    echo json_encode(['error' => 'Failed to obtain user information']);
    exit;
}

// Extract user data
$oauth_id = $userinfo['id'];
$email = $userinfo['email'];
$name = $userinfo['name'] ?? '';
$oauth_provider = 'google';

// Connect to database
$conn = getDBConnection();
if (!$conn) {
    http_response_code(500);
    echo json_encode(['error' => 'Database connection failed']);
    exit;
}

// Check if user exists with this OAuth account
$stmt = $conn->prepare("SELECT id, email, name, role, subscription_tier FROM users WHERE oauth_provider = ? AND oauth_id = ? AND deleted_at IS NULL");
$stmt->bind_param("ss", $oauth_provider, $oauth_id);
$stmt->execute();
$result = $stmt->get_result();

if ($result->num_rows > 0) {
    // User exists, log them in
    $user = $result->fetch_assoc();
} else {
    // Check if user exists with this email
    $stmt = $conn->prepare("SELECT id, email, name, role, subscription_tier, oauth_provider, oauth_id FROM users WHERE email = ? AND deleted_at IS NULL");
    $stmt->bind_param("s", $email);
    $stmt->execute();
    $result = $stmt->get_result();
    
    if ($result->num_rows > 0) {
        // User exists with email, link OAuth account
        $user = $result->fetch_assoc();
        
        if (empty($user['oauth_provider'])) {
            // Link OAuth account to existing user
            $stmt = $conn->prepare("UPDATE users SET oauth_provider = ?, oauth_id = ?, email_verified_at = NOW() WHERE id = ?");
            $stmt->bind_param("ssi", $oauth_provider, $oauth_id, $user['id']);
            $stmt->execute();
        }
    } else {
        // Create new user
        $stmt = $conn->prepare("INSERT INTO users (email, name, oauth_provider, oauth_id, email_verified_at, role, subscription_tier) VALUES (?, ?, ?, ?, NOW(), 'user', 'free')");
        $stmt->bind_param("ssss", $email, $name, $oauth_provider, $oauth_id);
        $stmt->execute();
        
        $user = [
            'id' => $conn->insert_id,
            'email' => $email,
            'name' => $name,
            'role' => 'user',
            'subscription_tier' => 'free'
        ];
    }
}

$stmt->close();

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

// Start PHP session
$_SESSION['user_id'] = $user['id'];
$_SESSION['email'] = $user['email'];
$_SESSION['role'] = $user['role'];
$_SESSION['session_id'] = $session_id;

$conn->close();

// Redirect to application with token
$app_url = getenv('APP_URL') ?: 'http://localhost';
header('Location: ' . $app_url . '?token=' . urlencode($token));
exit;
