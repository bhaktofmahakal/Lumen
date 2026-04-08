<?php
/**
 * LaTeX Template Management API
 * Requirements: 9.1, 9.2, 9.3, 9.4, 9.5
 */

require_once __DIR__ . '/../auth/AuthMiddleware.php';

header('Content-Type: application/json');

// Enable CORS
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

// Authenticate user
$auth = new AuthMiddleware();
$user = $auth->authenticate();

if (!$user) {
    http_response_code(401);
    echo json_encode(['error' => 'Unauthorized']);
    exit();
}

$method = $_SERVER['REQUEST_METHOD'];
$path = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
$pathParts = explode('/', trim($path, '/'));

// AI services base URL
$AI_SERVICES_URL = getenv('AI_SERVICES_URL') ?: 'http://ai-services:8000';

/**
 * Forward request to Python AI services
 */
function forwardToAIServices($endpoint, $method = 'GET', $data = null) {
    global $AI_SERVICES_URL;
    
    $url = $AI_SERVICES_URL . $endpoint;
    
    $ch = curl_init($url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_CUSTOMREQUEST, $method);
    
    if ($data !== null) {
        curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
        curl_setopt($ch, CURLOPT_HTTPHEADER, [
            'Content-Type: application/json',
            'Content-Length: ' . strlen(json_encode($data))
        ]);
    }
    
    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    
    http_response_code($httpCode);
    return $response;
}

// Route handling
try {
    switch ($method) {
        case 'GET':
            if (end($pathParts) === 'templates' || end($pathParts) === 'list') {
                // List templates - Requirement 9.1
                $templateType = $_GET['template_type'] ?? null;
                $includeBuiltin = isset($_GET['include_builtin']) ? filter_var($_GET['include_builtin'], FILTER_VALIDATE_BOOLEAN) : true;
                $includeCustom = isset($_GET['include_custom']) ? filter_var($_GET['include_custom'], FILTER_VALIDATE_BOOLEAN) : true;
                
                $queryParams = http_build_query([
                    'template_type' => $templateType,
                    'user_id' => $user['id'],
                    'include_builtin' => $includeBuiltin ? 'true' : 'false',
                    'include_custom' => $includeCustom ? 'true' : 'false'
                ]);
                
                echo forwardToAIServices("/api/templates/list?{$queryParams}", 'GET');
                
            } elseif (isset($pathParts[count($pathParts) - 2]) && $pathParts[count($pathParts) - 2] === 'templates') {
                // Get specific template - Requirement 9.2
                $templateId = end($pathParts);
                
                $queryParams = http_build_query(['user_id' => $user['id']]);
                echo forwardToAIServices("/api/templates/{$templateId}?{$queryParams}", 'GET');
                
            } elseif (in_array('outline', $pathParts)) {
                // Get outline
                $outlineId = end($pathParts);
                $queryParams = http_build_query(['user_id' => $user['id']]);
                
                echo forwardToAIServices("/api/templates/outline/{$outlineId}?{$queryParams}", 'GET');
                
            } else {
                http_response_code(404);
                echo json_encode(['error' => 'Endpoint not found']);
            }
            break;
            
        case 'POST':
            $input = json_decode(file_get_contents('php://input'), true);
            
            if (!$input) {
                http_response_code(400);
                echo json_encode(['error' => 'Invalid JSON input']);
                exit();
            }
            
            if (end($pathParts) === 'customize') {
                // Customize template - Requirement 9.3
                if (!isset($input['template_id']) || !isset($input['customization'])) {
                    http_response_code(400);
                    echo json_encode(['error' => 'Missing required fields: template_id, customization']);
                    exit();
                }
                
                $data = [
                    'template_id' => $input['template_id'],
                    'user_id' => $user['id'],
                    'customization' => $input['customization']
                ];
                
                echo forwardToAIServices('/api/templates/customize', 'POST', $data);
                
            } elseif (end($pathParts) === 'save') {
                // Save custom template - Requirement 9.5
                if (!isset($input['name']) || !isset($input['template_type']) || !isset($input['content'])) {
                    http_response_code(400);
                    echo json_encode(['error' => 'Missing required fields: name, template_type, content']);
                    exit();
                }
                
                $data = [
                    'name' => $input['name'],
                    'description' => $input['description'] ?? null,
                    'template_type' => $input['template_type'],
                    'content' => $input['content'],
                    'user_id' => $user['id'],
                    'project_id' => $input['project_id'] ?? null,
                    'is_public' => $input['is_public'] ?? false,
                    'customization_options' => $input['customization_options'] ?? null,
                    'default_settings' => $input['default_settings'] ?? null,
                    'tags' => $input['tags'] ?? null
                ];
                
                echo forwardToAIServices('/api/templates/save', 'POST', $data);
                
            } elseif (in_array('outline', $pathParts) && end($pathParts) === 'generate') {
                // Generate outline - Requirement 9.4
                if (!isset($input['research_topic']) || !isset($input['project_id'])) {
                    http_response_code(400);
                    echo json_encode(['error' => 'Missing required fields: research_topic, project_id']);
                    exit();
                }
                
                $data = [
                    'research_topic' => $input['research_topic'],
                    'project_id' => $input['project_id'],
                    'user_id' => $user['id'],
                    'document_ids' => $input['document_ids'] ?? null,
                    'document_type' => $input['document_type'] ?? 'article'
                ];
                
                echo forwardToAIServices('/api/templates/outline/generate', 'POST', $data);
                
            } else {
                http_response_code(404);
                echo json_encode(['error' => 'Endpoint not found']);
            }
            break;
            
        case 'DELETE':
            if (isset($pathParts[count($pathParts) - 2]) && $pathParts[count($pathParts) - 2] === 'templates') {
                // Delete custom template - Requirement 9.5
                $templateId = end($pathParts);
                $queryParams = http_build_query(['user_id' => $user['id']]);
                
                echo forwardToAIServices("/api/templates/{$templateId}?{$queryParams}", 'DELETE');
                
            } else {
                http_response_code(404);
                echo json_encode(['error' => 'Endpoint not found']);
            }
            break;
            
        default:
            http_response_code(405);
            echo json_encode(['error' => 'Method not allowed']);
            break;
    }
    
} catch (Exception $e) {
    error_log("Template API error: " . $e->getMessage());
    http_response_code(500);
    echo json_encode([
        'error' => 'Internal server error',
        'message' => $e->getMessage()
    ]);
}
