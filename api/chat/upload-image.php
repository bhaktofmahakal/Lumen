<?php
/**
 * Image Upload for Chat Queries API
 * Handles image upload and OCR extraction
 * Requirements: 4.10
 */

require_once __DIR__ . '/../auth/AuthMiddleware.php';
require_once __DIR__ . '/../../config.php';

header('Content-Type: application/json');

// Enable CORS
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
    exit;
}

// Authenticate user
$auth = new AuthMiddleware();
$user = $auth->requireAuth();

try {
    // Validate file upload
    if (!isset($_FILES['image'])) {
        http_response_code(400);
        echo json_encode(['error' => 'No image file provided']);
        exit;
    }
    
    $file = $_FILES['image'];
    $session_id = $_POST['session_id'] ?? null;
    $query = $_POST['query'] ?? '';
    
    if (!$session_id) {
        http_response_code(400);
        echo json_encode(['error' => 'session_id is required']);
        exit;
    }
    
    // Validate file type
    $allowed_types = ['image/jpeg', 'image/png', 'image/jpg', 'image/webp'];
    $finfo = finfo_open(FILEINFO_MIME_TYPE);
    $mime_type = finfo_file($finfo, $file['tmp_name']);
    finfo_close($finfo);
    
    if (!in_array($mime_type, $allowed_types)) {
        http_response_code(400);
        echo json_encode(['error' => 'Invalid file type. Only JPEG, PNG, and WebP images are allowed']);
        exit;
    }
    
    // Validate file size (max 10MB)
    $max_size = 10 * 1024 * 1024; // 10MB
    if ($file['size'] > $max_size) {
        http_response_code(400);
        echo json_encode(['error' => 'File size exceeds 10MB limit']);
        exit;
    }
    
    // Read file content
    $image_content = file_get_contents($file['tmp_name']);
    $image_base64 = base64_encode($image_content);
    
    // Call Python AI service for OCR extraction
    $ocr_result = extractTextFromImage($image_base64, $mime_type);
    
    if (!$ocr_result['success']) {
        http_response_code(500);
        echo json_encode([
            'error' => 'Failed to extract text from image',
            'details' => $ocr_result['error'] ?? 'Unknown error'
        ]);
        exit;
    }
    
    $extracted_text = $ocr_result['text'];
    
    // Combine query with extracted text
    $combined_query = $query;
    if (!empty($extracted_text)) {
        $combined_query .= "\n\n[Image content]: " . $extracted_text;
    }
    
    echo json_encode([
        'success' => true,
        'extracted_text' => $extracted_text,
        'combined_query' => $combined_query,
        'message' => 'Image processed successfully'
    ]);
    
} catch (Exception $e) {
    error_log("Image upload error: " . $e->getMessage());
    http_response_code(500);
    echo json_encode(['error' => 'Internal server error']);
}

/**
 * Extract text from image using OCR
 */
function extractTextFromImage($image_base64, $mime_type) {
    $ai_service_url = getenv('AI_SERVICE_URL') ?: 'http://ai-services:8000';
    
    $payload = [
        'image_base64' => $image_base64,
        'mime_type' => $mime_type
    ];
    
    $ch = curl_init($ai_service_url . '/api/ocr/extract');
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($payload));
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'Content-Type: application/json'
    ]);
    curl_setopt($ch, CURLOPT_TIMEOUT, 30);
    
    $response = curl_exec($ch);
    $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $error = curl_error($ch);
    curl_close($ch);
    
    if ($error) {
        error_log("OCR service error: " . $error);
        return ['success' => false, 'error' => $error];
    }
    
    if ($http_code !== 200) {
        error_log("OCR service returned HTTP $http_code: " . $response);
        return ['success' => false, 'error' => "HTTP $http_code"];
    }
    
    $data = json_decode($response, true);
    
    if (!$data) {
        error_log("Failed to decode OCR service response");
        return ['success' => false, 'error' => 'Invalid response format'];
    }
    
    return ['success' => true, 'text' => $data['text'] ?? ''];
}
