# Authentication and Access Control System

This directory contains the authentication and authorization system for the AI Research Copilot platform.

## Features

### 1. User Registration and Login (Task 2.1)
- Email/password authentication with bcrypt password hashing
- JWT token generation and validation
- Email verification (basic implementation)
- Session management with database persistence
- Password requirements: minimum 8 characters, uppercase, lowercase, number, special character

### 2. OAuth 2.0 Integration (Task 2.3)
- Google OAuth authentication
- Automatic account linking for existing users
- New user creation from OAuth profile

### 3. Role-Based Access Control (Task 2.4)
- Three role levels: viewer, editor, admin
- Permission-based access control
- Project-level access control with collaborator roles
- Project sharing with role assignment

## API Endpoints

### Registration
```
POST /api/auth/register.php
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "name": "John Doe"
}
```

### Login
```
POST /api/auth/login.php
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!"
}

Response:
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "session_id": "abc123...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "John Doe",
    "role": "user",
    "subscription_tier": "free"
  }
}
```

### Logout
```
POST /api/auth/logout.php
Authorization: Bearer <token>
```

### Google OAuth
```
GET /api/auth/oauth-google.php
```
Redirects to Google OAuth consent screen, then back to callback URL.

### Email Verification
```
GET /api/auth/verify-email.php?user_id=<id>&token=<token>
```

### Project Sharing
```
POST /api/projects/share.php
Authorization: Bearer <token>
Content-Type: application/json

{
  "project_id": 1,
  "email": "collaborator@example.com",
  "role": "editor"
}
```

### List Collaborators
```
GET /api/projects/collaborators.php?project_id=1
Authorization: Bearer <token>
```

### Update Collaborator Role
```
PUT /api/projects/collaborators.php
Authorization: Bearer <token>
Content-Type: application/json

{
  "project_id": 1,
  "user_id": 2,
  "role": "admin"
}
```

### Remove Collaborator
```
DELETE /api/projects/collaborators.php
Authorization: Bearer <token>
Content-Type: application/json

{
  "project_id": 1,
  "user_id": 2
}
```

## Usage Examples

### Protecting an Endpoint with Authentication
```php
<?php
require_once __DIR__ . '/../auth/AuthMiddleware.php';

$auth = new AuthMiddleware();
$user = $auth->requireAuth();

// User is authenticated, proceed with endpoint logic
echo json_encode(['user_id' => $user['user_id']]);
```

### Checking Permissions
```php
<?php
require_once __DIR__ . '/../auth/RBACMiddleware.php';

$rbac = new RBACMiddleware();

// Check if user has permission
if ($rbac->hasPermission($user, 'document.upload')) {
    // Allow document upload
}

// Require permission (exits if not authorized)
$rbac->requirePermission($user, 'project.delete');
```

### Checking Project Access
```php
<?php
require_once __DIR__ . '/../auth/RBACMiddleware.php';

$rbac = new RBACMiddleware();

// Check if user has access to project
$access = $rbac->checkProjectAccess($user['user_id'], $project_id);

if ($access) {
    echo "User role: " . $access['role'];
    echo "Is owner: " . ($access['is_owner'] ? 'yes' : 'no');
}

// Require specific role level (exits if insufficient permissions)
$access = $rbac->requireProjectAccess($user['user_id'], $project_id, 'editor');
```

## Roles and Permissions

### Viewer
- project.view
- document.view
- chat.view
- latex.view

### Editor
All viewer permissions plus:
- project.edit
- document.upload
- document.delete
- chat.create
- latex.edit
- latex.compile

### Admin
All editor permissions plus:
- project.delete
- project.share
- chat.delete
- latex.delete
- collaborator.add
- collaborator.remove
- collaborator.edit

## Security Features

1. **Password Hashing**: bcrypt with cost factor 12
2. **JWT Tokens**: HMAC-SHA256 signed tokens with 7-day expiration
3. **CSRF Protection**: State tokens for OAuth flows
4. **Session Management**: Database-backed sessions with IP and user agent tracking
5. **Email Verification**: Required before login
6. **Role-Based Access**: Granular permission system

## Environment Variables

Add these to your `.env` file:

```
JWT_SECRET=your_secure_random_secret_key_here
JWT_EXPIRATION=604800
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
APP_URL=http://localhost
```

## Testing

Run authentication tests:
```bash
./vendor/bin/phpunit tests/AuthenticationTest.php
```

Run RBAC tests:
```bash
./vendor/bin/phpunit tests/RBACTest.php
```

## Database Schema

The authentication system uses the following tables:
- `users`: User accounts
- `sessions`: Active sessions
- `projects`: User projects
- `project_collaborators`: Project sharing and roles

See `docker/mysql/init/01-schema.sql` for complete schema.

## Future Enhancements

- Two-factor authentication (2FA) implementation
- Email verification with token storage
- Password reset functionality
- Rate limiting for login attempts
- Refresh token support
- Additional OAuth providers (GitHub, Microsoft)
