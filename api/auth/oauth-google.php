<?php
/**
 * Google OAuth 2.0 Integration
 * Handles Google OAuth authentication flow
 */

session_start();
require_once __DIR__ . '/../../config.php';
require_once __DIR__ . '/../../utilities.php';
require_once __DIR__ . '/JWTHandler.php';

// Google OAuth configuration
$google_client_id = getenv('GOOGLE_CLIENT_ID') ?: '';
$google_client_secret = getenv('GOOGLE_CLIENT_SECRET') ?: '';
$redirect_uri = getenv('APP_URL') . '/api/auth/oauth-callback.php';

if (empty($google_client_id) || empty($google_client_secret)) {
    http_response_code(500);
    echo json_encode(['error' => 'Google OAuth not configured']);
    exit;
}

// Generate state token for CSRF protection
$state = bin2hex(random_bytes(16));
$_SESSION['oauth_state'] = $state;

// Build Google OAuth authorization URL
$auth_url = 'https://accounts.google.com/o/oauth2/v2/auth?' . http_build_query([
    'client_id' => $google_client_id,
    'redirect_uri' => $redirect_uri,
    'response_type' => 'code',
    'scope' => 'openid email profile',
    'state' => $state,
    'access_type' => 'offline',
    'prompt' => 'consent'
]);

// Redirect to Google OAuth
header('Location: ' . $auth_url);
exit;
