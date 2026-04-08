"""
AI Research Copilot - Python FastAPI Service
Main application entry point with health check endpoints
"""

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from datetime import datetime, timezone

from config import settings
from health import HealthChecker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize health checker
health_checker = HealthChecker()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting AI Research Copilot service...")
    
    # Startup: Initialize connections
    await health_checker.initialize()
    
    yield
    
    # Shutdown: Cleanup
    logger.info("Shutting down AI Research Copilot service...")
    await health_checker.cleanup()


# Create FastAPI application
app = FastAPI(
    title="AI Research Copilot API",
    description="AI-powered document analysis and research assistance",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Root endpoint
@app.get("/", status_code=status.HTTP_200_OK)
async def root():
    """Root endpoint"""
    return {
        "service": "AI Research Copilot API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "detailed_health": "/health/detailed",
            "mysql_health": "/health/mysql",
            "redis_health": "/health/redis",
            "qdrant_health": "/health/qdrant",
            "ollama_health": "/health/ollama",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }


# Health Check Endpoints

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Basic health check endpoint
    Returns OK if service is running
    """
    return {
        "status": "healthy",
        "service": "ai-research-copilot",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/health/detailed", status_code=status.HTTP_200_OK)
async def detailed_health_check():
    """
    Detailed health check endpoint
    Checks all service dependencies (MySQL, Redis, Qdrant, Ollama)
    """
    health_status = await health_checker.check_all()
    
    # Determine overall status
    all_healthy = all(
        service["status"] == "healthy" 
        for service in health_status["services"].values()
        if service["status"] != "unavailable"  # Ollama is optional
    )
    
    status_code = status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return JSONResponse(
        status_code=status_code,
        content=health_status
    )


@app.get("/health/mysql", status_code=status.HTTP_200_OK)
async def mysql_health_check():
    """MySQL database health check"""
    result = await health_checker.check_mysql()
    status_code = status.HTTP_200_OK if result["status"] == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(status_code=status_code, content=result)


@app.get("/health/redis", status_code=status.HTTP_200_OK)
async def redis_health_check():
    """Redis cache health check"""
    result = await health_checker.check_redis()
    status_code = status.HTTP_200_OK if result["status"] == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(status_code=status_code, content=result)


@app.get("/health/qdrant", status_code=status.HTTP_200_OK)
async def qdrant_health_check():
    """Qdrant vector store health check"""
    result = await health_checker.check_qdrant()
    status_code = status.HTTP_200_OK if result["status"] == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(status_code=status_code, content=result)


@app.get("/health/ollama", status_code=status.HTTP_200_OK)
async def ollama_health_check():
    """Ollama LLM health check (optional service)"""
    result = await health_checker.check_ollama()
    # Ollama is optional, so unavailable is not an error
    status_code = status.HTTP_200_OK if result["status"] in ["healthy", "unavailable"] else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(status_code=status_code, content=result)


# Document Ingestion Endpoints

from fastapi import File, UploadFile, Form
from models import DocumentUploadResponse, DocumentMetadata
from document_service import document_service


@app.post("/api/documents/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(..., description="PDF file to upload"),
    project_id: str = Form(..., description="Project ID"),
    user_id: str = Form(..., description="User ID"),
    title: str = Form(None, description="Document title (optional)"),
    authors: str = Form(None, description="Document authors as JSON array (optional)")
):
    """
    Upload a PDF document for processing
    
    Requirements: 1.1, 1.8
    - Validates file format (PDF only) and size (max 50MB)
    - Generates unique document ID
    - Stores metadata in MySQL
    - Stores PDF file in local storage
    - Detects document type for optimal processing
    """
    import json
    
    # Parse authors if provided
    authors_list = None
    if authors:
        try:
            authors_list = json.loads(authors)
        except:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid authors format. Must be JSON array"
            )
    
    return await document_service.upload_document(
        file=file,
        project_id=project_id,
        user_id=user_id,
        title=title,
        authors=authors_list
    )


@app.get("/api/documents/{document_id}", response_model=DocumentMetadata)
async def get_document(document_id: str):
    """
    Get document metadata by ID
    """
    metadata = await document_service.get_document_metadata(document_id)
    if not metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {document_id}"
        )
    return metadata


@app.get("/api/projects/{project_id}/documents")
async def get_project_documents(project_id: str):
    """
    Get all documents for a project
    """
    from database import db_manager
    documents = await db_manager.get_project_documents(project_id)
    return {"documents": documents}


# Memory System Endpoints
from memory_api import router as memory_router
app.include_router(memory_router)

# Chat/RAG Endpoints
from chat_api import router as chat_router
app.include_router(chat_router)

# OCR Endpoints
from ocr_service import router as ocr_router
app.include_router(ocr_router)

# LaTeX Compilation Endpoints
from latex_api import router as latex_router
app.include_router(latex_router)

# Template Management Endpoints
from template_api import router as template_router
app.include_router(template_router)

# Citation Management Endpoints
from citation_api import router as citation_router
app.include_router(citation_router)

# Summarization and Data Extraction Endpoints
from summarization_api import router as summarization_router
app.include_router(summarization_router)


# External Import Endpoints

from models import ExternalDocumentRequest
from external_import import external_import_service


@app.post("/api/documents/import", status_code=status.HTTP_201_CREATED)
async def import_external_document(
    request: ExternalDocumentRequest,
    user_id: str = Form(..., description="User ID")
):
    """
    Import document from external source (DOI, arXiv, PubMed)
    
    Requirements: 1.4
    - Fetches metadata from Crossref, arXiv, or PubMed APIs
    - Downloads PDF if available
    - Stores document with metadata
    """
    from fastapi import HTTPException
    import uuid
    import json
    
    # Import document
    result = await external_import_service.import_document(
        source_type=request.source_type,
        identifier=request.identifier
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not fetch document from {request.source_type}: {request.identifier}"
        )
    
    pdf_content, metadata = result
    
    # If PDF is available, save it
    document_id = str(uuid.uuid4())
    file_path = None
    file_size = 0
    file_hash = None
    
    if pdf_content:
        # Save PDF
        filename = f"{request.identifier.replace('/', '_')}.pdf"
        from storage import storage_manager
        file_path = await storage_manager.save_file(document_id, filename, pdf_content)
        file_size = len(pdf_content)
        
        # Calculate hash
        file_hash = document_service.calculate_file_hash(pdf_content)
        
        # Check for duplicates
        from database import db_manager
        duplicate = await db_manager.check_duplicate_document(file_hash, request.project_id)
        if duplicate:
            # Clean up saved file
            await storage_manager.delete_file(document_id, filename)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Document already exists: {duplicate['filename']} (uploaded {duplicate['created_at']})"
            )
    
    # Store metadata in database
    from database import db_manager
    document_data = {
        'document_id': document_id,
        'project_id': request.project_id,
        'user_id': user_id,
        'filename': metadata.get('title', request.identifier) + '.pdf' if pdf_content else None,
        'file_path': file_path,
        'file_size': file_size,
        'file_hash': file_hash,
        'title': metadata.get('title'),
        'authors': json.dumps(metadata.get('authors')) if metadata.get('authors') else None,
        'publication_date': metadata.get('publication_date'),
        'doi': metadata.get('doi'),
        'arxiv_id': metadata.get('arxiv_id'),
        'pubmed_id': metadata.get('pubmed_id'),
        'document_type': 'standard',
        'status': 'pending' if pdf_content else 'metadata_only',
        'page_count': 0
    }
    
    await db_manager.insert_document(document_data)
    
    return {
        "document_id": document_id,
        "metadata": metadata,
        "pdf_available": pdf_content is not None,
        "message": f"Document imported successfully from {request.source_type}"
    }
