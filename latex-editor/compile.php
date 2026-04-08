<?php
declare(strict_types=1);

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST');
header('Access-Control-Allow-Headers: Content-Type');

error_reporting(E_ALL);
ini_set('display_errors', '0'); // Disable HTML error display for JSON API

/**
 * Clean up PDF files older than $maxAge seconds from the given directory.
 *
 * Applies graceful degradation: if cleanup fails for any reason (permissions,
 * missing directory, etc.) the error is logged but compilation continues.
 *
 * @param string $directory  Absolute path to the output directory.
 * @param int    $maxAge     Maximum file age in seconds (default: 86400 = 24h).
 */
function cleanupOldPDFs(string $directory, int $maxAge = 86400): void
{
    if (!is_dir($directory)) {
        return;
    }

    $now = time();
    $pattern = $directory . DIRECTORY_SEPARATOR . '*.pdf';
    $files = glob($pattern);

    if ($files === false) {
        error_log("cleanupOldPDFs: glob() failed for pattern: {$pattern}");
        return;
    }

    foreach ($files as $file) {
        if (!is_file($file)) {
            continue;
        }

        $mtime = filemtime($file);
        if ($mtime === false) {
            error_log("cleanupOldPDFs: could not read mtime for: {$file}");
            continue;
        }

        if (($now - $mtime) > $maxAge) {
            if (!unlink($file)) {
                error_log("cleanupOldPDFs: failed to delete old PDF: {$file}");
            } else {
                error_log("cleanupOldPDFs: deleted old PDF: {$file}");
            }
        }
    }
}

class LaTeXCompiler {
    private $tempDir;
    private $outputDir;
    private $maxExecutionTime = 30;
    private $maxFileSize = 50 * 1024 * 1024;
    
    public function __construct() {
        $this->tempDir = sys_get_temp_dir() . DIRECTORY_SEPARATOR . 'latex_' . uniqid();
        $this->outputDir = __DIR__ . DIRECTORY_SEPARATOR . 'output';
        
        if (!file_exists($this->tempDir)) {
            mkdir($this->tempDir, 0755, true);
        }
        if (!file_exists($this->outputDir)) {
            mkdir($this->outputDir, 0755, true);
        }
        
        set_time_limit($this->maxExecutionTime + 10);
    }
    
    public function compile($latexContent) {
        try {
            // Clean up old PDFs before generating a new one (graceful degradation)
            try {
                cleanupOldPDFs($this->outputDir);
            } catch (Throwable $cleanupError) {
                error_log("PDF cleanup failed (non-fatal): " . $cleanupError->getMessage());
            }

            if (empty($latexContent)) {
                throw new Exception("LaTeX content cannot be empty");
            }
            
            if (strlen($latexContent) > $this->maxFileSize) {
                throw new Exception("LaTeX content too large (max 50MB)");
            }
            
            $this->validateLatexContent($latexContent);
            
            $filename = 'document_' . uniqid();
            $texFile = $this->tempDir . DIRECTORY_SEPARATOR . $filename . '.tex';
            $pdfFile = $this->tempDir . DIRECTORY_SEPARATOR . $filename . '.pdf';
            $outputPdfFile = $this->outputDir . DIRECTORY_SEPARATOR . $filename . '.pdf';
            
            if (file_put_contents($texFile, $latexContent) === false) {
                throw new Exception("Failed to write LaTeX file");
            }
            
            $result = $this->executeLatexCompilation($texFile, $filename);
            
            if ($result['success']) {
                if (file_exists($pdfFile)) {
                    if (copy($pdfFile, $outputPdfFile)) {
                        $this->cleanupTempFiles($this->tempDir);
                        
                        return [
                            'success' => true,
                            'pdf_url' => 'output/' . $filename . '.pdf',
                            'filename' => $filename . '.pdf',
                            'size' => filesize($outputPdfFile)
                        ];
                    } else {
                        throw new Exception("Failed to move PDF file");
                    }
                } else {
                    throw new Exception("PDF file was not generated");
                }
            } else {
                throw new Exception($result['error']);
            }
            
        } catch (Exception $e) {
            $this->cleanupTempFiles($this->tempDir);
            
            return [
                'success' => false,
                'error' => $e->getMessage()
            ];
        }
    }
    
