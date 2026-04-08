"""
Data models for document ingestion and processing
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class DocumentType(str, Enum):
    """Document type classification"""
    STANDARD = "standard"
    SCIENTIFIC = "scientific"
    COMPLEX = "complex"
    SCANNED = "scanned"


class DocumentStatus(str, Enum):
    """Document processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentUploadRequest(BaseModel):
    """Request model for document upload"""
    project_id: str = Field(..., description="Project ID to associate document with")
    title: Optional[str] = Field(None, description="Document title (optional)")
    authors: Optional[List[str]] = Field(None, description="Document authors (optional)")


class DocumentMetadata(BaseModel):
    """Document metadata"""
    document_id: str
    project_id: str
    user_id: str
    filename: str
    file_size: int
    file_hash: str
    title: Optional[str] = None
    authors: Optional[List[str]] = None
    publication_date: Optional[str] = None
    doi: Optional[str] = None
    arxiv_id: Optional[str] = None
    pubmed_id: Optional[str] = None
    document_type: DocumentType
    status: DocumentStatus
    page_count: int = 0
    created_at: datetime
    updated_at: datetime


class DocumentUploadResponse(BaseModel):
    """Response model for document upload"""
    document_id: str
    filename: str
    file_size: int
    status: DocumentStatus
    message: str


class ChunkMetadata(BaseModel):
    """Metadata for text chunks"""
    document_id: str
    chunk_id: int
    page_number: Optional[int] = None
    section: Optional[str] = None


class TextChunk(BaseModel):
    """Text chunk with metadata"""
    text: str
    metadata: ChunkMetadata
    embedding: Optional[List[float]] = None


class ExternalDocumentRequest(BaseModel):
    """Request model for importing documents from external sources"""
    project_id: str
    source_type: str = Field(..., description="Type: doi, arxiv, or pubmed")
    identifier: str = Field(..., description="DOI, arXiv ID, or PubMed ID")
    
    @field_validator('source_type')
    @classmethod
    def validate_source_type(cls, v):
        if v not in ['doi', 'arxiv', 'pubmed']:
            raise ValueError('source_type must be doi, arxiv, or pubmed')
        return v
