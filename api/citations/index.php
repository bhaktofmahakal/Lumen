<?php
/**
 * Citation Management API
 * Requirements: 13.1, 13.2, 13.3, 13.5, 13.9
 */

require_once __DIR__ . '/../auth/AuthMiddleware.php';

header('Content-Type: application/json');

// Enable CORS
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

// Authenticate user
$auth = new AuthMiddleware();
$user = $auth->authenticate();

if (!$user) {
    http_response_code(401);
    echo json_encode(['error' => 'Unauthorized']);
    exit();
}

// Database connection
$db = new mysqli(
    getenv('DB_HOST') ?: 'mysql',
    getenv('DB_USER') ?: 'root',
    getenv('DB_PASSWORD') ?: 'rootpassword',
    getenv('DB_NAME') ?: 'ai_research'
);

if ($db->connect_error) {
    http_response_code(500);
    echo json_encode(['error' => 'Database connection failed']);
    exit();
}

$method = $_SERVER['REQUEST_METHOD'];
$path = $_SERVER['PATH_INFO'] ?? '/';

// Route requests
switch ($method) {
    case 'GET':
        if (preg_match('/^\/project\/([^\/]+)$/', $path, $matches)) {
            getProjectCitations($db, $matches[1], $user);
        } elseif (preg_match('/^\/export\/([^\/]+)$/', $path, $matches)) {
            exportCitations($db, $matches[1], $user);
        } elseif (preg_match('/^\/(\d+)$/', $path, $matches)) {
            getCitation($db, $matches[1], $user);
        } else {
            http_response_code(404);
            echo json_encode(['error' => 'Not found']);
        }
        break;
    
    case 'POST':
        if ($path === '/create') {
            createCitation($db, $user);
        } elseif ($path === '/import-from-document') {
            importFromDocument($db, $user);
        } elseif ($path === '/update-format') {
            updateCitationFormat($db, $user);
        } else {
            http_response_code(404);
            echo json_encode(['error' => 'Not found']);
        }
        break;
    
    case 'PUT':
        if (preg_match('/^\/(\d+)$/', $path, $matches)) {
            updateCitation($db, $matches[1], $user);
        } else {
            http_response_code(404);
            echo json_encode(['error' => 'Not found']);
        }
        break;
    
    case 'DELETE':
        if (preg_match('/^\/(\d+)$/', $path, $matches)) {
            deleteCitation($db, $matches[1], $user);
        } else {
            http_response_code(404);
            echo json_encode(['error' => 'Not found']);
        }
        break;
    
    default:
        http_response_code(405);
        echo json_encode(['error' => 'Method not allowed']);
}

$db->close();


/**
 * Get all citations for a project
 * Requirements: 13.3
 */
