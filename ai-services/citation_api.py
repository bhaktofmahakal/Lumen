"""
Citation Management API
FastAPI endpoints for citation management
Requirements: 13.1, 13.2, 13.3, 13.5, 13.9
"""

from fastapi import APIRouter, HTTPException, status, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging

from citation_service import citation_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/citations", tags=["citations"])


class CitationCreate(BaseModel):
    """Citation creation request"""
    project_id: str
    title: str
    authors: List[str]
    publication_year: Optional[int] = None
    journal: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    doi: Optional[str] = None
    arxiv_id: Optional[str] = None
    url: Optional[str] = None
    citation_key: Optional[str] = None


class CitationUpdate(BaseModel):
    """Citation update request"""
    title: Optional[str] = None
    authors: Optional[List[str]] = None
    publication_year: Optional[int] = None
    journal: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    doi: Optional[str] = None
    arxiv_id: Optional[str] = None
    url: Optional[str] = None
    citation_format: Optional[str] = None


class FormatUpdateRequest(BaseModel):
    """Citation format update request"""
    project_id: str
    format: str


@router.post("/import-from-pdf")
async def import_citation_from_pdf(
    project_id: str,
    document_id: Optional[str] = None,
    pdf_path: Optional[str] = None
):
    """
    Import citation from PDF metadata
    Requirements: 13.1, 13.2
    
    Args:
        project_id: Project ID
        document_id: Optional document ID
        pdf_path: Path to PDF file
    
    Returns:
        Citation metadata
    """
    try:
        if not pdf_path:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PDF path is required"
            )
        
        result = await citation_service.import_citation_from_pdf(
            pdf_path=pdf_path,
            project_id=project_id,
            document_id=document_id
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error importing citation from PDF: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )



@router.post("/create")
async def create_citation(citation: CitationCreate):
    """
    Create citation manually
    Requirements: 13.3
    
    Args:
        citation: Citation data
    
    Returns:
        Created citation
    """
    try:
        citation_data = citation.dict()
        project_id = citation_data.pop('project_id')
        
        result = await citation_service.create_citation(
            project_id=project_id,
            citation_data=citation_data
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error creating citation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/project/{project_id}")
async def get_project_citations(project_id: str):
    """
    Get all citations for a project
    Requirements: 13.3
    
    Args:
        project_id: Project ID
    
    Returns:
        List of citations
    """
    try:
        citations = await citation_service.get_citations(project_id)
        return {
            'status': 'success',
            'citations': citations,
            'count': len(citations)
        }
        
    except Exception as e:
        logger.error(f"Error getting citations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/{citation_id}")
async def update_citation(citation_id: int, updates: CitationUpdate):
    """
    Update citation
    Requirements: 13.3
    
    Args:
        citation_id: Citation ID
        updates: Citation updates
    
    Returns:
        Update status
    """
    try:
        update_data = updates.dict(exclude_unset=True)
        result = await citation_service.update_citation(citation_id, update_data)
        return result
        
    except Exception as e:
        logger.error(f"Error updating citation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{citation_id}")
async def delete_citation(citation_id: int):
    """
    Delete citation
    Requirements: 13.3
    
    Args:
        citation_id: Citation ID
    
    Returns:
        Delete status
    """
    try:
        result = await citation_service.delete_citation(citation_id)
        return result
        
    except Exception as e:
        logger.error(f"Error deleting citation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/update-format")
async def update_citation_format(request: FormatUpdateRequest):
    """
    Update citation format for all citations in project
    Requirements: 13.7
    
    Args:
        request: Format update request
    
    Returns:
        Update status
    """
    try:
        result = await citation_service.update_citation_format(
            project_id=request.project_id,
            new_format=request.format
        )
        return result
        
    except Exception as e:
        logger.error(f"Error updating citation format: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/export/{project_id}")
async def export_citations(
    project_id: str,
    format: str = 'bibtex'
):
    """
    Export citations in specified format
    Requirements: 13.9
    
    Args:
        project_id: Project ID
        format: Export format (bibtex, ris, endnote)
    
    Returns:
        Formatted citation string
    """
    try:
        if format not in ['bibtex', 'ris', 'endnote']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid format. Must be 'bibtex', 'ris', or 'endnote'"
            )
        
        result = await citation_service.export_citations(project_id, format)
        
        # Set appropriate content type
        content_types = {
            'bibtex': 'application/x-bibtex',
            'ris': 'application/x-research-info-systems',
            'endnote': 'application/xml'
        }
        
        return {
            'status': 'success',
            'format': format,
            'content': result,
            'content_type': content_types[format]
        }
        
    except Exception as e:
        logger.error(f"Error exporting citations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
