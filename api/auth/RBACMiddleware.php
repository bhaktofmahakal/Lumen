<?php
/**
 * Role-Based Access Control (RBAC) Middleware
 * Manages permissions and role-based access to resources
 */

require_once __DIR__ . '/AuthMiddleware.php';
require_once __DIR__ . '/../../config.php';

class RBACMiddleware {
    private $auth_middleware;
    
    // Define role hierarchy (higher number = more permissions)
    private $role_hierarchy = [
        'viewer' => 1,
        'editor' => 2,
        'admin' => 3
    ];
    
    // Define permissions for each role
    private $role_permissions = [
        'viewer' => [
            'project.view',
            'document.view',
            'chat.view',
            'latex.view'
        ],
        'editor' => [
            'project.view',
            'project.edit',
            'document.view',
            'document.upload',
            'document.delete',
            'chat.view',
            'chat.create',
            'latex.view',
            'latex.edit',
            'latex.compile'
        ],
        'admin' => [
            'project.view',
            'project.edit',
            'project.delete',
            'project.share',
            'document.view',
            'document.upload',
            'document.delete',
            'chat.view',
            'chat.create',
            'chat.delete',
            'latex.view',
            'latex.edit',
            'latex.compile',
            'latex.delete',
            'collaborator.add',
            'collaborator.remove',
            'collaborator.edit'
        ]
    ];
    
    public function __construct() {
        $this->auth_middleware = new AuthMiddleware();
    }
    
    /**
     * Check if user has permission
     * 
     * @param array $user User data
     * @param string $permission Permission to check
     * @return bool True if user has permission
     */
    public function hasPermission($user, $permission) {
        $role = $user['role'] ?? 'viewer';
        
        // System admin has all permissions
        if ($role === 'admin' && isset($user['subscription_tier'])) {
            return true;
        }
        
        // Check if role has permission
        if (isset($this->role_permissions[$role])) {
            return in_array($permission, $this->role_permissions[$role]);
        }
        
        return false;
    }
    
    /**
     * Require permission for endpoint
     * 
     * @param array $user User data
     * @param string $permission Required permission
     */
    public function requirePermission($user, $permission) {
        if (!$this->hasPermission($user, $permission)) {
            http_response_code(403);
            echo json_encode([
                'error' => 'Insufficient permissions',
                'required_permission' => $permission
            ]);
            exit;
        }
    }
    
    /**
     * Check if user has access to project
     * 
     * @param int $user_id User ID
     * @param int $project_id Project ID
     * @return array|false Project collaborator data or false if no access
     */
    public function checkProjectAccess($user_id, $project_id) {
        $conn = getDBConnection();
        if (!$conn) {
            return false;
        }
        
        // Check if user is project owner
        $stmt = $conn->prepare("SELECT id, user_id FROM projects WHERE id = ? AND user_id = ? AND deleted_at IS NULL");
        $stmt->bind_param("ii", $project_id, $user_id);
        $stmt->execute();
        $result = $stmt->get_result();
        
        if ($result->num_rows > 0) {
            $stmt->close();
            $conn->close();
            return [
                'role' => 'admin',
                'is_owner' => true
            ];
        }
        $stmt->close();
        
        // Check if user is collaborator
        $stmt = $conn->prepare("SELECT role, accepted_at FROM project_collaborators WHERE project_id = ? AND user_id = ? AND accepted_at IS NOT NULL");
        $stmt->bind_param("ii", $project_id, $user_id);
        $stmt->execute();
        $result = $stmt->get_result();
        
        if ($result->num_rows > 0) {
            $collaborator = $result->fetch_assoc();
            $stmt->close();
            $conn->close();
            return [
                'role' => $collaborator['role'],
                'is_owner' => false
            ];
        }
        
        $stmt->close();
        $conn->close();
        return false;
    }
    
    /**
     * Require project access with specific role
     * 
     * @param int $user_id User ID
     * @param int $project_id Project ID
     * @param string $required_role Required role (viewer, editor, admin)
     * @return array Project access data
     */
    public function requireProjectAccess($user_id, $project_id, $required_role = 'viewer') {
        $access = $this->checkProjectAccess($user_id, $project_id);
        
        if (!$access) {
            http_response_code(403);
            echo json_encode(['error' => 'Access denied to this project']);
            exit;
        }
        
        // Check if user has required role level
        $user_role_level = $this->role_hierarchy[$access['role']] ?? 0;
        $required_role_level = $this->role_hierarchy[$required_role] ?? 0;
        
        if ($user_role_level < $required_role_level) {
            http_response_code(403);
            echo json_encode([
                'error' => 'Insufficient permissions for this action',
                'required_role' => $required_role,
                'current_role' => $access['role']
            ]);
            exit;
        }
        
        return $access;
    }
}
