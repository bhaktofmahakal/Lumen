<?php
/**
 * Authentication Middleware
 * Validates JWT tokens and protects API endpoints
 */

require_once __DIR__ . '/JWTHandler.php';
require_once __DIR__ . '/../../config.php';

class AuthMiddleware {
    private $jwt_handler;
    
    public function __construct() {
        $this->jwt_handler = new JWTHandler();
    }
    
    /**
     * Authenticate request and return user data
     * 
     * @return array|false User data or false if authentication fails
     */
    public function authenticate() {
        $token = $this->jwt_handler->getTokenFromHeader();
        
        if (!$token) {
            http_response_code(401);
            echo json_encode(['error' => 'Authentication required']);
            return false;
        }
        
        $payload = $this->jwt_handler->validateToken($token);
        
        if (!$payload) {
            http_response_code(401);
            echo json_encode(['error' => 'Invalid or expired token']);
            return false;
        }
        
        return $payload;
    }
    
    /**
     * Require authentication for endpoint
     * Exits if authentication fails
     * 
     * @return array User data
     */
    public function requireAuth() {
        $user = $this->authenticate();
        
        if (!$user) {
            exit;
        }
        
        return $user;
    }
    
    /**
     * Check if user has required role
     * 
     * @param array $user User data
     * @param string|array $required_roles Required role(s)
     * @return bool True if user has required role
     */
    public function hasRole($user, $required_roles) {
        if (!is_array($required_roles)) {
            $required_roles = [$required_roles];
        }
        
        return in_array($user['role'], $required_roles);
    }
    
    /**
     * Require specific role for endpoint
     * Exits if user doesn't have required role
     * 
     * @param array $user User data
     * @param string|array $required_roles Required role(s)
     */
    public function requireRole($user, $required_roles) {
        if (!$this->hasRole($user, $required_roles)) {
            http_response_code(403);
            echo json_encode(['error' => 'Insufficient permissions']);
            exit;
        }
    }
}
