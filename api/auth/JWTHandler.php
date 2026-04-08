<?php
/**
 * JWT Token Handler
 * Handles JWT token generation and validation
 */

class JWTHandler {
    private $secret_key;
    private $algorithm = 'HS256';
    private $token_expiry = 604800; // 7 days in seconds
    
    public function __construct() {
        // Get secret key from environment or generate one
        $this->secret_key = getenv('JWT_SECRET') ?: $this->generateSecretKey();
    }
    
    /**
     * Generate a JWT token
     * 
     * @param array $payload User data to encode in token
     * @return string JWT token
     */
    public function generateToken($payload) {
        $header = [
            'typ' => 'JWT',
            'alg' => $this->algorithm
        ];
        
        $issued_at = time();
        $expiration = $issued_at + $this->token_expiry;
        
        $token_payload = array_merge($payload, [
            'iat' => $issued_at,
            'exp' => $expiration
        ]);
        
        $header_encoded = $this->base64UrlEncode(json_encode($header));
        $payload_encoded = $this->base64UrlEncode(json_encode($token_payload));
        
        $signature = hash_hmac('sha256', "$header_encoded.$payload_encoded", $this->secret_key, true);
        $signature_encoded = $this->base64UrlEncode($signature);
        
        return "$header_encoded.$payload_encoded.$signature_encoded";
    }
    
    /**
     * Validate and decode a JWT token
     * 
     * @param string $token JWT token to validate
     * @return array|false Decoded payload or false if invalid
     */
    public function validateToken($token) {
        $parts = explode('.', $token);
        
        if (count($parts) !== 3) {
            return false;
        }
        
        list($header_encoded, $payload_encoded, $signature_encoded) = $parts;
        
        // Verify signature
        $signature = hash_hmac('sha256', "$header_encoded.$payload_encoded", $this->secret_key, true);
        $signature_check = $this->base64UrlEncode($signature);
        
        if ($signature_encoded !== $signature_check) {
            return false;
        }
        
        // Decode payload
        $payload = json_decode($this->base64UrlDecode($payload_encoded), true);
        
        if (!$payload) {
            return false;
        }
        
        // Check expiration
        if (isset($payload['exp']) && $payload['exp'] < time()) {
            return false;
        }
        
        return $payload;
    }
    
    /**
     * Extract token from Authorization header
     * 
     * @return string|null Token or null if not found
     */
    public function getTokenFromHeader() {
        $headers = getallheaders();
        
        if (isset($headers['Authorization'])) {
            $auth_header = $headers['Authorization'];
            
            if (preg_match('/Bearer\s+(.*)$/i', $auth_header, $matches)) {
                return $matches[1];
            }
        }
        
        return null;
    }
    
    /**
     * Base64 URL encode
     * 
     * @param string $data Data to encode
     * @return string Encoded data
     */
    private function base64UrlEncode($data) {
        return rtrim(strtr(base64_encode($data), '+/', '-_'), '=');
    }
    
    /**
     * Base64 URL decode
     * 
     * @param string $data Data to decode
     * @return string Decoded data
     */
    private function base64UrlDecode($data) {
        return base64_decode(strtr($data, '-_', '+/'));
    }
    
    /**
     * Generate a secure secret key
     * 
     * @return string Secret key
     */
    private function generateSecretKey() {
        return bin2hex(random_bytes(32));
    }
}
