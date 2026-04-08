"""
FastAPI endpoints for document summarization and data extraction
Requirements: 5.1, 5.2, 5.3, 5.7, 6.1, 6.2, 6.3, 6.5, 6.7, 14.1, 14.2
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import logging

from summarization_service import (
    SummarizationService,
    ComparativeSummarizationService,
    DataExtractionService,
    DataExportService,
    SummaryLength,
    DocumentSummary,
    ComparativeSummary,
    ExtractedData
)
from equation_extraction_service import (
    EquationExtractionService,
    ExtractedEquation
)
from llm_router import LLMRouter
from vector_store import QdrantVectorStore
from embeddings import EmbeddingGenerator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/summarization", tags=["summarization"])

# Initialize services
llm_router = LLMRouter()
vector_store = QdrantVectorStore()
embedding_generator = EmbeddingGenerator()

summarization_service = SummarizationService(llm_router, vector_store, embedding_generator)
comparative_service = ComparativeSummarizationService(llm_router, summarization_service)
data_extraction_service = DataExtractionService(llm_router, vector_store)
data_export_service = DataExportService()
equation_service = EquationExtractionService()


# Request/Response Models

class SummarizeRequest(BaseModel):
    """Request model for document summarization"""
    document_id: str
    project_id: Optional[str] = None
    length: SummaryLength = SummaryLength.STANDARD
    document_title: Optional[str] = None


class ComparativeSummarizeRequest(BaseModel):
    """Request model for comparative summarization"""
    document_ids: List[str]
    project_id: Optional[str] = None
    document_titles: Optional[Dict[str, str]] = None


class ExtractDataRequest(BaseModel):
    """Request model for data extraction"""
    document_id: str
    project_id: Optional[str] = None
    data_types: Optional[List[str]] = None


class ExtractDataMultipleRequest(BaseModel):
    """Request model for extracting data from multiple documents"""
    document_ids: List[str]
    project_id: Optional[str] = None
    data_types: Optional[List[str]] = None


class ExportDataRequest(BaseModel):
    """Request model for data export"""
    extracted_data: List[Dict[str, Any]]
    format: str  # "csv", "json", "excel"


class ExtractEquationsRequest(BaseModel):
    """Request model for equation extraction"""
    pdf_path: str
    page_numbers: Optional[List[int]] = None


# Endpoints

@router.post("/summarize", response_model=DocumentSummary)
async def summarize_document(request: SummarizeRequest):
    """
    Generate structured summary of a document
    Requirements: 5.1, 5.2, 5.3
    
    Args:
        request: Summarization request
    
    Returns:
        DocumentSummary with structured sections
    """
    try:
        logger.info(
            f"Summarizing document {request.document_id} "
            f"with length {request.length.value}"
        )
        
        summary = await summarization_service.generate_summary(
            document_id=request.document_id,
            project_id=request.project_id,
            length=request.length,
            document_title=request.document_title
        )
        
        return summary
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error summarizing document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/summarize/comparative", response_model=ComparativeSummary)
async def summarize_comparative(request: ComparativeSummarizeRequest):
    """
    Generate comparative summary for multiple documents
    Requirements: 5.7
    
    Args:
        request: Comparative summarization request
    
    Returns:
        ComparativeSummary with similarities, differences, and themes
    """
    try:
        logger.info(
            f"Generating comparative summary for {len(request.document_ids)} documents"
        )
        
        if len(request.document_ids) < 2:
            raise HTTPException(
                status_code=400,
                detail="Need at least 2 documents for comparative summary"
            )
        
        summary = await comparative_service.generate_comparative_summary(
            document_ids=request.document_ids,
            project_id=request.project_id,
            document_titles=request.document_titles
        )
        
        return summary
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating comparative summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract-data", response_model=ExtractedData)
async def extract_data(request: ExtractDataRequest):
    """
    Extract specific data from a research paper
    Requirements: 6.1, 6.2, 6.3
    
    Args:
        request: Data extraction request
    
    Returns:
        ExtractedData with structured information
    """
    try:
        logger.info(f"Extracting data from document {request.document_id}")
        
        data = await data_extraction_service.extract_data(
            document_id=request.document_id,
            project_id=request.project_id,
            data_types=request.data_types
        )
        
        return data
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error extracting data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract-data/multiple", response_model=List[ExtractedData])
async def extract_data_multiple(request: ExtractDataMultipleRequest):
    """
    Extract data from multiple documents
    Requirements: 6.1, 6.2
    
    Args:
        request: Multiple document extraction request
    
    Returns:
        List of ExtractedData for each document
    """
    try:
        logger.info(f"Extracting data from {len(request.document_ids)} documents")
        
        data_list = await data_extraction_service.extract_data_from_multiple(
            document_ids=request.document_ids,
            project_id=request.project_id,
            data_types=request.data_types
        )
        
        return data_list
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error extracting data from multiple documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export-data")
async def export_data(request: ExportDataRequest):
    """
    Export extracted data in specified format
    Requirements: 6.5
    
    Args:
        request: Export request with data and format
    
    Returns:
        Exported data in requested format
    """
    try:
        logger.info(f"Exporting data in {request.format} format")
        
        # Convert dict data to ExtractedData objects
        extracted_data = [
            ExtractedData(**data) for data in request.extracted_data
        ]
        
        if request.format == "csv":
            content = data_export_service.export_to_csv(extracted_data)
            return {
                "format": "csv",
                "content": content,
                "filename": "extracted_data.csv"
            }
        
        elif request.format == "json":
            content = data_export_service.export_to_json(extracted_data)
            return {
                "format": "json",
                "content": content,
                "filename": "extracted_data.json"
            }
        
        elif request.format == "excel":
            import base64
            content_bytes = data_export_service.export_to_excel(extracted_data)
            content_b64 = base64.b64encode(content_bytes).decode()
            return {
                "format": "excel",
                "content": content_b64,
                "filename": "extracted_data.xlsx",
                "encoding": "base64"
            }
        
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported format: {request.format}. Use csv, json, or excel."
            )
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error exporting data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract-equations", response_model=List[ExtractedEquation])
async def extract_equations(request: ExtractEquationsRequest):
    """
    Extract equations from PDF and convert to LaTeX
    Requirements: 6.7, 14.1, 14.2
    
    Args:
        request: Equation extraction request
    
    Returns:
        List of ExtractedEquation objects
    """
    try:
        logger.info(f"Extracting equations from PDF: {request.pdf_path}")
        
        equations = await equation_service.extract_equations_from_pdf(
            pdf_path=request.pdf_path,
            page_numbers=request.page_numbers
        )
        
        return equations
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error extracting equations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract-equation-from-image", response_model=ExtractedEquation)
async def extract_equation_from_image(
    image: UploadFile = File(...),
    image_format: str = Query("png", description="Image format (png, jpg, etc.)")
):
    """
    Extract equation from uploaded image
    Requirements: 14.1, 14.2
    
    Args:
        image: Uploaded image file
        image_format: Image format
    
    Returns:
        ExtractedEquation object
    """
    try:
        logger.info(f"Extracting equation from uploaded image")
        
        # Read image data
        image_data = await image.read()
        
        equation = await equation_service.extract_equation_from_image(
            image_data=image_data,
            image_format=image_format
        )
        
        return equation
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error extracting equation from image: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "summarization",
        "nougat_available": equation_service.nougat_available
    }