    private function validateLatexContent($content) {
        $dangerousCommands = [
            '\\write18',
            '\\immediate\\write18',
            '\\input{|',
            '\\openin',
            '\\openout',
            '\\special{system',
            '\\special{!',
            '\\def\\write18',
            'shell-escape'
        ];
        
        $contentLower = strtolower($content);
        foreach ($dangerousCommands as $dangerous) {
            if (strpos($contentLower, strtolower($dangerous)) !== false) {
                throw new Exception("Potentially dangerous LaTeX command detected: " . $dangerous);
            }
        }
    }
    
    private function executeLatexCompilation($texFile, $filename) {
        $workingDir = dirname($texFile);
        $baseFilename = pathinfo($texFile, PATHINFO_FILENAME);
        
        $texlivePath = 'C:\texlive\2025\bin\windows';
        
        $engines = [
            'pdflatex' => [
                'command' => $texlivePath . '\pdflatex.exe',
                'args' => [
                    '-interaction=nonstopmode',
                    '-file-line-error',
                    '-synctex=1',
                    '--max-print-line=10000',
                    '-output-directory=' . escapeshellarg($workingDir),
                    escapeshellarg($texFile)
                ]
            ],
            'xelatex' => [
                'command' => $texlivePath . '\xelatex.exe',
                'args' => [
                    '-interaction=nonstopmode',
                    '-file-line-error',
                    '-synctex=1',
                    '--max-print-line=10000',
                    '-output-directory=' . escapeshellarg($workingDir),
                    escapeshellarg($texFile)
                ]
            ],
            'lualatex' => [
                'command' => $texlivePath . '\lualatex.exe',
                'args' => [
                    '-interaction=nonstopmode',
                    '-file-line-error',
                    '-synctex=1',
                    '--max-print-line=10000',
                    '-output-directory=' . escapeshellarg($workingDir),
                    escapeshellarg($texFile)
                ]
            ]
        ];
        
        $lastError = '';
        
        foreach ($engines as $engineName => $engine) {
            $command = $engine['command'] . ' ' . implode(' ', $engine['args']);
            
            $output = [];
            $returnCode = 0;
            
            $oldDir = getcwd();
            chdir($workingDir);
            
            exec($command . ' 2>&1', $output, $returnCode);
            
            chdir($oldDir);
            
            $outputText = implode("\n", $output);
            
            $pdfFile = $workingDir . DIRECTORY_SEPARATOR . $baseFilename . '.pdf';
            
            // Check for PDF generation success
            if ($returnCode === 0 && file_exists($pdfFile) && filesize($pdfFile) > 0) {
                // Even if PDF is generated, check for warnings and errors
                $errorAnalysis = $this->parseLatexError($outputText, $engineName);
                
                return [
                    'success' => true,
                    'engine' => $engineName,
                    'output' => $outputText,
                    'warnings' => $errorAnalysis // Include warnings even on success
                ];
            } else {
                // Process all errors and warnings
                $lastError = $this->parseLatexError($outputText, $engineName);
                
                // Handle bibliography/cross-reference reruns
                if (strpos($outputText, 'Rerun to get cross-references right') !== false ||
                    strpos($outputText, 'There were undefined references') !== false ||
                    strpos($outputText, 'Citation') !== false) {
                    
                    // Run second pass
                    exec($command . ' 2>&1', $output2, $returnCode2);
                    $outputText2 = implode("\n", $output2);
                    
                    if ($returnCode2 === 0 && file_exists($pdfFile) && filesize($pdfFile) > 0) {
                        $errorAnalysis2 = $this->parseLatexError($outputText2, $engineName);
                        return [
                            'success' => true,
                            'engine' => $engineName,
                            'output' => $outputText2,
                            'warnings' => $errorAnalysis2
                        ];
                    } else {
                        // Combine errors from both runs
                        $combinedErrors = $lastError . "\n\n" . "After second run:\n" . $this->parseLatexError($outputText2, $engineName);
                        $lastError = $combinedErrors;
                    }
                }
            }
        }
        
        return [
            'success' => false,
            'error' => $lastError ?: 'LaTeX compilation failed with all engines'
        ];
    }
    