function getProjectCitations($db, $projectId, $user) {
    // Verify user has access to project
    $stmt = $db->prepare("
        SELECT p.* FROM projects p
        LEFT JOIN project_collaborators pc ON p.id = pc.project_id
        WHERE p.id = ? AND (p.user_id = ? OR pc.user_id = ?)
    ");
    $stmt->bind_param('iii', $projectId, $user['id'], $user['id']);
    $stmt->execute();
    $result = $stmt->get_result();
    
    if ($result->num_rows === 0) {
        http_response_code(403);
        echo json_encode(['error' => 'Access denied']);
        return;
    }
    
    // Get citations
    $stmt = $db->prepare("
        SELECT * FROM citations
        WHERE project_id = ?
        ORDER BY created_at DESC
    ");
    $stmt->bind_param('i', $projectId);
    $stmt->execute();
    $result = $stmt->get_result();
    
    $citations = [];
    while ($row = $result->fetch_assoc()) {
        // Parse authors JSON
        if ($row['authors']) {
            $row['authors'] = json_decode($row['authors'], true);
        }
        $citations[] = $row;
    }
    
    echo json_encode([
        'status' => 'success',
        'citations' => $citations,
        'count' => count($citations)
    ]);
}

/**
 * Get single citation
 * Requirements: 13.3
 */
function getCitation($db, $citationId, $user) {
    $stmt = $db->prepare("
        SELECT c.*, p.user_id as project_owner
        FROM citations c
        JOIN projects p ON c.project_id = p.id
        WHERE c.id = ?
    ");
    $stmt->bind_param('i', $citationId);
    $stmt->execute();
    $result = $stmt->get_result();
    
    if ($result->num_rows === 0) {
        http_response_code(404);
        echo json_encode(['error' => 'Citation not found']);
        return;
    }
    
    $citation = $result->fetch_assoc();
    
    // Verify access
    if ($citation['project_owner'] != $user['id']) {
        // Check if user is collaborator
        $stmt = $db->prepare("
            SELECT * FROM project_collaborators
            WHERE project_id = ? AND user_id = ?
        ");
        $stmt->bind_param('ii', $citation['project_id'], $user['id']);
        $stmt->execute();
        $collab = $stmt->get_result();
        
        if ($collab->num_rows === 0) {
            http_response_code(403);
            echo json_encode(['error' => 'Access denied']);
            return;
        }
    }
    
    // Parse authors JSON
    if ($citation['authors']) {
        $citation['authors'] = json_decode($citation['authors'], true);
    }
    
    echo json_encode([
        'status' => 'success',
        'citation' => $citation
    ]);
}


/**
 * Create citation manually
 * Requirements: 13.3
 */
function createCitation($db, $user) {
    $input = json_decode(file_get_contents('php://input'), true);
    
    if (!$input || !isset($input['project_id'])) {
        http_response_code(400);
        echo json_encode(['error' => 'Invalid input']);
        return;
    }
    
    $projectId = $input['project_id'];
    
    // Verify user has access to project
    $stmt = $db->prepare("
        SELECT * FROM projects
        WHERE id = ? AND user_id = ?
    ");
    $stmt->bind_param('ii', $projectId, $user['id']);
    $stmt->execute();
    $result = $stmt->get_result();
    
    if ($result->num_rows === 0) {
        http_response_code(403);
        echo json_encode(['error' => 'Access denied']);
        return;
    }
    
    // Generate citation key if not provided
    $citationKey = $input['citation_key'] ?? generateCitationKey($input);
    
    // Check for duplicates
    $stmt = $db->prepare("
        SELECT * FROM citations
        WHERE project_id = ? AND citation_key = ?
    ");
    $stmt->bind_param('is', $projectId, $citationKey);
    $stmt->execute();
    $duplicate = $stmt->get_result();
    
    if ($duplicate->num_rows > 0) {
        http_response_code(409);
        echo json_encode([
            'status' => 'duplicate',
            'message' => "Citation $citationKey already exists"
        ]);
        return;
    }
    
    // Prepare data
    $title = $input['title'] ?? null;
    $authors = isset($input['authors']) ? json_encode($input['authors']) : null;
    $publicationYear = $input['publication_year'] ?? null;
    $journal = $input['journal'] ?? null;
    $volume = $input['volume'] ?? null;
    $issue = $input['issue'] ?? null;
    $pages = $input['pages'] ?? null;
    $doi = $input['doi'] ?? null;
    $arxivId = $input['arxiv_id'] ?? null;
    $url = $input['url'] ?? null;
    $citationFormat = $input['citation_format'] ?? 'APA';
    
    // Generate BibTeX (simplified)
    $bibtex = generateBibTeX($citationKey, $input);
    
    // Insert citation
    $stmt = $db->prepare("
        INSERT INTO citations (
            project_id, citation_key, title, authors, publication_year,
            journal, volume, issue, pages, doi, arxiv_id, url,
            bibtex, citation_format
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ");
    $stmt->bind_param(
        'isssisssssssss',
        $projectId, $citationKey, $title, $authors, $publicationYear,
        $journal, $volume, $issue, $pages, $doi, $arxivId, $url,
        $bibtex, $citationFormat
    );
    
    if ($stmt->execute()) {
        $citationId = $stmt->insert_id;
        
        echo json_encode([
            'status' => 'success',
            'citation_id' => $citationId,
            'citation_key' => $citationKey,
            'message' => 'Citation created successfully'
        ]);
    } else {
        http_response_code(500);
        echo json_encode(['error' => 'Failed to create citation']);
    }
}

/**
 * Generate citation key from metadata
 */
function generateCitationKey($data) {
    $key = '';
    
    // Get first author's last name
    if (isset($data['authors']) && count($data['authors']) > 0) {
        $firstAuthor = $data['authors'][0];
        $parts = explode(' ', $firstAuthor);
        $lastName = end($parts);
        $key .= preg_replace('/[^a-zA-Z]/', '', $lastName);
    } else {
        $key .= 'Unknown';
    }
    
    // Add year
    if (isset($data['publication_year'])) {
        $key .= $data['publication_year'];
    } else {
        $key .= date('Y');
    }
    
    return $key;
}

/**
 * Generate BibTeX entry (simplified)
 */
function generateBibTeX($citationKey, $data) {
    $bibtex = "@article{" . $citationKey . ",\n";
    
    if (isset($data['title'])) {
        $bibtex .= "  title = {" . $data['title'] . "},\n";
    }
    
    if (isset($data['authors']) && count($data['authors']) > 0) {
        $bibtex .= "  author = {" . implode(' and ', $data['authors']) . "},\n";
    }
    
    if (isset($data['publication_year'])) {
        $bibtex .= "  year = {" . $data['publication_year'] . "},\n";
    }
    
    if (isset($data['journal'])) {
        $bibtex .= "  journal = {" . $data['journal'] . "},\n";
    }
    
    if (isset($data['volume'])) {
        $bibtex .= "  volume = {" . $data['volume'] . "},\n";
    }
    
    if (isset($data['doi'])) {
        $bibtex .= "  doi = {" . $data['doi'] . "},\n";
    }
    
    $bibtex .= "}\n";
    
    return $bibtex;
}


/**
 * Update citation
 * Requirements: 13.3
 */
function updateCitation($db, $citationId, $user) {
    $input = json_decode(file_get_contents('php://input'), true);
    
    if (!$input) {
        http_response_code(400);
        echo json_encode(['error' => 'Invalid input']);
        return;
    }
    
    // Verify user has access
    $stmt = $db->prepare("
        SELECT c.*, p.user_id as project_owner
        FROM citations c
        JOIN projects p ON c.project_id = p.id
        WHERE c.id = ?
    ");
    $stmt->bind_param('i', $citationId);
    $stmt->execute();
    $result = $stmt->get_result();
    
    if ($result->num_rows === 0) {
        http_response_code(404);
        echo json_encode(['error' => 'Citation not found']);
        return;
    }
    
    $citation = $result->fetch_assoc();
    
    if ($citation['project_owner'] != $user['id']) {
        http_response_code(403);
        echo json_encode(['error' => 'Access denied']);
        return;
    }
    
    // Build update query
    $updates = [];
    $types = '';
    $values = [];
    
    $allowedFields = ['title', 'publication_year', 'journal', 'volume', 'issue', 'pages', 'doi', 'arxiv_id', 'url', 'citation_format'];
    
    foreach ($allowedFields as $field) {
        if (isset($input[$field])) {
            $updates[] = "$field = ?";
            $types .= 's';
            $values[] = $input[$field];
        }
    }
    
    if (isset($input['authors'])) {
        $updates[] = "authors = ?";
        $types .= 's';
        $values[] = json_encode($input['authors']);
    }
    
    if (empty($updates)) {
        http_response_code(400);
        echo json_encode(['error' => 'No valid fields to update']);
        return;
    }
    
    $types .= 'i';
    $values[] = $citationId;
    
    $sql = "UPDATE citations SET " . implode(', ', $updates) . " WHERE id = ?";
    $stmt = $db->prepare($sql);
    $stmt->bind_param($types, ...$values);
    
    if ($stmt->execute()) {
        echo json_encode([
            'status' => 'success',
            'message' => 'Citation updated successfully'
        ]);
    } else {
        http_response_code(500);
        echo json_encode(['error' => 'Failed to update citation']);
    }
}

/**
 * Delete citation
 * Requirements: 13.3
 */
function deleteCitation($db, $citationId, $user) {
    // Verify user has access
    $stmt = $db->prepare("
        SELECT c.*, p.user_id as project_owner
        FROM citations c
        JOIN projects p ON c.project_id = p.id
        WHERE c.id = ?
    ");
    $stmt->bind_param('i', $citationId);
    $stmt->execute();
    $result = $stmt->get_result();
    
    if ($result->num_rows === 0) {
        http_response_code(404);
        echo json_encode(['error' => 'Citation not found']);
        return;
    }
    
    $citation = $result->fetch_assoc();
    
    if ($citation['project_owner'] != $user['id']) {
        http_response_code(403);
        echo json_encode(['error' => 'Access denied']);
        return;
    }
    
    // Delete citation
    $stmt = $db->prepare("DELETE FROM citations WHERE id = ?");
    $stmt->bind_param('i', $citationId);
    
    if ($stmt->execute()) {
        echo json_encode([
            'status' => 'success',
            'message' => 'Citation deleted successfully'
        ]);
    } else {
        http_response_code(500);
        echo json_encode(['error' => 'Failed to delete citation']);
    }
}


/**
 * Import citation from document
 * Requirements: 13.1, 13.2
 */
function importFromDocument($db, $user) {
    $input = json_decode(file_get_contents('php://input'), true);
    
    if (!$input || !isset($input['document_id'])) {
        http_response_code(400);
        echo json_encode(['error' => 'Document ID required']);
        return;
    }
    
    $documentId = $input['document_id'];
    
    // Get document
    $stmt = $db->prepare("
        SELECT d.*, p.user_id as project_owner
        FROM documents d
        JOIN projects p ON d.project_id = p.id
        WHERE d.document_id = ?
    ");
    $stmt->bind_param('s', $documentId);
    $stmt->execute();
    $result = $stmt->get_result();
    
    if ($result->num_rows === 0) {
        http_response_code(404);
        echo json_encode(['error' => 'Document not found']);
        return;
    }
    
    $document = $result->fetch_assoc();
    
    // Verify access
    if ($document['project_owner'] != $user['id']) {
        http_response_code(403);
        echo json_encode(['error' => 'Access denied']);
        return;
    }
    
    // Call Python service to import citation
    $pythonServiceUrl = getenv('PYTHON_SERVICE_URL') ?: 'http://ai-services:8000';
    $url = "$pythonServiceUrl/api/citations/import-from-pdf";
    
    $postData = [
        'project_id' => $document['project_id'],
        'document_id' => $documentId,
        'pdf_path' => $document['file_path']
    ];
    
    $ch = curl_init($url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, http_build_query($postData));
    curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/x-www-form-urlencoded']);
    
    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    
    if ($httpCode === 200) {
        echo $response;
    } else {
        http_response_code($httpCode);
        echo $response ?: json_encode(['error' => 'Failed to import citation']);
    }
}

/**
 * Update citation format for all citations in project
 * Requirements: 13.7
 */
function updateCitationFormat($db, $user) {
    $input = json_decode(file_get_contents('php://input'), true);
    
    if (!$input || !isset($input['project_id']) || !isset($input['format'])) {
        http_response_code(400);
        echo json_encode(['error' => 'Project ID and format required']);
        return;
    }
    
    $projectId = $input['project_id'];
    $format = $input['format'];
    
    // Validate format
    $validFormats = ['APA', 'MLA', 'Chicago', 'IEEE'];
    if (!in_array($format, $validFormats)) {
        http_response_code(400);
        echo json_encode(['error' => 'Invalid format. Must be APA, MLA, Chicago, or IEEE']);
        return;
    }
    
    // Verify user has access to project
    $stmt = $db->prepare("
        SELECT * FROM projects
        WHERE id = ? AND user_id = ?
    ");
    $stmt->bind_param('ii', $projectId, $user['id']);
    $stmt->execute();
    $result = $stmt->get_result();
    
    if ($result->num_rows === 0) {
        http_response_code(403);
        echo json_encode(['error' => 'Access denied']);
        return;
    }
    
    // Update all citations
    $stmt = $db->prepare("
        UPDATE citations
        SET citation_format = ?
        WHERE project_id = ?
    ");
    $stmt->bind_param('si', $format, $projectId);
    
    if ($stmt->execute()) {
        echo json_encode([
            'status' => 'success',
            'message' => "Citation format updated to $format",
            'updated_count' => $stmt->affected_rows
        ]);
    } else {
        http_response_code(500);
        echo json_encode(['error' => 'Failed to update citation format']);
    }
}

/**
 * Export citations in specified format
 * Requirements: 13.9
 */
function exportCitations($db, $projectId, $user) {
    $format = $_GET['format'] ?? 'bibtex';
    
    // Validate format
    $validFormats = ['bibtex', 'ris', 'endnote'];
    if (!in_array($format, $validFormats)) {
        http_response_code(400);
        echo json_encode(['error' => 'Invalid format. Must be bibtex, ris, or endnote']);
        return;
    }
    
    // Verify user has access to project
    $stmt = $db->prepare("
        SELECT p.* FROM projects p
        LEFT JOIN project_collaborators pc ON p.id = pc.project_id
        WHERE p.id = ? AND (p.user_id = ? OR pc.user_id = ?)
    ");
    $stmt->bind_param('iii', $projectId, $user['id'], $user['id']);
    $stmt->execute();
    $result = $stmt->get_result();
    
    if ($result->num_rows === 0) {
        http_response_code(403);
        echo json_encode(['error' => 'Access denied']);
        return;
    }
    
    // Call Python service to export citations
    $pythonServiceUrl = getenv('PYTHON_SERVICE_URL') ?: 'http://ai-services:8000';
    $url = "$pythonServiceUrl/api/citations/export/$projectId?format=$format";
    
    $ch = curl_init($url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    
    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    
    if ($httpCode === 200) {
        echo $response;
    } else {
        http_response_code($httpCode);
        echo $response ?: json_encode(['error' => 'Failed to export citations']);
    }
}

?>
