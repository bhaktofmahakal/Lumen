<?php

require_once __DIR__ . '/../config.php';

// Use API_KEY from shared config instead of hardcoded value
// GEMINI_API_KEY is now defined in config.php from environment variables

// MODEL PREFERENCES ( Combo)
define('OLLAMA_DEFAULT_MODEL', 'qwen2.5-coder:7b-instruct');
define('OLLAMA_FALLBACK_MODEL', 'qwen2.5-coder:7b-instruct'); 
define('OLLAMA_ENDPOINT', 'http://localhost:11434/api/generate');

// local qwen2.5-coder + Cloud Gemini
define('USE_HYBRID_APPROACH', true);
define('PREFER_LOCAL_MODEL', true);
define('GEMINI_AS_FALLBACK', true);

// SETTINGS
define('AI_CACHE_DURATION', 24); // hours
define('AI_REQUEST_TIMEOUT', 60); // seconds - comprehensive analysis timeout
define('MAX_INPUT_SIZE', 15000); // characters - simple limit
define('MAX_OUTPUT_SIZE', 3000); // characters

define('DAILY_REQUEST_LIMIT', 100);
define('HOURLY_REQUEST_LIMIT', 20);

define('ENABLE_OLLAMA', true);
define('ENABLE_GEMINI', true);
define('ENABLE_CACHING', true);
define('ENABLE_ANALYTICS', true);

//  ERROR HANDLING
define('FALLBACK_TO_LOCAL', true);
define('LOG_AI_ERRORS', true);

define('REQUIRE_USER_AUTH', false); // Set to true in production
define('ALLOWED_ORIGINS', ['localhost', '127.0.0.1']);

define('AI_LOG_LEVEL', 'INFO'); // DEBUG, INFO, WARNING, ERROR
define('AI_LOG_FILE', 'logs/ai-service.log');

function getAIConfig() {
    return [
        'api_keys' => [
            'gemini' => API_KEY  // Use shared API_KEY constant from config.php
        ],
        'models' => [
            'ollama_default' => OLLAMA_DEFAULT_MODEL,
            'ollama_fallback' => OLLAMA_FALLBACK_MODEL,
            'endpoint' => OLLAMA_ENDPOINT
        ],
        'performance' => [
            'cache_duration' => AI_CACHE_DURATION,
            'timeout' => AI_REQUEST_TIMEOUT,
            'max_input' => MAX_INPUT_SIZE,
            'max_output' => MAX_OUTPUT_SIZE
        ],
        'limits' => [
            'daily' => DAILY_REQUEST_LIMIT,
            'hourly' => HOURLY_REQUEST_LIMIT
        ],
        'features' => [
            'ollama' => ENABLE_OLLAMA,
            'gemini' => ENABLE_GEMINI,
            'caching' => ENABLE_CACHING,
            'analytics' => ENABLE_ANALYTICS
        ],
        'security' => [
            'require_auth' => REQUIRE_USER_AUTH,
            'allowed_origins' => ALLOWED_ORIGINS
        ]
    ];
}

function validateAPIKeys() {
    $errors = [];
    
    if (empty(API_KEY)) {
        $errors[] = 'Gemini API key not configured';
    }
    
    // Test Ollama connection
    if (ENABLE_OLLAMA) {
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, OLLAMA_ENDPOINT);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_TIMEOUT, 5);
        curl_setopt($ch, CURLOPT_NOBODY, true);
        
        $result = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        
        if ($httpCode === 0) {
            $errors[] = 'Ollama service not running on ' . OLLAMA_ENDPOINT;
        }
    }
    
    return $errors;
}

function initializeAIService() {
    try {
        $errors = validateAPIKeys();
        
        if (!empty($errors)) {
            return [
                'success' => false,
                'errors' => $errors,
                'message' => 'AI service configuration incomplete'
            ];
        }
        
        return [
            'success' => true,
            'message' => 'AI service ready',
            'config' => getAIConfig()
        ];
        
    } catch (Exception $e) {
        return [
            'success' => false,
            'error' => $e->getMessage(),
            'message' => 'AI service initialization failed'
        ];
    }
}
?>