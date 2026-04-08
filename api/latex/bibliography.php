<?php
/**
 * AI-Assisted LaTeX Writing - Generate Bibliography
 * Proxies requests to Python FastAPI service
 * Requirements: 8.8
 */

require_once __DIR__ . '/../auth/AuthMiddleware.php';

header('Content-Type: application/json');

// Authenticate user
$auth = new AuthMiddleware();
$user = $auth->authenticate();

if (!$user) {
    http_response_code(401);
    echo json_encode(['error' => 'Unauthorized']);
    exit;
}

// Only allow POST requests
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
    exit;
}

// Get request body
$input = json_decode(file_get_contents('php://input'), true);

if (!$input) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid JSON input']);
    exit;
}

// Validate required fields
$required_fields = ['citation_ids', 'project_id'];
foreach ($required_fields as $field) {
    if (!isset($input[$field])) {
        http_response_code(400);
        echo json_encode(['error' => "Missing required field: $field"]);
        exit;
    }
}

// Validate citation_ids is array
if (!is_array($input['citation_ids'])) {
    http_response_code(400);
    echo json_encode(['error' => 'citation_ids must be an array']);
    exit;
}

// Set default style
$input['style'] = $input['style'] ?? 'APA';

// Forward request to Python FastAPI service
$python_api_url = getenv('PYTHON_API_URL') ?: 'http://localhost:8000';
$endpoint = $python_api_url . '/api/latex/bibliography';

$ch = curl_init($endpoint);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($input));
curl_setopt($ch, CURLOPT_HTTPHEADER, [
    'Content-Type: application/json',
    'Accept: application/json'
]);
curl_setopt($ch, CURLOPT_TIMEOUT, 30);

$response = curl_exec($ch);
$http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
$curl_error = curl_error($ch);
curl_close($ch);

if ($curl_error) {
    error_log("Bibliography generation API error: $curl_error");
    http_response_code(500);
    echo json_encode(['error' => 'Failed to connect to AI service']);
    exit;
}

// Forward response
http_response_code($http_code);
echo $response;
