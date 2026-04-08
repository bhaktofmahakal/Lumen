<?php
session_start();
require_once 'includes/config.php';

// Redirect if already logged in
if (isAdminLoggedIn()) {
    header('Location: index.php');
    exit;
}

$error_message = "";
$info_message = "";

// Check for timeout message
if (isset($_GET['timeout'])) {
    $info_message = "Your session has expired. Please log in again.";
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $username = trim($_POST['username'] ?? '');
    $password = $_POST['password'] ?? '';
    $csrf_token = $_POST['csrf_token'] ?? '';
    $clientIP = $_SERVER['REMOTE_ADDR'] ?? 'Unknown';
    
    // CSRF Protection
    if (!verifyCSRFToken($csrf_token)) {
        $error_message = "Invalid security token. Please try again.";
    }
    // Rate limiting
    elseif (!checkLoginAttempts($clientIP)) {
        $error_message = "Too many login attempts. Please wait 15 minutes.";
        logLoginAttempt($clientIP, 0);
    }
    elseif (empty($username) || empty($password)) {
        $error_message = "Please fill in all fields.";
        logLoginAttempt($clientIP, 0);
    } else {
        $conn = getDBConnection();
        if (!$conn) {
            // Fallback authentication if database fails
            if ($username === 'admin' && $password === 'admin123') {
                // Regenerate session ID to prevent session fixation attacks
                session_regenerate_id(true);
                
                $_SESSION['admin_logged_in'] = true;
                $_SESSION['admin_username'] = 'admin';
                $_SESSION['admin_id'] = 1;
                $_SESSION['admin_email'] = 'admin@chatapp.com';
                $_SESSION['admin_ip'] = $clientIP;
                
                error_log("Admin login (fallback): {$username} from {$clientIP}");
                header('Location: index.php');
                exit;
            } else {
                $error_message = "Database connection failed and invalid credentials.";
                logLoginAttempt($clientIP, 0);
            }
        } else {
            $stmt = $conn->prepare("SELECT * FROM admins WHERE username = ?");
            $stmt->bind_param("s", $username);
            $stmt->execute();
            $result = $stmt->get_result();

            if ($result->num_rows && $admin = $result->fetch_assoc()) {
                // Check password (supports both old hash and new bcrypt)
                if (password_verify($password, $admin['password']) || 
                    hash('sha256', $password) === $admin['password'] || 
                    $password === $admin['password']) {
                    
                    // Regenerate session ID to prevent session fixation attacks
                    session_regenerate_id(true);
                    
                    $_SESSION['admin_logged_in'] = true;
                    $_SESSION['admin_username'] = $admin['username'];
                    $_SESSION['admin_id'] = $admin['id'];
                    $_SESSION['admin_email'] = $admin['email'];
                    $_SESSION['admin_ip'] = $clientIP;
                    
                    // Update last login (if column exists)
                    try {
                        $stmt = $conn->prepare("UPDATE admins SET last_login = NOW() WHERE id = ?");
                        $stmt->bind_param("i", $admin['id']);
                        $stmt->execute();
                    } catch (Exception $e) {
                        // Column doesn't exist, skip update
                        error_log("Admin table update failed: " . $e->getMessage());
                    }
                    
                    logLoginAttempt($clientIP, 1);
                    error_log("Admin login: {$username} from {$clientIP}");
                    
                    header('Location: index.php');
                    exit;
                } else {
                    $error_message = "Invalid username or password.";
                    logLoginAttempt($clientIP, 0);
                }
            } else {
                $error_message = "Invalid username or password.";
                logLoginAttempt($clientIP, 0);
            }
        }
    }
}
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Login - <?php echo ADMIN_TITLE; ?></title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body class="bg-gradient-to-br from-blue-500 to-purple-600 min-h-screen flex items-center justify-center">
    <div class="bg-white p-8 rounded-xl shadow-2xl w-full max-w-md">
        <div class="text-center mb-8">
            <div class="mx-auto w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-4">
                <i class="fas fa-shield-alt text-2xl text-blue-600"></i>
            </div>
            <h1 class="text-2xl font-bold text-gray-800">Admin Panel</h1>
            <p class="text-gray-600">Sign in to your account</p>
        </div>

        <?php if ($error_message): ?>
            <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
                <div class="flex">
                    <i class="fas fa-exclamation-circle mr-2 mt-0.5"></i>
                    <span><?php echo htmlspecialchars($error_message); ?></span>
                </div>
            </div>
        <?php endif; ?>
        
        <?php if ($info_message): ?>
            <div class="bg-blue-100 border border-blue-400 text-blue-700 px-4 py-3 rounded mb-4">
                <div class="flex">
                    <i class="fas fa-info-circle mr-2 mt-0.5"></i>
                    <span><?php echo htmlspecialchars($info_message); ?></span>
                </div>
            </div>
        <?php endif; ?>

        <form method="POST" action="" class="space-y-6">
            <input type="hidden" name="csrf_token" value="<?php echo generateCSRFToken(); ?>">
            <div>
                <label for="username" class="block text-sm font-medium text-gray-700 mb-2">
                    <i class="fas fa-user mr-2"></i>Username
                </label>
                <input type="text" 
                       id="username" 
                       name="username" 
                       value="<?php echo htmlspecialchars($_POST['username'] ?? ''); ?>"
                       class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
                       placeholder="Enter your username"
                       required>
            </div>

            <div>
                <label for="password" class="block text-sm font-medium text-gray-700 mb-2">
                    <i class="fas fa-lock mr-2"></i>Password
                </label>
                <div class="relative">
                    <input type="password" 
                           id="password" 
                           name="password" 
                           class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition pr-12"
                           placeholder="Enter your password"
                           required>
                    <button type="button" 
                            onclick="togglePassword()"
                            class="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700">
                        <i class="fas fa-eye" id="password-toggle"></i>
                    </button>
                </div>
            </div>

            <button type="submit" 
                    class="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition font-medium">
                <i class="fas fa-sign-in-alt mr-2"></i>
                Sign In
            </button>
        </form>



        <div class="mt-8 text-center">
            <a href="../index.php" class="text-blue-600 hover:text-blue-800 text-sm">
                <i class="fas fa-arrow-left mr-1"></i>
                Back to Chat App
            </a>
        </div>
    </div>

    <script>
        function togglePassword() {
            const passwordInput = document.getElementById('password');
            const toggleIcon = document.getElementById('password-toggle');
            
            if (passwordInput.type === 'password') {
                passwordInput.type = 'text';
                toggleIcon.className = 'fas fa-eye-slash';
            } else {
                passwordInput.type = 'password';
                toggleIcon.className = 'fas fa-eye';
            }
        }

        // Auto-focus on username field
        document.getElementById('username').focus();
    </script>
</body>
</html>