    private function parseLatexError($output, $engine) {
        // First try to extract specific line-based errors from the raw output
        $errors = $this->extractSpecificErrors($output);
        
        // If no specific errors found, use general parsing
        if (empty($errors)) {
            $errors = $this->generalErrorParsing($output);
        }
        
        // If still no errors found, try fallback method
        if (empty($errors)) {
            $errors = $this->fallbackErrorParsing($output);
        }
        
        $warnings = $this->extractWarnings($output);
        
        // Remove duplicates
        $errors = array_unique($errors);
        $warnings = array_unique($warnings);
        
        // Debug: Enhanced logging for better troubleshooting
        error_log("LaTeX Debug - Error lines extracted:\n" . $this->extractErrorLines($output));
        error_log("LaTeX Parsed Errors (" . count($errors) . " found): " . print_r($errors, true));
        
        // Save complete debug info
        $debugFile = sys_get_temp_dir() . '/latex_debug_' . date('Y-m-d_H-i-s') . '.txt';
        file_put_contents($debugFile, 
            "COMPLETE RAW OUTPUT:\n" . str_repeat("=", 50) . "\n" . $output . 
            "\n\n" . str_repeat("=", 50) . "\nPARSED ERRORS:\n" . print_r($errors, true) .
            "\n\nPARSED WARNINGS:\n" . print_r($warnings, true)
        );
        
        // Build comprehensive error message
        $errorMessage = "";
        
        if (!empty($errors)) {
            $errorMessage .= "COMPILATION ERRORS (" . count($errors) . " found):\n";
            $errorMessage .= "═══════════════════════════════════════\n\n";
            $errorMessage .= implode("\n\n", $errors);
        }
        
        if (!empty($warnings)) {
            if ($errorMessage) $errorMessage .= "\n\n";
            $errorMessage .= "WARNINGS (" . count($warnings) . " found):\n";
            $errorMessage .= "═══════════════════════════════════════\n\n";
            $errorMessage .= implode("\n\n", array_slice($warnings, 0, 5)); // Show max 5 warnings
            if (count($warnings) > 5) {
                $errorMessage .= "\n\n... and " . (count($warnings) - 5) . " more warnings";
            }
        }
        
        if (empty($errors) && empty($warnings)) {
            // Filter out verbose output for cleaner error display
            $lines = explode("\n", $output);
            $relevantLines = array_filter($lines, function($line) {
                $line = trim($line);
                return !empty($line) && 
                       !preg_match('/^This is |^LaTeX2e |^Document Class|^Package |^File: |^\(|^entering extended mode/', $line) &&
                       !preg_match('/^\*\*|^Output written|^Transcript written|^LaTeX Font Info/', $line);
            });
            
            $errorOutput = implode("\n", array_slice($relevantLines, -25));
            return "Compilation failed with $engine engine\n\nOutput:\n" . $errorOutput;
        }
        
        // Add smart error interpretation
        if (!empty($errors)) {
            $errorMessage = $this->addSmartErrorAnalysis($errorMessage, $errors);
        }
        
        return $errorMessage;
    }
    
    private function addSmartErrorAnalysis($errorMessage, $errors) {
        // Remove all hard-coded suggestions - let AI handle analysis
        return $errorMessage;
    }
    
    private function extractSpecificErrors($output) {
        $errors = [];
        
        // Method 1: Extract complete error messages using better regex
        if (preg_match_all('/([^:\s]+\.tex):(\d+):\s*([^\r\n]+(?:\r?\n(?!\s*[a-zA-Z])[^\r\n]*)*)/m', $output, $matches, PREG_SET_ORDER)) {
            foreach ($matches as $match) {
                $lineNum = $match[2];
                $errorMsg = trim(preg_replace('/\s+/', ' ', $match[3]));
                
                if (strlen($errorMsg) > 5) {
                    $errors[] = "Line " . $lineNum . ": " . $errorMsg;
                }
            }
        }
        
        // Method 1b: Try simpler approach for file:line format
        $lines = explode("\n", $output);
        for ($i = 0; $i < count($lines); $i++) {
            if (preg_match('/([^:\s]+\.tex):(\d+):\s*(.+)/', $lines[$i], $match)) {
                $lineNum = $match[2];
                $errorMsg = trim($match[3]);
                
                // Collect additional lines if they seem to be part of the error
                for ($j = $i + 1; $j < min($i + 3, count($lines)); $j++) {
                    $nextLine = trim($lines[$j]);
                    if (!empty($nextLine) && 
                        !preg_match('/^\s*$|^[a-zA-Z]+\.tex:\d+:|^l\.\d+|^Output written/', $nextLine)) {
                        $errorMsg .= ' ' . $nextLine;
                    } else {
                        break;
                    }
                }
                
                if (strlen($errorMsg) > 5) {
                    $errors[] = "Line " . $lineNum . ": " . $errorMsg;
                }
            }
        }
        
        // Method 2: Parse ! error blocks with line numbers (capture full error)
        if (preg_match_all('/!\s*(.+?)(?=\nl\.\d+|\n\n|\z)/s', $output, $errorMatches, PREG_SET_ORDER)) {
            if (preg_match_all('/l\.(\d+)/', $output, $lineMatches)) {
                $lineNumbers = $lineMatches[1];
                foreach ($errorMatches as $index => $match) {
                    if (isset($lineNumbers[$index])) {
                        $errorText = trim(preg_replace('/\s+/', ' ', $match[1]));
                        $lineNumber = $lineNumbers[$index];
                        if (strlen($errorText) > 5) {
                            $errors[] = "Line " . $lineNumber . ": " . $errorText;
                        }
                    }
                }
            }
        }
        
        // Method 3: Comprehensive error extraction with full messages
        $this->extractComprehensiveErrors($output, $errors);
        
        return array_unique($errors);
    }
    
