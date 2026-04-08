<?php
declare(strict_types=1);

require_once 'error_handler.php';
require_once 'database_logger.php';

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, GET, OPTIONS');
header('Access-control-allow-headers: Content-Type');
try {
    if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
        http_response_code(200);
        exit;
    }

    require_once 'config.php';
    require_once 'utilities.php';

    $conn = getDBConnection();

    if (session_status() === PHP_SESSION_NONE) {
        session_set_cookie_params([
            'lifetime' => 1800,
            'path' => '/',
            'domain' => '',
            'secure' => false,
            'httponly' => true,
            'samesite' => 'Lax'
        ]);

        if (!session_start()) {
            throw new Exception("Failed to start session. Streaming is unavailable.");
        }
    }

    // -------------------------------------------------------------------------
    // callGroqAPI() — Groq Cloud fallback (Circuit Breaker pattern)
    // -------------------------------------------------------------------------

    /**
     * Call the Groq Cloud API as a fallback when Gemini is unavailable.
     *
     * @param string $prompt  The user prompt text.
     * @param array  $parts   The parts array (text + optional image).
     * @return string         The text response from Groq.
     * @throws Exception      On curl error, HTTP error, or invalid response.
     */
    function callGroqAPI(string $prompt, array $parts): string
    {
        $groqApiKey = defined('GROQ_API_KEY') ? GROQ_API_KEY : '';
        if (empty($groqApiKey)) {
            throw new Exception("Groq API key is not configured.");
        }

        // Build the message content — Groq uses OpenAI-compatible format
        $messageContent = $prompt;

        $requestBody = [
            'model'       => 'llama3-8b-8192',
            'messages'    => [
                ['role' => 'user', 'content' => $messageContent]
            ],
            'temperature' => 0.8,
            'max_tokens'  => 1024,
        ];

        $ch = curl_init('https://api.groq.com/openai/v1/chat/completions');
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_POST           => true,
            CURLOPT_HTTPHEADER     => [
                'Content-Type: application/json',
                'Authorization: Bearer ' . $groqApiKey,
            ],
            CURLOPT_POSTFIELDS      => json_encode($requestBody),
            CURLOPT_TIMEOUT         => 20,
            CURLOPT_CONNECTTIMEOUT  => 10,
            CURLOPT_FOLLOWLOCATION  => true,
            CURLOPT_SSL_VERIFYPEER  => false,
            CURLOPT_USERAGENT       => 'ChatApp/1.0',
        ]);

        $res      = curl_exec($ch);
        $httpCode = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $errno    = curl_errno($ch);
        $curlErr  = curl_error($ch);
        curl_close($ch);

        // Distinguish error types (Circuit Breaker / Graceful Degradation)
        if ($errno === 28) {
            throw new Exception("The AI service is taking too long to respond. Please try again.");
        }
        if ($curlErr) {
            throw new Exception("Network error contacting Groq API: " . $curlErr);
        }
        if ($httpCode === 429) {
            throw new Exception("The AI service is currently busy. Please wait a moment and try again.");
        }
        if ($httpCode !== 200) {
            throw new Exception("Groq API HTTP error: $httpCode");
        }

        // Validate JSON
        $result = json_decode($res, true);
        if (json_last_error() !== JSON_ERROR_NONE) {
            error_log('Raw Groq API response: ' . substr($res, 0, 500));
            throw new Exception("Invalid Groq API response JSON.");
        }

        // Validate response structure (API contract testing)
        if (!isset($result['choices']) || empty($result['choices'])) {
            error_log('Groq API response missing choices: ' . substr($res, 0, 500));
            throw new Exception("Groq API returned an empty response.");
        }
        if (!isset($result['choices'][0]['message']['content'])) {
            error_log('Groq API response missing content: ' . substr($res, 0, 500));
            throw new Exception("Groq API response structure is invalid.");
        }

        return (string) $result['choices'][0]['message']['content'];
    }

    // -------------------------------------------------------------------------
    // streamResponse() — SSE streaming via Gemini
    // -------------------------------------------------------------------------

    function streamResponse(string $url, array $data): void
    {
        header('Content-Type: text/event-stream');
        header('Cache-Control: no-cache');
        header('Connection: keep-alive');
        header('Access-Control-Allow-Origin: *');

        if (ob_get_level()) {
            ob_end_clean();
        }

        $ch = curl_init($url . "&alt=sse");
        curl_setopt_array($ch, [
            CURLOPT_POST           => true,
            CURLOPT_HTTPHEADER     => ["Content-Type: application/json"],
            CURLOPT_POSTFIELDS     => json_encode($data),
            CURLOPT_TIMEOUT        => 30,
            CURLOPT_CONNECTTIMEOUT => 10,
            CURLOPT_SSL_VERIFYPEER => false,
            CURLOPT_FOLLOWLOCATION => true,
            CURLOPT_USERAGENT      => 'ChatApp/1.0',
            CURLOPT_WRITEFUNCTION  => function ($curl, $chunk) {
                echo $chunk;
                flush();
                return strlen($chunk);
            }
        ]);

        $result    = curl_exec($ch);
        $httpCode  = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $errno     = curl_errno($ch);
        $curlError = curl_error($ch);
        curl_close($ch);

        if ($errno === 28) {
            echo "data: " . json_encode(["error" => "The AI service is taking too long to respond. Please try again."]) . "\n\n";
            flush();
        } elseif ($curlError || $httpCode !== 200) {
            echo "data: " . json_encode([
                "error" => "Streaming failed: " . ($curlError ?: "HTTP $httpCode")
            ]) . "\n\n";
            flush();
        }

        exit;
    }

    // -------------------------------------------------------------------------
    // GET ?stream — SSE stream handler
    // -------------------------------------------------------------------------

    $ip = getIP();

    if ($_SERVER['REQUEST_METHOD'] === 'GET' && isset($_GET['stream'])) {
        // Re-open the session so we can read the pending_prompt that was stored
        // in the prepare step (which called session_write_close() to release the lock).
        if (session_status() === PHP_SESSION_NONE) {
            session_start();
        }

        error_log("Stream request - Session ID: " . (session_id() ?: 'none'));
        error_log("Session data: " . print_r($_SESSION, true));

        $streamToken = $_GET['token'] ?? '';

        if (!isset($_SESSION['pending_prompt']) || empty($_SESSION['pending_prompt']) ||
            !isset($_SESSION['stream_token']) || $_SESSION['stream_token'] !== $streamToken) {

            header('Content-Type: text/event-stream');
            header('Cache-Control: no-cache');
            header('Connection: keep-alive');
            header('Access-Control-Allow-Origin: *');

            http_response_code(400);
            echo "data: " . json_encode(["error" => "Session expired or invalid token. Please try again."]) . "\n\n";
            flush();
            exit;
        }

        $prompt = $_SESSION['pending_prompt'];
        $parts  = $_SESSION['pending_parts'] ?? [["text" => $prompt]];
        unset($_SESSION['pending_prompt']);
        unset($_SESSION['pending_parts']);
        unset($_SESSION['stream_token']);
        session_write_close();

        $url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=" . API_KEY;

        $systemPrompt   = getEnhancedSystemPrompt($prompt);
        $enhancedPrompt = $systemPrompt . "\n\nUser Request: " . $prompt;

        $parts[0] = ["text" => $enhancedPrompt];

        $data = [
            "contents"         => [["parts" => $parts]],
            "generationConfig" => [
                "temperature"     => 0.8,
                "topK"            => 50,
                "topP"            => 0.95,
                "maxOutputTokens" => 1024,
                "candidateCount"  => 1
            ],
            "safetySettings" => [
                ["category" => "HARM_CATEGORY_HARASSMENT",        "threshold" => "BLOCK_MEDIUM_AND_ABOVE"],
                ["category" => "HARM_CATEGORY_HATE_SPEECH",       "threshold" => "BLOCK_MEDIUM_AND_ABOVE"],
                ["category" => "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold" => "BLOCK_MEDIUM_AND_ABOVE"],
                ["category" => "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold" => "BLOCK_MEDIUM_AND_ABOVE"]
            ]
        ];
        streamResponse($url, $data);
    }

    // -------------------------------------------------------------------------
    // POST — non-streaming request handler
    // -------------------------------------------------------------------------

    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
        if (rateLimit($conn, $ip)) {
            http_response_code(429);
            throw new Exception('Rate limit exceeded.');
        }

        $prompt = '';
        $parts  = [];

        if (!empty($_FILES['image']) && $_FILES['image']['error'] === UPLOAD_ERR_OK) {
            error_log("Image upload detected - File name: " . $_FILES['image']['name']);
            error_log("Image file size: " . $_FILES['image']['size']);

            $prompt    = trim($_POST['prompt'] ?? '');
            $imageFile = $_FILES['image'];

            $fileType = mime_content_type($imageFile['tmp_name']);
            error_log("Detected file type: " . $fileType);

            if (!in_array($fileType, ['image/jpeg', 'image/png', 'image/gif', 'image/webp'])) {
                throw new Exception("Invalid file type: $fileType");
            }

            $base64Image = base64_encode(file_get_contents($imageFile['tmp_name']));
            error_log("Base64 image length: " . strlen($base64Image));

            $parts = [["text" => $prompt], ["inline_data" => ["mime_type" => $fileType, "data" => $base64Image]]];
            error_log("Created parts array with image data");
        } else {
            if (!empty($_FILES['image']) && $_FILES['image']['error'] !== UPLOAD_ERR_OK) {
                $errorMsg = match ($_FILES['image']['error']) {
                    UPLOAD_ERR_INI_SIZE  => 'File too large (exceeds server limit)',
                    UPLOAD_ERR_FORM_SIZE => 'File too large (exceeds form limit)',
                    UPLOAD_ERR_PARTIAL   => 'File was only partially uploaded',
                    UPLOAD_ERR_NO_FILE   => 'No file was uploaded',
                    UPLOAD_ERR_NO_TMP_DIR => 'Missing temporary folder',
                    UPLOAD_ERR_CANT_WRITE => 'Failed to write file to disk',
                    UPLOAD_ERR_EXTENSION  => 'File upload stopped by extension',
                    default               => 'Unknown upload error'
                };
                error_log("File upload error: " . $errorMsg);
                throw new Exception("File upload failed: " . $errorMsg);
            }

            $input = json_decode(file_get_contents('php://input'), true);
            if (json_last_error() !== JSON_ERROR_NONE) {
                throw new Exception('Invalid JSON input: ' . json_last_error_msg());
            }
            $prompt = trim($input['prompt'] ?? '');
            $parts  = [["text" => $prompt]];
        }

        if (empty($prompt) || strlen($prompt) > 3000) {
            throw new Exception("Prompt must be 1-3000 characters");
        }

        // ---- prepareStream: store data in session and release lock ----
        if (isset($_GET['prepareStream'])) {
            $_SESSION['pending_prompt'] = $prompt;
            $_SESSION['pending_parts']  = $parts;
            $streamToken                = md5(uniqid() . $prompt . time());
            $_SESSION['stream_token']   = $streamToken;

            // Release the session lock so the SSE stream handler can read it
            session_write_close();

            error_log("Prepared stream - Session ID: " . session_id());
            error_log("Stored prompt: " . substr($prompt, 0, 50) . "...");
            error_log("Stored parts count: " . count($parts));
            error_log("Stream token: " . $streamToken);

            echo json_encode([
                "status"       => "ready",
                "session_id"   => session_id(),
                "stream_token" => $streamToken
            ]);
            exit;
        }

        // ---- Non-streaming Gemini call with Groq fallback (Circuit Breaker) ----
        $url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=" . API_KEY;

        $systemPrompt   = getEnhancedSystemPrompt($prompt);
        $enhancedPrompt = $systemPrompt . "\n\nUser Request: " . $prompt;

        $parts[0] = ["text" => $enhancedPrompt];

        $data = [
            "contents"         => [["parts" => $parts]],
            "generationConfig" => [
                "temperature"     => 0.8,
                "topK"            => 50,
                "topP"            => 0.95,
                "maxOutputTokens" => 1024,
                "candidateCount"  => 1
            ],
            "safetySettings" => [
                ["category" => "HARM_CATEGORY_HARASSMENT",        "threshold" => "BLOCK_MEDIUM_AND_ABOVE"],
                ["category" => "HARM_CATEGORY_HATE_SPEECH",       "threshold" => "BLOCK_MEDIUM_AND_ABOVE"],
                ["category" => "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold" => "BLOCK_MEDIUM_AND_ABOVE"],
                ["category" => "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold" => "BLOCK_MEDIUM_AND_ABOVE"]
            ]
        ];

        $textResponse = null;
        $apiUsed      = 'gemini';

        try {
            $ch = curl_init($url);
            curl_setopt_array($ch, [
                CURLOPT_RETURNTRANSFER => true,
                CURLOPT_POST           => true,
                CURLOPT_HTTPHEADER     => ["Content-Type: application/json"],
                CURLOPT_POSTFIELDS     => json_encode($data),
                CURLOPT_TIMEOUT        => 20,
                CURLOPT_CONNECTTIMEOUT => 10,
                CURLOPT_FOLLOWLOCATION => true,
                CURLOPT_SSL_VERIFYPEER => false,
                CURLOPT_USERAGENT      => 'ChatApp/1.0'
            ]);
            $res      = curl_exec($ch);
            $httpCode = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
            $errno    = curl_errno($ch);
            $curlErr  = curl_error($ch);
            curl_close($ch);

            // Distinguish error types for user-friendly messages
            if ($errno === 28) {
                throw new Exception("The AI service is taking too long to respond. Please try again.");
            }
            if ($curlErr) {
                throw new Exception("Network error: " . $curlErr);
            }
            if ($httpCode === 429) {
                throw new Exception("The AI service is currently busy. Please wait a moment and try again.");
            }
            if ($httpCode !== 200) {
                throw new Exception("API HTTP error: $httpCode - " . substr($res, 0, 200));
            }

            // Validate JSON response
            $result = json_decode($res, true);
            if (json_last_error() !== JSON_ERROR_NONE) {
                error_log('Raw API response: ' . substr($res, 0, 500));
                throw new Exception("Invalid API response JSON.");
            }

            // Validate response structure (API contract testing)
            if (!isset($result['candidates']) || empty($result['candidates'])) {
                error_log('Gemini API response missing candidates: ' . substr($res, 0, 500));
                throw new Exception("AI response blocked or empty. Please rephrase your request.");
            }
            if (!isset($result['candidates'][0]['content']['parts']) || empty($result['candidates'][0]['content']['parts'])) {
                error_log('Gemini API response missing parts: ' . substr($res, 0, 500));
                throw new Exception("AI response structure is invalid. Please try again.");
            }

            $textResponse = $result['candidates'][0]['content']['parts'][0]['text'] ?? null;
            if ($textResponse === null || $textResponse === '') {
                error_log('Gemini API response missing text: ' . substr($res, 0, 500));
                throw new Exception("AI returned an empty response. Please try again.");
            }

        } catch (Exception $geminiException) {
            // Gemini failed — attempt Groq fallback (Circuit Breaker pattern)
            error_log("Gemini API failed, attempting Groq fallback: " . $geminiException->getMessage());
            try {
                $textResponse = callGroqAPI($prompt, $parts);
                $apiUsed      = 'groq';
                error_log("Groq fallback succeeded for prompt: " . substr($prompt, 0, 50));
            } catch (Exception $groqException) {
                // Both APIs failed — surface the most user-friendly message
                error_log("Groq fallback also failed: " . $groqException->getMessage());
                throw new Exception($geminiException->getMessage());
            }
        }

        // Log which API was used for analytics
        error_log("API used: $apiUsed for request from IP: $ip");

        saveChat($conn, $ip, $prompt, $textResponse);

        echo json_encode(["response" => $textResponse]);

    } else {
        throw new Exception('Method not allowed.');
    }

} catch (Throwable $e) {
    throw $e;
}
?>
