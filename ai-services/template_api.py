"""
LaTeX Template API Endpoints
Requirements: 9.1, 9.2, 9.3, 9.4, 9.5
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from template_service import (
    template_service,
    outline_generator,
    TemplateCustomization,
    Template,
    DocumentOutline
)
from llm_router import LLMRouter
from rag_service import RAGService
import redis
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/templates", tags=["templates"])

# Initialize Redis for LLM router
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    decode_responses=True
)


# Request/Response Models

class ListTemplatesRequest(BaseModel):
    """List templates request"""
    template_type: Optional[str] = None
    user_id: Optional[str] = None
    include_builtin: bool = True
    include_custom: bool = True


class GetTemplateRequest(BaseModel):
    """Get template request"""
    template_id: str
    user_id: Optional[str] = None


class CustomizeTemplateRequest(BaseModel):
    """Customize template request"""
    template_id: str
    user_id: Optional[str] = None
    customization: TemplateCustomization


class SaveTemplateRequest(BaseModel):
    """Save custom template request - Requirement 9.5"""
    name: str
    description: Optional[str] = None
    template_type: str
    content: str
    user_id: str
    project_id: Optional[str] = None
    is_public: bool = False
    customization_options: Optional[dict] = None
    default_settings: Optional[dict] = None
    tags: Optional[List[str]] = None


class GenerateOutlineRequest(BaseModel):
    """Generate outline request - Requirement 9.4"""
    research_topic: str
    project_id: str
    user_id: str
    document_ids: Optional[List[str]] = None
    document_type: str = "article"


class TemplateResponse(BaseModel):
    """Template response"""
    success: bool
    template: Optional[dict] = None
    message: Optional[str] = None


class TemplateListResponse(BaseModel):
    """Template list response"""
    success: bool
    templates: List[dict]
    count: int


class CustomizedTemplateResponse(BaseModel):
    """Customized template response"""
    success: bool
    content: str
    template_id: str


class OutlineResponse(BaseModel):
    """Outline response"""
    success: bool
    outline: Optional[dict] = None
    message: Optional[str] = None


# Endpoints

@router.get("/list", response_model=TemplateListResponse)
async def list_templates(
    template_type: Optional[str] = None,
    user_id: Optional[str] = None,
    include_builtin: bool = True,
    include_custom: bool = True
):
    """
    List available LaTeX templates
    Requirements: 9.1
    
    Query Parameters:
        - template_type: Filter by type (article, thesis, conference_paper, etc.)
        - user_id: Include user's custom templates
        - include_builtin: Include built-in templates (default: true)
        - include_custom: Include custom templates (default: true)
    
    Returns:
        List of templates with metadata
    """
    try:
        templates = await template_service.list_templates(
            template_type=template_type,
            user_id=user_id,
            include_builtin=include_builtin,
            include_custom=include_custom
        )
        
        return TemplateListResponse(
            success=True,
            templates=templates,
            count=len(templates)
        )
        
    except Exception as e:
        logger.error(f"Failed to list templates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list templates: {str(e)}"
        )


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(template_id: str, user_id: Optional[str] = None):
    """
    Get template by ID with full content
    Requirements: 9.1, 9.2
    
    Path Parameters:
        - template_id: Template identifier
    
    Query Parameters:
        - user_id: User ID for permission check
    
    Returns:
        Template with full LaTeX content and placeholder guidance
    """
    try:
        template = await template_service.get_template(template_id, user_id)
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template not found: {template_id}"
            )
        
        return TemplateResponse(
            success=True,
            template=template
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get template {template_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get template: {str(e)}"
        )


@router.post("/customize", response_model=CustomizedTemplateResponse)
async def customize_template(request: CustomizeTemplateRequest):
    """
    Customize template with user settings
    Requirements: 9.3
    
    Request Body:
        - template_id: Template to customize
        - user_id: User ID for permission check
        - customization: Customization settings (paper_size, font, margins, etc.)
    
    Returns:
        Customized LaTeX content with applied settings
    """
    try:
        customized_content = await template_service.customize_template(
            template_id=request.template_id,
            customization=request.customization,
            user_id=request.user_id
        )
        
        return CustomizedTemplateResponse(
            success=True,
            content=customized_content,
            template_id=request.template_id
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to customize template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to customize template: {str(e)}"
        )


@router.post("/save", response_model=TemplateResponse)
async def save_custom_template(request: SaveTemplateRequest):
    """
    Save custom template for reuse
    Requirements: 9.5
    
    Request Body:
        - name: Template name
        - description: Template description
        - template_type: Template type
        - content: LaTeX content
        - user_id: User ID
        - project_id: Optional project ID
        - is_public: Whether template is public (default: false)
        - customization_options: Available customization options
        - default_settings: Default settings
        - tags: Template tags
    
    Returns:
        Created template with ID
    """
    try:
        template_id = await template_service.save_custom_template(
            name=request.name,
            description=request.description,
            template_type=request.template_type,
            content=request.content,
            user_id=request.user_id,
            project_id=request.project_id,
            is_public=request.is_public,
            customization_options=request.customization_options,
            default_settings=request.default_settings,
            tags=request.tags
        )
        
        return TemplateResponse(
            success=True,
            template={'template_id': template_id},
            message="Template saved successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to save custom template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save template: {str(e)}"
        )


@router.delete("/{template_id}")
async def delete_template(template_id: str, user_id: str):
    """
    Delete custom template
    Requirements: 9.5
    
    Path Parameters:
        - template_id: Template identifier
    
    Query Parameters:
        - user_id: User ID for permission check
    
    Returns:
        Success status
    """
    try:
        success = await template_service.delete_template(template_id, user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found or permission denied"
            )
        
        return {
            "success": True,
            "message": "Template deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete template {template_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete template: {str(e)}"
        )


@router.post("/outline/generate", response_model=OutlineResponse)
async def generate_outline(request: GenerateOutlineRequest):
    """
    Generate structured outline from research topic
    Requirements: 9.4
    
    Request Body:
        - research_topic: Research topic description
        - project_id: Project identifier
        - user_id: User identifier
        - document_ids: Optional document IDs for context
        - document_type: Type of document (article, thesis, etc.)
    
    Returns:
        Generated outline with hierarchical structure and LaTeX content
    """
    try:
        # Initialize outline generator if not already done
        global outline_generator
        if outline_generator is None:
            from template_service import OutlineGenerator
            llm_router = LLMRouter(redis_client)
            rag_service = RAGService()
            outline_generator = OutlineGenerator(llm_router, rag_service)
        
        outline = await outline_generator.generate_outline(
            research_topic=request.research_topic,
            project_id=request.project_id,
            user_id=request.user_id,
            document_ids=request.document_ids,
            document_type=request.document_type
        )
        
        return OutlineResponse(
            success=True,
            outline={
                'outline_id': outline.outline_id,
                'title': outline.title,
                'research_topic': outline.research_topic,
                'outline_structure': [s.dict() for s in outline.outline_structure],
                'source_document_ids': outline.source_document_ids,
                'latex_content': outline.latex_content,
                'created_at': outline.created_at.isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to generate outline: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate outline: {str(e)}"
        )


@router.get("/outline/{outline_id}", response_model=OutlineResponse)
async def get_outline(outline_id: str, user_id: str):
    """
    Get outline by ID
    Requirements: 9.4
    
    Path Parameters:
        - outline_id: Outline identifier
    
    Query Parameters:
        - user_id: User ID for permission check
    
    Returns:
        Outline with structure and LaTeX content
    """
    try:
        # Initialize outline generator if not already done
        global outline_generator
        if outline_generator is None:
            from template_service import OutlineGenerator
            llm_router = LLMRouter(redis_client)
            rag_service = RAGService()
            outline_generator = OutlineGenerator(llm_router, rag_service)
        
        outline = await outline_generator.get_outline(outline_id, user_id)
        
        if not outline:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Outline not found: {outline_id}"
            )
        
        return OutlineResponse(
            success=True,
            outline={
                'outline_id': outline.outline_id,
                'title': outline.title,
                'research_topic': outline.research_topic,
                'outline_structure': [s.dict() for s in outline.outline_structure],
                'source_document_ids': outline.source_document_ids,
                'latex_content': outline.latex_content,
                'created_at': outline.created_at.isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get outline {outline_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get outline: {str(e)}"
        )