    private function extractComprehensiveErrors($output, &$errors) {
        // Split output into error sections
        $sections = preg_split('/(?=^!)/m', $output);
        
        foreach ($sections as $section) {
            $lines = explode("\n", $section);
            $errorMessage = '';
            $lineNumber = '';
            
            foreach ($lines as $i => $line) {
                $line = trim($line);
                
                // Find error message (starts with !)
                if (preg_match('/^!\s*(.+)/', $line, $matches)) {
                    $errorMessage = $matches[1];
                    
                    // Collect all relevant continuation lines
                    for ($j = $i + 1; $j < count($lines); $j++) {
                        $nextLine = trim($lines[$j]);
                        
                        if (preg_match('/^l\.(\d+)/', $nextLine)) {
                            // Found line number, stop collecting
                            break;
                        } elseif (!empty($nextLine) && 
                                 !preg_match('/^See the LaTeX manual|^Type  H|^\s*$/', $nextLine)) {
                            $errorMessage .= ' ' . $nextLine;
                        }
                    }
                }
                
                // Find line number
                if (preg_match('/^l\.(\d+)/', $line, $matches)) {
                    $lineNumber = $matches[1];
                    break;
                }
            }
            
            // Add error if we have both message and line number
            if (!empty($errorMessage) && !empty($lineNumber)) {
                $cleanError = trim(preg_replace('/\s+/', ' ', $errorMessage));
                $errors[] = "Line " . $lineNumber . ": " . $cleanError;
            }
        }
        
        return array_unique($errors);
    }
    
    private function generalErrorParsing($output) {
        $errors = [];
        
        // Parse complete error messages with line numbers
        $lines = explode("\n", $output);
        
        for ($i = 0; $i < count($lines); $i++) {
            $line = trim($lines[$i]);
            $errorMessage = '';
            $lineNumber = '';
            
            // Look for specific error patterns with full messages
            if (preg_match('/Paragraph ended before (.+) was complete/', $line, $matches)) {
                $errorMessage = "Paragraph ended before " . $matches[1] . " was complete (missing closing brace)";
            }
            elseif (preg_match('/Undefined control sequence(.*)/', $line, $matches)) {
                $errorMessage = "Undefined control sequence" . $matches[1];
                // Look ahead for the actual command name
                if (isset($lines[$i+1]) && preg_match('/\\\\([a-zA-Z]+)/', $lines[$i+1], $cmdMatch)) {
                    $errorMessage .= " '\\" . $cmdMatch[1] . "'";
                }
            }
            elseif (preg_match('/LaTeX Error:\s*(.+)/', $line, $matches)) {
                $errorMessage = "LaTeX Error: " . $matches[1];
            }
            elseif (preg_match('/Environment\s+([^:]+)\s+undefined/', $line, $matches)) {
                $errorMessage = "Environment '{$matches[1]}' is undefined";
            }
            elseif (preg_match('/(Too many [})].*?)/', $line, $matches)) {
                $errorMessage = $matches[1];
            }
            elseif (preg_match('/(Missing \$ inserted.*)/', $line, $matches)) {
                $errorMessage = $matches[1] . " (math mode error)";
            }
            elseif (preg_match('/(Runaway argument.*)/', $line, $matches)) {
                $errorMessage = $matches[1] . " - missing closing brace";
            }
            elseif (preg_match('/(Extra \\\\[a-zA-Z]+.*)/', $line, $matches)) {
                $errorMessage = $matches[1];
            }
            
            // If we found an error message, look for line number nearby
            if (!empty($errorMessage)) {
                // Look in current and next few lines for line number
                for ($j = $i; $j < min($i + 5, count($lines)); $j++) {
                    if (preg_match('/l\.(\d+)/', $lines[$j], $lineMatch)) {
                        $lineNumber = $lineMatch[1];
                        break;
                    }
                }
                
                if (!empty($lineNumber)) {
                    $errors[] = "Line " . $lineNumber . ": " . $errorMessage;
                } else {
                    $errors[] = $errorMessage;
                }
            }
        }
        
        return array_unique($errors);
    }
    
