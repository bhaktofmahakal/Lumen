<?php
// Load environment variables from .env file
if (file_exists(__DIR__ . '/.env')) {
    $lines = file(__DIR__ . '/.env', FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    foreach ($lines as $line) {
        if (strpos(trim($line), '#') === 0) continue;
        list($name, $value) = explode('=', $line, 2);
        $name = trim($name);
        $value = trim($value);
        if (!getenv($name)) {
            putenv("$name=$value");
        }
    }
}

// API Keys from environment variables
define('API_KEY', getenv('GEMINI_API_KEY') ?: '');
define('GROQ_API_KEY', getenv('GROQ_API_KEY') ?: '');

// Database configuration
define('DB_HOST', 'localhost');
define('DB_USER', 'root');
define('DB_PASS', '');
define('DB_NAME', 'chat_app');

// Rate limiting
define('TIME_WINDOW', 60);
define('RATE_LIMIT', 10);
// Validation function to check if API keys are configured
function validateAPIKeys() {
    $errors = [];
    
    if (empty(API_KEY)) {
        $errors[] = 'GEMINI_API_KEY not configured in environment';
    }
    
    if (empty(GROQ_API_KEY)) {
        $errors[] = 'GROQ_API_KEY not configured in environment';
    }
    
    return $errors;
}

function getDBConnection() {
    try {
        $conn = new mysqli(DB_HOST, DB_USER, DB_PASS, DB_NAME);
        if ($conn->connect_error) {
            error_log("Database connection failed: " . $conn->connect_error);
            return false;
        }
        $conn->set_charset("utf8mb4");
        return $conn;
    } catch (Exception $e) {
        error_log("Database connection error: " . $e->getMessage());
        return false;
    }
}
?>

