"""
LaTeX Template Management Service
Handles template library, outline generation, and custom template saving
Requirements: 9.1, 9.2, 9.3, 9.4, 9.5
"""

import logging
import uuid
import json
from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel

from database import db_manager
from llm_router import LLMRouter
from rag_service import RAGService

logger = logging.getLogger(__name__)


class TemplateCustomization(BaseModel):
    """Template customization options"""
    paper_size: Optional[str] = "letter"
    font_size: Optional[str] = "12pt"
    citation_style: Optional[str] = "APA"
    margins: Optional[str] = "1in"
    line_spacing: Optional[str] = "double"
    columns: Optional[str] = "onecolumn"


class Template(BaseModel):
    """LaTeX template model"""
    template_id: str
    name: str
    description: Optional[str]
    template_type: str
    content: str
    placeholder_content: Optional[str]
    is_builtin: bool
    is_public: bool
    customization_options: Optional[Dict[str, List[str]]]
    default_settings: Optional[Dict[str, str]]
    journal_name: Optional[str]
    conference_name: Optional[str]
    tags: Optional[List[str]]
    usage_count: int
    created_at: datetime


class OutlineSection(BaseModel):
    """Outline section model"""
    title: str
    level: int  # 1 = section, 2 = subsection, 3 = subsubsection
    description: Optional[str]
    subsections: List['OutlineSection'] = []


class DocumentOutline(BaseModel):
    """Document outline model"""
    outline_id: str
    project_id: str
    user_id: str
    title: str
    research_topic: str
    outline_structure: List[OutlineSection]
    source_document_ids: Optional[List[str]]
    latex_content: Optional[str]
    created_at: datetime