    private function extractWarnings($output) {
        $warnings = [];
        $lines = explode("\n", $output);
        
        foreach ($lines as $line) {
            if (preg_match('/^Package\s+([^:]+)\s+Warning:\s*(.+)/', $line, $matches)) {
                $warnings[] = "Warning ({$matches[1]}): " . $matches[2];
            }
            elseif (preg_match('/Warning:\s*(.+)/', $line, $matches)) {
                $warnings[] = "Warning: " . $matches[1];
            }
        }
        
        return $warnings;
    }
    
    private function fallbackErrorParsing($output) {
        $errors = [];
        
        // Find line numbers anywhere in the output
        preg_match_all('/l\.(\d+)/', $output, $lineMatches);
        $lineNumbers = array_unique($lineMatches[1]);
        
        // Find common error messages
        $errorPatterns = [
            'Missing closing brace' => ['Paragraph ended before', 'was complete'],
            'Undefined control sequence' => ['Undefined control sequence'],
            'Missing $ for math mode' => ['Missing \\$ inserted'],
            'Too many closing braces' => ['Too many }'],
            'Undefined environment' => ['undefined', 'Environment'],
            'LaTeX syntax error' => ['LaTeX Error']
        ];
        
        foreach ($errorPatterns as $errorType => $patterns) {
            foreach ($patterns as $pattern) {
                if (stripos($output, $pattern) !== false) {
                    if (!empty($lineNumbers)) {
                        $errors[] = "Line " . $lineNumbers[0] . ": " . $errorType;
                        array_shift($lineNumbers); // Remove used line number
                    } else {
                        $errors[] = $errorType;
                    }
                    break;
                }
            }
        }
        
        return array_unique($errors);
    }
    
    private function formatError($errorMsg, $lineNumber = '') {
        if ($lineNumber) {
            return "Line " . $lineNumber . ": " . $errorMsg;
        } else {
            return $errorMsg;
        }
    }
    
    private function extractErrorLines($output) {
        $lines = explode("\n", $output);
        $errorLines = [];
        
        foreach ($lines as $i => $line) {
            if (preg_match('/\.tex:\d+:|^!|^l\.\d+|LaTeX Error|Undefined|Too many|Missing/', $line)) {
                $errorLines[] = "Line " . ($i + 1) . ": " . trim($line);
            }
        }
        
        return implode("\n", array_slice($errorLines, 0, 10)); // First 10 error-related lines
    }
    
    private function cleanupTempFiles($dir) {
        if (!is_dir($dir)) return;
        
        $files = glob($dir . DIRECTORY_SEPARATOR . '*');
        foreach ($files as $file) {
            if (is_file($file)) {
                unlink($file);
            }
        }
        rmdir($dir);
    }
    
    public function __destruct() {
        if (is_dir($this->tempDir)) {
            $this->cleanupTempFiles($this->tempDir);
        }
    }
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    try {
        $latexContent = $_POST['latex'] ?? '';
        
        if (empty($latexContent)) {
            throw new Exception("No LaTeX content provided");
        }
        
        $compiler = new LaTeXCompiler();
        $result = $compiler->compile($latexContent);
        
        echo json_encode($result);
        
    } catch (Exception $e) {
        echo json_encode([
            'success' => false,
            'error' => $e->getMessage()
        ]);
    }
} else {
    echo json_encode([
        'success' => false,
        'error' => 'Only POST method allowed'
    ]);
}
?>