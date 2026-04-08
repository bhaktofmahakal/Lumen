<?php
session_start();
require_once '../includes/config.php';
requireLogin();

header('Content-Type: application/json');

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    echo json_encode(['success' => false, 'error' => 'Invalid request method']);
    exit;
}

$input = json_decode(file_get_contents('php://input'), true);
$messageId = $input['message_id'] ?? '';

if (empty($messageId)) {
    echo json_encode(['success' => false, 'error' => 'Message ID required']);
    exit;
}

try {
    $conn = getDBConnection();
    if (!$conn) {
        throw new Exception('Database connection failed');
    }
    
    // Get message info before deleting
    $stmt = $conn->prepare("SELECT session_id, role FROM chat_messages WHERE id = ?");
    $stmt->bind_param("i", $messageId);
    $stmt->execute();
    $result = $stmt->get_result();
    
    if ($result->num_rows === 0) {
        throw new Exception('Message not found');
    }
    
    $messageInfo = $result->fetch_assoc();
    
    // Delete message
    $stmt = $conn->prepare("DELETE FROM chat_messages WHERE id = ?");
    $stmt->bind_param("i", $messageId);
    $stmt->execute();
    
    if ($stmt->affected_rows === 0) {
        throw new Exception('Failed to delete message');
    }
    
    // Update session message count
    $stmt = $conn->prepare("UPDATE chat_sessions SET 
                  total_messages = (SELECT COUNT(*) FROM chat_messages WHERE session_id = ?),
                  updated_at = NOW() 
                  WHERE session_id = ?");
    $stmt->bind_param("ss", $messageInfo['session_id'], $messageInfo['session_id']);
    $stmt->execute();
    
    // Log deletion
    $admin = getAdminInfo();
    error_log("Admin {$admin['username']} deleted message ID: {$messageId} from session: {$messageInfo['session_id']}");
    
    echo json_encode(['success' => true]);
    
} catch (Exception $e) {
    echo json_encode(['success' => false, 'error' => $e->getMessage()]);
}
?>