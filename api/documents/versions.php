<?php
/**
 * Document Version History API
 * Requirements: 12.1, 12.2, 12.3, 12.4
 */

require_once __DIR__ . '/../auth/AuthMiddleware.php';
require_once __DIR__ . '/../../config/database.php';

header('Content-Type: application/json');

// Authenticate user
$auth = new AuthMiddleware();
$user = $auth->authenticate();

if (!$user) {
    http_response_code(401);
    echo json_encode(['error' => 'Unauthorized']);
    exit;
}

$method = $_SERVER['REQUEST_METHOD'];
$path = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
$pathParts = explode('/', trim($path, '/'));

// Extract document ID from path
$documentId = $pathParts[2] ?? null;

if (!$documentId) {
    http_response_code(400);
    echo json_encode(['error' => 'Document ID required']);
    exit;
}

try {
    $db = Database::getInstance()->getConnection();
    
    // Check if this is a diff request
    if (isset($pathParts[4]) && $pathParts[4] === 'diff') {
        getDiff($db, $documentId, $user);
        exit;
    }
    
    // Check if this is a restore request
    if (isset($pathParts[4]) && isset($pathParts[5]) && $pathParts[5] === 'restore') {
        restoreVersion($db, $documentId, $pathParts[4], $user);
        exit;
    }
    
    // Check if this is a label request
    if (isset($pathParts[4]) && isset($pathParts[5]) && $pathParts[5] === 'label') {
        labelVersion($db, $pathParts[4], $user);
        exit;
    }
    
    switch ($method) {
        case 'GET':
            // Get version history
            getVersionHistory($db, $documentId, $user);
            break;
            
        case 'POST':
            // Create new version (auto-save)
            createVersion($db, $documentId, $user);
            break;
            
        default:
            http_response_code(405);
            echo json_encode(['error' => 'Method not allowed']);
    }
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(['error' => 'Server error: ' . $e->getMessage()]);
}

/**
 * Get version history for a document
 */