class TemplateService:
    """
    Template management service
    Requirements: 9.1, 9.2, 9.3, 9.5
    """
    
    def __init__(self):
        """Initialize template service"""
        self.db = db_manager
        logger.info("Template service initialized")
    
    async def list_templates(
        self,
        template_type: Optional[str] = None,
        user_id: Optional[str] = None,
        include_builtin: bool = True,
        include_custom: bool = True
    ) -> List[Dict[str, Any]]:
        """
        List available templates
        Requirements: 9.1
        
        Args:
            template_type: Filter by template type (article, thesis, etc.)
            user_id: User ID to include user's custom templates
            include_builtin: Include built-in templates
            include_custom: Include custom templates
        
        Returns:
            List of template dictionaries
        """
        try:
            query = """
                SELECT 
                    template_id,
                    name,
                    description,
                    template_type,
                    is_builtin,
                    is_public,
                    customization_options,
                    default_settings,
                    journal_name,
                    conference_name,
                    tags,
                    usage_count,
                    created_at
                FROM latex_templates
                WHERE deleted_at IS NULL
            """
            
            conditions = []
            params = []
            
            # Filter by type
            if template_type:
                conditions.append("template_type = %s")
                params.append(template_type)
            
            # Filter by builtin/custom
            if include_builtin and not include_custom:
                conditions.append("is_builtin = TRUE")
            elif include_custom and not include_builtin:
                conditions.append("is_builtin = FALSE")
            
            # Include user's custom templates or public templates
            if user_id:
                conditions.append("(is_builtin = TRUE OR is_public = TRUE OR user_id = %s)")
                params.append(user_id)
            else:
                conditions.append("(is_builtin = TRUE OR is_public = TRUE)")
            
            if conditions:
                query += " AND " + " AND ".join(conditions)
            
            query += " ORDER BY is_builtin DESC, usage_count DESC, name ASC"
            
            templates = await self.db.fetch_all(query, params)
            
            # Parse JSON fields
            for template in templates:
                if template.get('customization_options'):
                    template['customization_options'] = json.loads(template['customization_options'])
                if template.get('default_settings'):
                    template['default_settings'] = json.loads(template['default_settings'])
                if template.get('tags'):
                    template['tags'] = json.loads(template['tags'])
            
            logger.info(f"Listed {len(templates)} templates")
            return templates
            
        except Exception as e:
            logger.error(f"Failed to list templates: {e}")
            raise
    
    async def get_template(self, template_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get template by ID
        Requirements: 9.1, 9.2
        
        Args:
            template_id: Template identifier
            user_id: User ID for permission check
        
        Returns:
            Template dictionary with full content
        """
        try:
            query = """
                SELECT *
                FROM latex_templates
                WHERE template_id = %s
                  AND deleted_at IS NULL
                  AND (is_builtin = TRUE OR is_public = TRUE OR user_id = %s)
            """
            
            template = await self.db.fetch_one(query, [template_id, user_id])
            
            if not template:
                return None
            
            # Parse JSON fields
            if template.get('customization_options'):
                template['customization_options'] = json.loads(template['customization_options'])
            if template.get('default_settings'):
                template['default_settings'] = json.loads(template['default_settings'])
            if template.get('tags'):
                template['tags'] = json.loads(template['tags'])
            
            # Increment usage count
            await self.db.execute(
                "UPDATE latex_templates SET usage_count = usage_count + 1 WHERE template_id = %s",
                [template_id]
            )
            
            logger.info(f"Retrieved template: {template_id}")
            return template
            
        except Exception as e:
            logger.error(f"Failed to get template {template_id}: {e}")
            raise
    
    async def customize_template(
        self,
        template_id: str,
        customization: TemplateCustomization,
        user_id: Optional[str] = None
    ) -> str:
        """
        Customize template with user settings
        Requirements: 9.3
        
        Args:
            template_id: Template identifier
            customization: Customization settings
            user_id: User ID for permission check
        
        Returns:
            Customized LaTeX content
        """
        try:
            # Get template
            template = await self.get_template(template_id, user_id)
            
            if not template:
                raise ValueError(f"Template not found: {template_id}")
            
            content = template['content']
            
            # Apply customizations
            # Paper size
            if customization.paper_size:
                content = self._apply_paper_size(content, customization.paper_size)
            
            # Font size
            if customization.font_size:
                content = self._apply_font_size(content, customization.font_size)
            
            # Citation style
            if customization.citation_style:
                content = self._apply_citation_style(content, customization.citation_style)
            
            # Margins
            if customization.margins:
                content = self._apply_margins(content, customization.margins)
            
            # Line spacing
            if customization.line_spacing:
                content = self._apply_line_spacing(content, customization.line_spacing)
            
            # Columns
            if customization.columns:
                content = self._apply_columns(content, customization.columns)
            
            logger.info(f"Customized template: {template_id}")
            return content
            
        except Exception as e:
            logger.error(f"Failed to customize template {template_id}: {e}")
            raise
    
    def _apply_paper_size(self, content: str, paper_size: str) -> str:
        """Apply paper size customization"""
        import re
        
        # Replace in documentclass
        content = re.sub(
            r'\\documentclass\[([^\]]*)\]',
            lambda m: f"\\documentclass[{paper_size}paper,{m.group(1)}]" if paper_size not in m.group(1) else m.group(0),
            content
        )
        
        # Update geometry if present
        if '\\usepackage{geometry}' in content:
            if f'{paper_size}paper' not in content:
                content = content.replace(
                    '\\usepackage{geometry}',
                    f'\\usepackage[{paper_size}paper]{{geometry}}'
                )
        
        return content
    
    def _apply_font_size(self, content: str, font_size: str) -> str:
        """Apply font size customization"""
        import re
        
        # Replace in documentclass
        content = re.sub(
            r'\\documentclass\[([^\]]*)\]',
            lambda m: f"\\documentclass[{font_size},{','.join([p for p in m.group(1).split(',') if 'pt' not in p])}]",
            content
        )
        
        return content
    
    def _apply_citation_style(self, content: str, citation_style: str) -> str:
        """Apply citation style customization"""
        import re
        
        # Map citation styles to bibliography styles
        style_map = {
            'APA': 'apa',
            'MLA': 'mla',
            'Chicago': 'chicago',
            'IEEE': 'IEEEtran'
        }
        
        bib_style = style_map.get(citation_style, citation_style.lower())
        
        # Replace bibliographystyle
        content = re.sub(
            r'\\bibliographystyle\{[^}]+\}',
            f'\\\\bibliographystyle{{{bib_style}}}',
            content
        )
        
        return content
    
    def _apply_margins(self, content: str, margins: str) -> str:
        """Apply margins customization"""
        import re
        
        # Add or update geometry package
        if '\\usepackage{geometry}' in content:
            content = re.sub(
                r'\\usepackage(\[[^\]]*\])?\{geometry\}',
                f'\\\\usepackage[margin={margins}]{{geometry}}',
                content
            )
        else:
            # Add after documentclass
            content = re.sub(
                r'(\\documentclass\[[^\]]*\]\{[^}]+\})',
                f'\\1\n\\\\usepackage[margin={margins}]{{geometry}}',
                content
            )
        
        return content
    
    def _apply_line_spacing(self, content: str, line_spacing: str) -> str:
        """Apply line spacing customization"""
        import re
        
        spacing_map = {
            'single': '1.0',
            'onehalf': '1.5',
            'double': '2.0'
        }
        
        spacing_value = spacing_map.get(line_spacing, line_spacing)
        
        # Add setspace package if not present
        if '\\usepackage{setspace}' not in content:
            content = re.sub(
                r'(\\documentclass\[[^\]]*\]\{[^}]+\})',
                r'\1\n\\usepackage{setspace}',
                content
            )
        
        # Add spacing command after begin{document}
        if line_spacing == 'onehalf':
            spacing_cmd = '\\onehalfspacing'
        elif line_spacing == 'double':
            spacing_cmd = '\\doublespacing'
        else:
            spacing_cmd = f'\\setstretch{{{spacing_value}}}'
        
        content = re.sub(
            r'(\\begin\{document\})',
            r'\1\n' + spacing_cmd,
            content
        )
        
        return content
    
    def _apply_columns(self, content: str, columns: str) -> str:
        """Apply column layout customization"""
        import re
        
        # Replace in documentclass
        content = re.sub(
            r'\\documentclass\[([^\]]*)\]',
            lambda m: f"\\documentclass[{columns},{','.join([p for p in m.group(1).split(',') if 'column' not in p])}]",
            content
        )
        
        return content
    
    async def save_custom_template(
        self,
        name: str,
        description: Optional[str],
        template_type: str,
        content: str,
        user_id: str,
        project_id: Optional[str] = None,
        is_public: bool = False,
        customization_options: Optional[Dict[str, List[str]]] = None,
        default_settings: Optional[Dict[str, str]] = None,
        tags: Optional[List[str]] = None
    ) -> str:
        """
        Save custom template
        Requirements: 9.5
        
        Args:
            name: Template name
            description: Template description
            template_type: Template type
            content: LaTeX content
            user_id: User ID
            project_id: Optional project ID
            is_public: Whether template is public
            customization_options: Available customization options
            default_settings: Default settings
            tags: Template tags
        
        Returns:
            Template ID
        """
        try:
            template_id = str(uuid.uuid4())
            
            query = """
                INSERT INTO latex_templates (
                    template_id,
                    name,
                    description,
                    template_type,
                    content,
                    is_builtin,
                    is_public,
                    user_id,
                    project_id,
                    customization_options,
                    default_settings,
                    tags
                ) VALUES (%s, %s, %s, %s, %s, FALSE, %s, %s, %s, %s, %s, %s)
            """
            
            await self.db.execute(query, [
                template_id,
                name,
                description,
                template_type,
                content,
                is_public,
                user_id,
                project_id,
                json.dumps(customization_options) if customization_options else None,
                json.dumps(default_settings) if default_settings else None,
                json.dumps(tags) if tags else None
            ])
            
            logger.info(f"Saved custom template: {template_id} for user {user_id}")
            return template_id
            
        except Exception as e:
            logger.error(f"Failed to save custom template: {e}")
            raise
    
    async def delete_template(self, template_id: str, user_id: str) -> bool:
        """
        Delete custom template (soft delete)
        Requirements: 9.5
        
        Args:
            template_id: Template identifier
            user_id: User ID for permission check
        
        Returns:
            True if deleted successfully
        """
        try:
            query = """
                UPDATE latex_templates
                SET deleted_at = NOW()
                WHERE template_id = %s
                  AND user_id = %s
                  AND is_builtin = FALSE
            """
            
            result = await self.db.execute(query, [template_id, user_id])
            
            if result:
                logger.info(f"Deleted template: {template_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete template {template_id}: {e}")
            raise


class OutlineGenerator:
    """
    Generate structured outlines from research topic and documents
    Requirements: 9.4
    """
    
    def __init__(self, llm_router: LLMRouter, rag_service: Optional[RAGService] = None):
        """
        Initialize outline generator
        
        Args:
            llm_router: LLM router for outline generation
            rag_service: RAG service for document context
        """
        self.llm_router = llm_router
        self.rag_service = rag_service
        self.db = db_manager
        logger.info("Outline generator initialized")
    
    async def generate_outline(
        self,
        research_topic: str,
        project_id: str,
        user_id: str,
        document_ids: Optional[List[str]] = None,
        document_type: str = "article"
    ) -> DocumentOutline:
        """
        Generate structured outline from research topic
        Requirements: 9.4
        
        Args:
            research_topic: Research topic description
            project_id: Project identifier
            user_id: User identifier
            document_ids: Optional document IDs for context
            document_type: Type of document (article, thesis, etc.)
        
        Returns:
            DocumentOutline with hierarchical structure
        """
        try:
            # Step 1: Gather context from uploaded documents
            context = ""
            if self.rag_service and document_ids:
                logger.info(f"Gathering context from {len(document_ids)} documents")
                
                # Query documents for relevant content
                rag_results = await self.rag_service.search_service.search(
                    query=research_topic,
                    project_id=project_id,
                    document_ids=document_ids,
                    limit=20
                )
                
                if rag_results:
                    context = "\n\nRelevant content from uploaded documents:\n"
                    for i, result in enumerate(rag_results[:10]):
                        context += f"\n[Document {i+1}] {result.get('text', '')[:300]}...\n"
            
            # Step 2: Generate outline using LLM
            prompt = self._build_outline_prompt(research_topic, document_type, context)
            
            response = await self.llm_router.complete(
                query=prompt,
                context={'complexity': 'complex'},
                temperature=0.7,
                max_tokens=2000
            )
            
            # Step 3: Parse outline structure
            outline_structure = self._parse_outline(response['content'])
            
            # Step 4: Generate LaTeX structure
            latex_content = self._generate_latex_structure(outline_structure, document_type)
            
            # Step 5: Save outline to database
            outline_id = str(uuid.uuid4())
            
            query = """
                INSERT INTO document_outlines (
                    outline_id,
                    project_id,
                    user_id,
                    title,
                    research_topic,
                    outline_structure,
                    source_document_ids,
                    latex_content
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            await self.db.execute(query, [
                outline_id,
                project_id,
                user_id,
                f"Outline: {research_topic[:100]}",
                research_topic,
                json.dumps([s.dict() for s in outline_structure]),
                json.dumps(document_ids) if document_ids else None,
                latex_content
            ])
            
            logger.info(f"Generated outline: {outline_id}")
            
            return DocumentOutline(
                outline_id=outline_id,
                project_id=project_id,
                user_id=user_id,
                title=f"Outline: {research_topic[:100]}",
                research_topic=research_topic,
                outline_structure=outline_structure,
                source_document_ids=document_ids,
                latex_content=latex_content,
                created_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Failed to generate outline: {e}")
            raise
    
    def _build_outline_prompt(self, research_topic: str, document_type: str, context: str) -> str:
        """Build prompt for outline generation"""
        
        type_guidance = {
            'article': 'a research article with Introduction, Related Work, Methodology, Results, Discussion, and Conclusion',
            'thesis': 'a PhD thesis with multiple chapters including Literature Review, Methodology, Results, Discussion, and Conclusion',
            'conference_paper': 'a conference paper with Introduction, Related Work, Approach, Evaluation, and Conclusion',
            'dissertation': 'a dissertation with comprehensive chapters and appendices'
        }
        
        guidance = type_guidance.get(document_type, 'a research document')
        
        prompt = f"""Generate a detailed, structured outline for {guidance} on the following research topic:

Research Topic: {research_topic}
{context}

Create a hierarchical outline with:
1. Main sections (use ## for section headers)
2. Subsections (use ### for subsection headers)
3. Brief descriptions of what each section should cover

Format your response as:
## Section Title
Description of what this section covers

### Subsection Title
Description of what this subsection covers

Provide a comprehensive outline that covers all major aspects of the research topic."""
        
        return prompt
    
    def _parse_outline(self, outline_text: str) -> List[OutlineSection]:
        """Parse outline text into structured format"""
        import re
        
        sections = []
        current_section = None
        current_subsection = None
        
        lines = outline_text.split('\n')
        
        for line in lines:
            line = line.strip()
            
            if not line:
                continue
            
            # Section (##)
            if line.startswith('## '):
                if current_section:
                    sections.append(current_section)
                
                title = line[3:].strip()
                current_section = OutlineSection(
                    title=title,
                    level=1,
                    description="",
                    subsections=[]
                )
                current_subsection = None
            
            # Subsection (###)
            elif line.startswith('### '):
                if current_section:
                    title = line[4:].strip()
                    current_subsection = OutlineSection(
                        title=title,
                        level=2,
                        description="",
                        subsections=[]
                    )
                    current_section.subsections.append(current_subsection)
            
            # Description text
            elif not line.startswith('#'):
                if current_subsection:
                    current_subsection.description += line + " "
                elif current_section:
                    current_section.description += line + " "
        
        # Add last section
        if current_section:
            sections.append(current_section)
        
        return sections
    
    def _generate_latex_structure(self, outline_structure: List[OutlineSection], document_type: str) -> str:
        """Generate LaTeX structure from outline"""
        
        latex_lines = []
        
        for section in outline_structure:
            # Section
            latex_lines.append(f"\\section{{{section.title}}}")
            if section.description:
                latex_lines.append(f"% {section.description.strip()}")
            latex_lines.append("")
            
            # Subsections
            for subsection in section.subsections:
                latex_lines.append(f"\\subsection{{{subsection.title}}}")
                if subsection.description:
                    latex_lines.append(f"% {subsection.description.strip()}")
                latex_lines.append("")
        
        return "\n".join(latex_lines)
    
    async def get_outline(self, outline_id: str, user_id: str) -> Optional[DocumentOutline]:
        """
        Get outline by ID
        
        Args:
            outline_id: Outline identifier
            user_id: User ID for permission check
        
        Returns:
            DocumentOutline or None
        """
        try:
            query = """
                SELECT *
                FROM document_outlines
                WHERE outline_id = %s
                  AND user_id = %s
            """
            
            result = await self.db.fetch_one(query, [outline_id, user_id])
            
            if not result:
                return None
            
            # Parse JSON fields
            outline_structure = json.loads(result['outline_structure'])
            source_document_ids = json.loads(result['source_document_ids']) if result.get('source_document_ids') else None
            
            return DocumentOutline(
                outline_id=result['outline_id'],
                project_id=result['project_id'],
                user_id=result['user_id'],
                title=result['title'],
                research_topic=result['research_topic'],
                outline_structure=[OutlineSection(**s) for s in outline_structure],
                source_document_ids=source_document_ids,
                latex_content=result['latex_content'],
                created_at=result['created_at']
            )
            
        except Exception as e:
            logger.error(f"Failed to get outline {outline_id}: {e}")
            raise


# Global service instances
template_service = TemplateService()
outline_generator = None  # Lazy-loaded with dependencies

