"""
Document ingestion service for PDF processing
"""

import hashlib
import uuid
from typing import Optional, Tuple, BinaryIO, List
from fastapi import UploadFile, HTTPException, status
import logging
import fitz  # PyMuPDF
import json

from config import settings
from models import (
    DocumentType, DocumentStatus, DocumentMetadata,
    DocumentUploadResponse
)
from database import db_manager
from storage import storage_manager

logger = logging.getLogger(__name__)


class DocumentValidator:
    """Validates uploaded documents"""
    
    def __init__(self):
        self.max_size = settings.MAX_UPLOAD_SIZE
        self.allowed_types = settings.allowed_file_types_list
    
    def validate_file(self, file: UploadFile) -> Tuple[bool, Optional[str]]:
        """
        Validate uploaded file
        Returns: (is_valid, error_message)
        """
        # Check file extension
        if not file.filename:
            return False, "Filename is required"
        
        file_ext = file.filename.split('.')[-1].lower()
        if file_ext not in self.allowed_types:
            return False, f"Invalid file type. Only {', '.join(self.allowed_types)} files are allowed"
        
        # Check content type
        if file.content_type and not file.content_type.startswith('application/pdf'):
            return False, "Invalid content type. Only PDF files are allowed"
        
        return True, None
    
    def validate_file_size(self, file_size: int) -> Tuple[bool, Optional[str]]:
        """Validate file size"""
        if file_size > self.max_size:
            max_mb = self.max_size / (1024 * 1024)
            return False, f"File size exceeds maximum allowed size of {max_mb}MB"
        
        if file_size == 0:
            return False, "File is empty"
        
        return True, None
    
    def validate_pdf_content(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """Validate PDF file can be opened and read"""
        try:
            doc = fitz.open(file_path)
            if doc.page_count == 0:
                return False, "PDF has no pages"
            doc.close()
            return True, None
        except Exception as e:
            return False, f"Invalid PDF file: {str(e)}"


class DocumentTypeDetector:
    """Detects document type for optimal processing"""
    
    def detect_type(self, pdf_path: str) -> DocumentType:
        """Detect PDF type for optimal processing"""
        try:
            doc = fitz.open(pdf_path)
            
            # Get first page text
            if doc.page_count > 0:
                text = doc[0].get_text()
            else:
                return DocumentType.STANDARD
            
            # Check if scanned (no text or very little text)
            if len(text.strip()) < 50:
                return DocumentType.SCANNED
            
            # Check for equations (LaTeX patterns or mathematical symbols)
            if self._has_equations(text):
                return DocumentType.SCIENTIFIC
            
            # Check for complex layout (tables, figures)
            if self._has_complex_layout(doc):
                return DocumentType.COMPLEX
            
            doc.close()
            return DocumentType.STANDARD
            
        except Exception as e:
            logger.error(f"Error detecting document type: {e}")
            return DocumentType.STANDARD
    
    def _has_equations(self, text: str) -> bool:
        """Check for mathematical content"""
        import re
        math_indicators = [
            r'∫', r'∑', r'∏', r'√', r'∂', r'∇',  # Math symbols
            r'theorem', r'lemma', r'proof', r'equation',  # Math keywords
            r'\d+\s*[+\-*/=]\s*\d+',  # Simple equations
        ]
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in math_indicators)
    
    def _has_complex_layout(self, doc) -> bool:
        """Check for tables and figures"""
        try:
            if doc.page_count > 0:
                page = doc[0]
                # Check for images
                images = page.get_images()
                if len(images) > 2:
                    return True
                
                # Check for tables (simple heuristic: many horizontal/vertical lines)
                drawings = page.get_drawings()
                if len(drawings) > 20:
                    return True
            
            return False
        except:
            return False


class DocumentService:
    """Main document ingestion service"""
    
    def __init__(self):
        self.validator = DocumentValidator()
        self.detector = DocumentTypeDetector()
    
    def calculate_file_hash(self, content: bytes) -> str:
        """Calculate SHA-256 hash of file content"""
        return hashlib.sha256(content).hexdigest()
    
    async def upload_document(
        self,
        file: UploadFile,
        project_id: str,
        user_id: str,
        title: Optional[str] = None,
        authors: Optional[List[str]] = None
    ) -> DocumentUploadResponse:
        """
        Upload and validate document
        Requirements: 1.1, 1.8
        """
        
        # Validate file type
        is_valid, error_msg = self.validator.validate_file(file)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # Validate file size
        is_valid, error_msg = self.validator.validate_file_size(file_size)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # Calculate file hash
        file_hash = self.calculate_file_hash(file_content)
        
        # Check for duplicates (Requirement 1.11)
        duplicate = await db_manager.check_duplicate_document(file_hash, project_id)
        if duplicate:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Document already exists: {duplicate['filename']} (uploaded {duplicate['created_at']})"
            )
        
        # Generate unique document ID
        document_id = str(uuid.uuid4())
        
        # Save file to storage
        file_path = await storage_manager.save_file(document_id, file.filename, file_content)
        
        # Validate PDF content
        is_valid, error_msg = self.validator.validate_pdf_content(file_path)
        if not is_valid:
            # Clean up saved file
            await storage_manager.delete_file(document_id, file.filename)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # Detect document type
        doc_type = self.detector.detect_type(file_path)
        
        # Get page count
        doc = fitz.open(file_path)
        page_count = doc.page_count
        doc.close()
        
        # Store metadata in database
        document_data = {
            'document_id': document_id,
            'project_id': project_id,
            'user_id': user_id,
            'filename': file.filename,
            'file_path': file_path,
            'file_size': file_size,
            'file_hash': file_hash,
            'title': title,
            'authors': json.dumps(authors) if authors else None,
            'publication_date': None,
            'doi': None,
            'arxiv_id': None,
            'pubmed_id': None,
            'document_type': doc_type.value,
            'status': DocumentStatus.PENDING.value,
            'page_count': page_count
        }
        
        await db_manager.insert_document(document_data)
        
        logger.info(f"Document uploaded successfully: {document_id}")
        
        return DocumentUploadResponse(
            document_id=document_id,
            filename=file.filename,
            file_size=file_size,
            status=DocumentStatus.PENDING,
            message=f"Document uploaded successfully. Type: {doc_type.value}, Pages: {page_count}"
        )
    
    async def get_document_metadata(self, document_id: str) -> Optional[DocumentMetadata]:
        """Get document metadata"""
        doc_data = await db_manager.get_document(document_id)
        if not doc_data:
            return None
        
        # Parse authors JSON
        authors = None
        if doc_data.get('authors'):
            try:
                authors = json.loads(doc_data['authors'])
            except:
                authors = None
        
        return DocumentMetadata(
            document_id=doc_data['document_id'],
            project_id=doc_data['project_id'],
            user_id=doc_data['user_id'],
            filename=doc_data['filename'],
            file_size=doc_data['file_size'],
            file_hash=doc_data['file_hash'],
            title=doc_data.get('title'),
            authors=authors,
            publication_date=doc_data.get('publication_date'),
            doi=doc_data.get('doi'),
            arxiv_id=doc_data.get('arxiv_id'),
            pubmed_id=doc_data.get('pubmed_id'),
            document_type=DocumentType(doc_data['document_type']),
            status=DocumentStatus(doc_data['status']),
            page_count=doc_data['page_count'],
            created_at=doc_data['created_at'],
            updated_at=doc_data['updated_at']
        )


# Global document service instance
document_service = DocumentService()