function getVersionHistory($db, $documentId, $user) {
    // Verify user has access to document
    $stmt = $db->prepare("
        SELECT d.id 
        FROM latex_documents d
        JOIN projects p ON d.project_id = p.id
        LEFT JOIN project_collaborators pc ON p.id = pc.project_id
        WHERE d.id = ? AND (p.user_id = ? OR pc.user_id = ?)
    ");
    $stmt->execute([$documentId, $user['id'], $user['id']]);
    
    if (!$stmt->fetch()) {
        http_response_code(403);
        echo json_encode(['error' => 'Access denied']);
        return;
    }
    
    // Get versions (last 90 days, Requirement 12.8)
    $stmt = $db->prepare("
        SELECT 
            v.id,
            v.version_number,
            v.change_summary,
            v.label,
            v.is_auto_save,
            v.created_at,
            u.name as user_name
        FROM document_version_history v
        JOIN users u ON v.user_id = u.id
        WHERE v.latex_document_id = ?
            AND v.created_at >= DATE_SUB(NOW(), INTERVAL 90 DAY)
        ORDER BY v.version_number DESC
        LIMIT 100
    ");
    $stmt->execute([$documentId]);
    $versions = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    echo json_encode([
        'success' => true,
        'versions' => $versions
    ]);
}

/**
 * Create new version (auto-save every 5 minutes, Requirement 12.1)
 */
function createVersion($db, $documentId, $user) {
    $input = json_decode(file_get_contents('php://input'), true);
    
    $content = $input['content'] ?? null;
    $changeSummary = $input['change_summary'] ?? null;
    $isAutoSave = $input['is_auto_save'] ?? true;
    
    if (!$content) {
        http_response_code(400);
        echo json_encode(['error' => 'Content required']);
        return;
    }
    
    // Verify user has access
    $stmt = $db->prepare("
        SELECT d.id, d.version
        FROM latex_documents d
        JOIN projects p ON d.project_id = p.id
        LEFT JOIN project_collaborators pc ON p.id = pc.project_id
        WHERE d.id = ? AND (p.user_id = ? OR pc.user_id = ? OR pc.role IN ('editor', 'admin'))
    ");
    $stmt->execute([$documentId, $user['id'], $user['id']]);
    $document = $stmt->fetch(PDO::FETCH_ASSOC);
    
    if (!$document) {
        http_response_code(403);
        echo json_encode(['error' => 'Access denied']);
        return;
    }
    
    // Get next version number
    $stmt = $db->prepare("
        SELECT COALESCE(MAX(version_number), 0) + 1 as next_version
        FROM document_version_history
        WHERE latex_document_id = ?
    ");
    $stmt->execute([$documentId]);
    $nextVersion = $stmt->fetch(PDO::FETCH_ASSOC)['next_version'];
    
    // Insert version
    $stmt = $db->prepare("
        INSERT INTO document_version_history 
        (latex_document_id, user_id, version_number, content_snapshot, change_summary, is_auto_save, created_at)
        VALUES (?, ?, ?, ?, ?, ?, NOW())
    ");
    $stmt->execute([
        $documentId,
        $user['id'],
        $nextVersion,
        $content,
        $changeSummary,
        $isAutoSave ? 1 : 0
    ]);
    
    $versionId = $db->lastInsertId();
    
    // Update document version
    $stmt = $db->prepare("UPDATE latex_documents SET version = ? WHERE id = ?");
    $stmt->execute([$nextVersion, $documentId]);
    
    echo json_encode([
        'success' => true,
        'version' => [
            'id' => $versionId,
            'version_number' => $nextVersion,
            'created_at' => date('Y-m-d H:i:s')
        ]
    ]);
}

/**
 * Restore a previous version (Requirement 12.4)
 */
function restoreVersion($db, $documentId, $versionId, $user) {
    // Get version content
    $stmt = $db->prepare("
        SELECT content_snapshot, version_number
        FROM document_version_history
        WHERE id = ? AND latex_document_id = ?
    ");
    $stmt->execute([$versionId, $documentId]);
    $version = $stmt->fetch(PDO::FETCH_ASSOC);
    
    if (!$version) {
        http_response_code(404);
        echo json_encode(['error' => 'Version not found']);
        return;
    }
    
    // Create new version with restored content (Requirement 12.7)
    $input = [
        'content' => $version['content_snapshot'],
        'change_summary' => 'Restored from version ' . $version['version_number'],
        'is_auto_save' => false
    ];
    
    // Temporarily set input for createVersion
    $_SERVER['REQUEST_METHOD'] = 'POST';
    file_put_contents('php://input', json_encode($input));
    
    createVersion($db, $documentId, $user);
}

/**
 * Add label to version (Requirement 12.5)
 */
function labelVersion($db, $versionId, $user) {
    $input = json_decode(file_get_contents('php://input'), true);
    $label = $input['label'] ?? null;
    
    if (!$label) {
        http_response_code(400);
        echo json_encode(['error' => 'Label required']);
        return;
    }
    
    // Update version label
    $stmt = $db->prepare("
        UPDATE document_version_history 
        SET label = ?
        WHERE id = ?
    ");
    $stmt->execute([$label, $versionId]);
    
    echo json_encode(['success' => true]);
}

/**
 * Get diff between two versions (Requirement 12.3)
 */
function getDiff($db, $documentId, $user) {
    $v1 = $_GET['v1'] ?? null;
    $v2 = $_GET['v2'] ?? null;
    
    if (!$v1 || !$v2) {
        http_response_code(400);
        echo json_encode(['error' => 'Two version IDs required']);
        return;
    }
    
    // Get both versions
    $stmt = $db->prepare("
        SELECT id, version_number, content_snapshot, created_at
        FROM document_version_history
        WHERE id IN (?, ?) AND latex_document_id = ?
    ");
    $stmt->execute([$v1, $v2, $documentId]);
    $versions = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    if (count($versions) !== 2) {
        http_response_code(404);
        echo json_encode(['error' => 'Versions not found']);
        return;
    }
    
    // Calculate diff
    $version1 = $versions[0];
    $version2 = $versions[1];
    
    $lines1 = explode("\n", $version1['content_snapshot']);
    $lines2 = explode("\n", $version2['content_snapshot']);
    
    $changes = calculateDiff($lines1, $lines2);
    
    echo json_encode([
        'success' => true,
        'diff' => [
            'version1' => [
                'id' => $version1['id'],
                'version_number' => $version1['version_number'],
                'created_at' => $version1['created_at']
            ],
            'version2' => [
                'id' => $version2['id'],
                'version_number' => $version2['version_number'],
                'created_at' => $version2['created_at']
            ],
            'changes' => $changes
        ]
    ]);
}

/**
 * Calculate diff between two arrays of lines
 * Simple line-by-line diff algorithm
 */
function calculateDiff($lines1, $lines2) {
    $changes = [];
    $maxLines = max(count($lines1), count($lines2));
    
    for ($i = 0; $i < $maxLines; $i++) {
        $line1 = $lines1[$i] ?? null;
        $line2 = $lines2[$i] ?? null;
        
        if ($line1 === $line2) {
            $changes[] = [
                'type' => 'unchanged',
                'lineNumber1' => $i + 1,
                'lineNumber2' => $i + 1,
                'content1' => $line1,
                'content2' => $line2
            ];
        } elseif ($line1 === null) {
            $changes[] = [
                'type' => 'addition',
                'lineNumber1' => null,
                'lineNumber2' => $i + 1,
                'content1' => '',
                'content2' => $line2
            ];
        } elseif ($line2 === null) {
            $changes[] = [
                'type' => 'deletion',
                'lineNumber1' => $i + 1,
                'lineNumber2' => null,
                'content1' => $line1,
                'content2' => ''
            ];
        } else {
            // Line modified
            $changes[] = [
                'type' => 'deletion',
                'lineNumber1' => $i + 1,
                'lineNumber2' => null,
                'content1' => $line1,
                'content2' => ''
            ];
            $changes[] = [
                'type' => 'addition',
                'lineNumber1' => null,
                'lineNumber2' => $i + 1,
                'content1' => '',
                'content2' => $line2
            ];
        }
    }
    
    return $changes;
}
