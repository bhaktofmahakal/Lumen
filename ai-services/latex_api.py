"""
LaTeX Compilation and AI-Assisted Writing API
Handles LaTeX document compilation to PDF and AI-powered content generation
Requirements: 7.3, 7.4, 7.5, 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.8
"""

import os
import subprocess
import tempfile
import shutil
import logging
import re
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from llm_router import LLMRouter
from memory_service import MemoryRouter, ShortTermMemory, LongTermMemory, EpisodicMemory
from rag_service import RAGService
import redis

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/latex", tags=["latex"])

# Initialize Redis for caching
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    decode_responses=True
)

# Memory system instances (lazy-loaded)
stm = None
ltm = None
em = None
memory_router = None


def get_memory_router():
    """Get or create memory router instance (lazy initialization)"""
    global stm, ltm, em, memory_router
    if memory_router is None:
        stm = ShortTermMemory()
        ltm = LongTermMemory()
        em = EpisodicMemory()
        memory_router = MemoryRouter(stm, ltm, em)
    return memory_router


class CompileRequest(BaseModel):
    """LaTeX compilation request"""
    content: str
    project_id: str
    document_id: Optional[str] = None


class GenerateRequest(BaseModel):
    """AI writing assistance request - Requirements: 8.1, 8.2"""
    prompt: str
    user_id: str
    project_id: str
    document_ids: Optional[List[str]] = None  # Context documents
    content_type: str = "section"  # section, paragraph, equation, table, figure
    style: Optional[str] = "formal"  # formal, technical, concise - Requirement 8.4
    existing_content: Optional[str] = None  # For iterative refinement - Requirement 8.6
    session_id: Optional[str] = None


class GenerateResponse(BaseModel):
    """AI writing assistance response"""
    success: bool
    content: str
    citations: Optional[List[Dict[str, str]]] = None
    terminology: Optional[Dict[str, str]] = None  # Key terms used for consistency
    generation_time: float


class BibliographyRequest(BaseModel):
    """Bibliography generation request - Requirement 8.8"""
    citation_ids: List[str]
    project_id: str
    style: str = "APA"  # APA, MLA, Chicago, IEEE


class BibliographyResponse(BaseModel):
    """Bibliography generation response"""
    success: bool
    bibtex_entries: List[str]
    formatted_bibliography: str


class ErrorFix(BaseModel):
    """AI-generated error fix suggestion"""
    error_type: str
    line: Optional[int]
    original_error: str
    suggested_fix: str
    explanation: str


class CompileResponse(BaseModel):
    """LaTeX compilation response"""
    success: bool
    pdf_url: Optional[str] = None
    errors: Optional[List[Dict[str, str]]] = None
    warnings: Optional[List[str]] = None
    compilation_time: float
    ai_fixes: Optional[List[ErrorFix]] = None  # Requirement 7.5


class LaTeXCompiler:
    """
    LaTeX compiler with error parsing and AI-assisted fixes
    Requirements: 7.3, 7.4
    """
    
    def __init__(self):
        self.max_compilation_time = 10  # seconds (Requirement 7.3)
        self.output_dir = Path("latex-output")
        self.output_dir.mkdir(exist_ok=True)
    
    async def compile(self, content: str, document_id: str) -> CompileResponse:
        """
        Compile LaTeX document to PDF
        Requirements: 7.3, 7.4
        
        Args:
            content: LaTeX source code
            document_id: Unique document identifier
        
        Returns:
            CompileResponse with PDF URL or errors
        """
        import time
        start_time = time.time()
        
        # Validate content
        if not content.strip():
            raise HTTPException(status_code=400, detail="LaTeX content cannot be empty")
        
        # Security validation
        self._validate_latex_content(content)
        
        # Create temporary directory for compilation
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            tex_file = temp_path / "document.tex"
            pdf_file = temp_path / "document.pdf"
            
            # Write LaTeX content
            tex_file.write_text(content, encoding='utf-8')
            
            try:
                # Compile with timeout
                result = await asyncio.wait_for(
                    self._run_pdflatex(tex_file, temp_path),
                    timeout=self.max_compilation_time
                )
                
                compilation_time = time.time() - start_time
                
                if result['success'] and pdf_file.exists():
                    # Move PDF to output directory
                    output_pdf = self.output_dir / f"{document_id}.pdf"
                    shutil.copy(pdf_file, output_pdf)
                    
                    return CompileResponse(
                        success=True,
                        pdf_url=f"/latex-output/{document_id}.pdf",
                        warnings=result.get('warnings'),
                        compilation_time=compilation_time
                    )
                else:
                    return CompileResponse(
                        success=False,
                        errors=result.get('errors', []),
                        warnings=result.get('warnings'),
                        compilation_time=compilation_time
                    )
                    
            except asyncio.TimeoutError:
                logger.error(f"LaTeX compilation timeout for document {document_id}")
                return CompileResponse(
                    success=False,
                    errors=[{
                        "type": "timeout",
                        "message": f"Compilation exceeded {self.max_compilation_time} seconds limit",
                        "line": "N/A"
                    }],
                    compilation_time=self.max_compilation_time
                )
            except Exception as e:
                logger.error(f"LaTeX compilation error: {e}")
                return CompileResponse(
                    success=False,
                    errors=[{
                        "type": "system_error",
                        "message": str(e),
                        "line": "N/A"
                    }],
                    compilation_time=time.time() - start_time
                )
    
    def _validate_latex_content(self, content: str):
        """
        Validate LaTeX content for security
        Prevents shell injection and dangerous commands
        """
        dangerous_commands = [
            r'\\write18',
            r'\\immediate\\write18',
            r'\\input\{[|]',
            r'\\openin',
            r'\\openout',
            r'\\special\{system',
            r'\\special\{!',
            'shell-escape'
        ]
        
        content_lower = content.lower()
        for dangerous in dangerous_commands:
            if re.search(dangerous, content_lower, re.IGNORECASE):
                raise HTTPException(
                    status_code=400,
                    detail=f"Potentially dangerous LaTeX command detected: {dangerous}"
                )
    
    async def _run_pdflatex(self, tex_file: Path, work_dir: Path) -> Dict:
        """
        Run pdflatex compilation
        Requirements: 7.3, 7.4
        
        Args:
            tex_file: Path to .tex file
            work_dir: Working directory
        
        Returns:
            Dict with success status, errors, and warnings
        """
        # Try multiple LaTeX engines
        engines = ['pdflatex', 'xelatex', 'lualatex']
        
        for engine in engines:
            try:
                # Run compilation
                process = await asyncio.create_subprocess_exec(
                    engine,
                    '-interaction=nonstopmode',
                    '-file-line-error',
                    '-halt-on-error',
                    str(tex_file),
                    cwd=work_dir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await process.communicate()
                output = stdout.decode('utf-8', errors='ignore')
                
                # Parse output for errors and warnings
                errors = self._parse_errors(output)
                warnings = self._parse_warnings(output)
                
                # Check if PDF was generated
                pdf_file = work_dir / "document.pdf"
                if pdf_file.exists() and pdf_file.stat().st_size > 0:
                    return {
                        'success': True,
                        'engine': engine,
                        'warnings': warnings
                    }
                elif not errors:
                    # PDF not generated but no errors found
                    errors = [{
                        'type': 'unknown',
                        'message': 'PDF generation failed without specific errors',
                        'line': None
                    }]
                
                # If errors found, return them
                if errors:
                    return {
                        'success': False,
                        'engine': engine,
                        'errors': errors,
                        'warnings': warnings
                    }
                    
            except FileNotFoundError:
                logger.warning(f"LaTeX engine {engine} not found")
                continue
            except Exception as e:
                logger.error(f"Error running {engine}: {e}")
                continue
        
        # All engines failed
        return {
            'success': False,
            'errors': [{
                'type': 'system_error',
                'message': 'No LaTeX engine available or all engines failed',
                'line': 'N/A'
            }]
        }
    
    def _parse_errors(self, output: str) -> List[Dict[str, str]]:
        """
        Parse LaTeX compilation errors
        Requirements: 7.4
        
        Args:
            output: LaTeX compilation output
        
        Returns:
            List of error dictionaries with line numbers and messages
        """
        errors = []
        
        # Pattern 1: file:line: error message
        pattern1 = re.compile(r'([^:]+\.tex):(\d+):\s*(.+?)(?=\n|$)', re.MULTILINE)
        for match in pattern1.finditer(output):
            errors.append({
                'type': 'syntax_error',
                'line': int(match.group(2)),
                'message': match.group(3).strip()
            })
        
        # Pattern 2: ! Error message followed by l.line
        pattern2 = re.compile(r'!\s*(.+?)\nl\.(\d+)', re.MULTILINE | re.DOTALL)
        for match in pattern2.finditer(output):
            error_msg = match.group(1).strip()
            line_num = int(match.group(2))
            
            if not any(e['line'] == line_num for e in errors):
                errors.append({
                    'type': 'latex_error',
                    'line': line_num,
                    'message': error_msg
                })
        
        # Pattern 3: LaTeX Error: message
        pattern3 = re.compile(r'LaTeX Error:\s*(.+?)(?=\n\n|\n!|\Z)', re.MULTILINE | re.DOTALL)
        for match in pattern3.finditer(output):
            error_msg = match.group(1).strip()
            
            # Try to find associated line number
            line_match = re.search(r'l\.(\d+)', error_msg)
            line_num = int(line_match.group(1)) if line_match else 'N/A'
            
            errors.append({
                'type': 'latex_error',
                'line': line_num,
                'message': error_msg
            })
        
        return errors
    
    def _parse_warnings(self, output: str) -> List[str]:
        """
        Parse LaTeX compilation warnings
        
        Args:
            output: LaTeX compilation output
        
        Returns:
            List of warning messages
        """
        warnings = []
        
        # Pattern: Package name Warning: message
        pattern = re.compile(r'Package\s+([^\s]+)\s+Warning:\s*(.+?)(?=\n\n|\n[A-Z]|\Z)', 
                           re.MULTILINE | re.DOTALL)
        
        for match in pattern.finditer(output):
            package = match.group(1)
            message = match.group(2).strip()
            warnings.append(f"{package}: {message}")
        
        # Generic warnings
        generic_pattern = re.compile(r'Warning:\s*(.+?)(?=\n\n|\Z)', re.MULTILINE)
        for match in generic_pattern.finditer(output):
            warning = match.group(1).strip()
            if warning not in warnings:
                warnings.append(warning)
        
        return warnings[:10]  # Limit to 10 warnings
    
    async def generate_error_fixes(self, errors: List[Dict[str, str]], content: str) -> List[ErrorFix]:
        """
        Generate AI-assisted error correction suggestions
        Requirements: 7.5
        
        Args:
            errors: List of compilation errors
            content: LaTeX source code
        
        Returns:
            List of ErrorFix suggestions
        """
        if not errors:
            return []
        
        try:
            # Initialize LLM router
            llm_router = LLMRouter(redis_client)
            
            fixes = []
            
            for error in errors[:5]:  # Limit to 5 errors to avoid token limits
                error_type = error.get('type', 'unknown')
                line_num = error.get('line')
                error_msg = error.get('message', '')
                
                # Get context around error line
                if line_num:
                    lines = content.split('\n')
                    start = max(0, line_num - 3)
                    end = min(len(lines), line_num + 2)
                    context = '\n'.join(lines[start:end])
                else:
                    context = content[:500]  # First 500 chars if no line number
                
                # Create prompt for LLM
                prompt = f"""You are a LaTeX expert. Analyze this compilation error and suggest a fix.

Error Type: {error_type}
Error Message: {error_msg}
Line Number: {line_num if line_num else 'Unknown'}

LaTeX Code Context:
```latex
{context}
```

Provide:
1. A clear explanation of what caused the error
2. The specific fix to apply (exact code change)
3. Why this fix resolves the error

Format your response as:
EXPLANATION: <explanation>
FIX: <exact code to replace or add>
REASON: <why this works>
"""
                
                # Get AI suggestion
                response = await llm_router.complete(
                    query=prompt,
                    context={'complexity': 'medium'},
                    temperature=0.3,  # Lower temperature for more precise fixes
                    max_tokens=500
                )
                
                # Parse response
                content_text = response['content']
                
                explanation_match = re.search(r'EXPLANATION:\s*(.+?)(?=FIX:|$)', content_text, re.DOTALL)
                fix_match = re.search(r'FIX:\s*(.+?)(?=REASON:|$)', content_text, re.DOTALL)
                reason_match = re.search(r'REASON:\s*(.+?)$', content_text, re.DOTALL)
                
                if explanation_match and fix_match:
                    fixes.append(ErrorFix(
                        error_type=error_type,
                        line=line_num,
                        original_error=error_msg,
                        suggested_fix=fix_match.group(1).strip(),
                        explanation=explanation_match.group(1).strip() + '\n\n' + 
                                  (reason_match.group(1).strip() if reason_match else '')
                    ))
            
            return fixes
            
        except Exception as e:
            logger.error(f"Failed to generate error fixes: {e}")
            return []


# Global compiler instance
compiler = LaTeXCompiler()


class AIWritingAssistant:
    """
    AI-powered LaTeX writing assistance
    Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.8
    """
    
    def __init__(self, llm_router: LLMRouter, memory_router: MemoryRouter, rag_service: Optional[RAGService] = None):
        """
        Initialize AI writing assistant
        
        Args:
            llm_router: LLM router for content generation
            memory_router: Memory router for context and preferences
            rag_service: RAG service for citation-backed content
        """
        self.llm_router = llm_router
        self.memory_router = memory_router
        self.rag_service = rag_service
        
        logger.info("AI Writing Assistant initialized")
    
    async def generate_content(
        self,
        prompt: str,
        user_id: str,
        project_id: str,
        content_type: str = "section",
        style: str = "formal",
        document_ids: Optional[List[str]] = None,
        existing_content: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> GenerateResponse:
        """
        Generate LaTeX-formatted content based on prompt
        Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6
        
        Args:
            prompt: User's writing prompt
            user_id: User identifier
            project_id: Project identifier
            content_type: Type of content (section, paragraph, equation, table, figure)
            style: Writing style (formal, technical, concise)
            document_ids: Source document IDs for citations
            existing_content: Existing content for iterative refinement
            session_id: Session identifier for context
        
        Returns:
            GenerateResponse with generated LaTeX content and citations
        """
        import time
        start_time = time.time()
        
        try:
            # Step 1: Retrieve relevant context from memory and documents
            context = await self._gather_context(
                user_id=user_id,
                project_id=project_id,
                session_id=session_id,
                document_ids=document_ids,
                prompt=prompt
            )
            
            # Step 2: Get user style preferences from memory
            style_prefs = await self._get_style_preferences(user_id, project_id, style)
            
            # Step 3: Generate content based on type
            if content_type == "equation":
                generated = await self._generate_equation(prompt, context, style_prefs)
            elif content_type == "table":
                generated = await self._generate_table(prompt, context, style_prefs)
            elif content_type == "figure":
                generated = await self._generate_figure(prompt, context, style_prefs)
            elif existing_content:
                # Iterative refinement - Requirement 8.6
                generated = await self._refine_content(
                    prompt, existing_content, context, style_prefs
                )
            else:
                # Section or paragraph generation
                generated = await self._generate_section(
                    prompt, content_type, context, style_prefs
                )
            
            # Step 4: Extract and format citations
            citations = self._extract_citations(generated['content'], context.get('sources', []))
            
            # Step 5: Store generated content in memory for consistency
            await self._store_in_memory(
                user_id=user_id,
                project_id=project_id,
                session_id=session_id,
                content=generated['content'],
                terminology=generated.get('terminology', {})
            )
            
            generation_time = time.time() - start_time
            
            return GenerateResponse(
                success=True,
                content=generated['content'],
                citations=citations,
                terminology=generated.get('terminology'),
                generation_time=generation_time
            )
            
        except Exception as e:
            logger.error(f"Content generation failed: {e}")
            raise HTTPException(status_code=500, detail=f"Content generation failed: {str(e)}")
    
    async def _gather_context(
        self,
        user_id: str,
        project_id: str,
        session_id: Optional[str],
        document_ids: Optional[List[str]],
        prompt: str
    ) -> Dict:
        """
        Gather context from memory and documents
        Requirements: 8.1, 8.3
        """
        context = {
            'memories': [],
            'sources': [],
            'terminology': {}
        }
        
        # Get relevant memories
        memory_context = {
            'project_id': project_id,
            'session_id': session_id
        }
        
        memories = self.memory_router.route_query(
            query=prompt,
            user_id=user_id,
            context=memory_context
        )
        context['memories'] = memories
        
        # Extract terminology from project memory
        for memory in memories:
            if memory.get('metadata', {}).get('memory_type') == 'project_finding':
                # Extract key terms (simplified - in production use NLP)
                text = memory.get('text', '')
                # Store for consistency
                context['terminology'].update(self._extract_key_terms(text))
        
        # Get relevant document passages if RAG service available
        if self.rag_service and document_ids:
            try:
                rag_results = await self.rag_service.query(
                    query=prompt,
                    project_id=project_id,
                    document_ids=document_ids,
                    top_k=5
                )
                context['sources'] = rag_results.get('results', [])
            except Exception as e:
                logger.warning(f"Failed to retrieve document context: {e}")
        
        return context
    
    def _extract_key_terms(self, text: str) -> Dict[str, str]:
        """Extract key terms from text (simplified implementation)"""
        # In production, use NLP for term extraction
        # For now, return empty dict
        return {}
    
    async def _get_style_preferences(
        self,
        user_id: str,
        project_id: str,
        requested_style: str
    ) -> Dict:
        """
        Get user style preferences from memory
        Requirements: 8.4
        """
        # Get memory instances from router
        em_instance = self.memory_router.em if hasattr(self.memory_router, 'em') else None
        ltm_instance = self.memory_router.ltm if hasattr(self.memory_router, 'ltm') else None
        
        # Check episodic memory for user preferences
        prefs = []
        if em_instance and hasattr(em_instance, 'get_user_preferences'):
            prefs = em_instance.get_user_preferences(user_id, preference_type="writing_style")
        
        # Check long-term memory for project-specific preferences
        project_prefs = []
        if ltm_instance and hasattr(ltm_instance, 'search'):
            project_prefs = ltm_instance.search(
                query="writing style preferences",
                user_id=user_id,
                filters={'project_id': project_id, 'memory_type': 'project_preference'}
            )
        
        # Build style configuration
        style_config = {
            'style': requested_style,
            'tone': 'formal',
            'verbosity': 'standard'
        }
        
        # Override with user preferences if available
        if prefs:
            for pref in prefs:
                pref_value = pref.get('metadata', {}).get('preference_value')
                if pref_value:
                    style_config['style'] = pref_value
        
        if project_prefs:
            for pref in project_prefs:
                pref_value = pref.get('metadata', {}).get('preference_value')
                if pref_value:
                    style_config['style'] = pref_value
        
        return style_config
    
    async def _generate_section(
        self,
        prompt: str,
        content_type: str,
        context: Dict,
        style_prefs: Dict
    ) -> Dict:
        """
        Generate section or paragraph content
        Requirements: 8.2, 8.3, 8.4
        """
        # Build context from sources
        sources_text = ""
        if context.get('sources'):
            sources_text = "\n\nRelevant Source Material:\n"
            for i, source in enumerate(context['sources'][:5]):
                sources_text += f"\n[Source {i+1}] (Document: {source.get('document_id', 'unknown')}, Page: {source.get('page', 'N/A')})\n"
                sources_text += source.get('text', '')[:500] + "\n"
        
        # Build style instructions
        style_instructions = self._build_style_instructions(style_prefs)
        
        # Create prompt
        system_prompt = f"""You are an expert academic writer specializing in LaTeX document preparation.

{style_instructions}

Your task is to generate a well-structured {content_type} in LaTeX format based on the user's request and provided source material.

Requirements:
1. Use proper LaTeX formatting (sections, subsections, paragraphs)
2. Include inline citations using \\cite{{document_id}} format for any information from sources
3. Maintain academic tone and clarity
4. Use consistent terminology throughout
5. Format equations using proper LaTeX math environments if needed
6. Ensure the content is publication-ready

When citing sources, use the document ID from the source material as the citation key."""
        
        user_prompt = f"""User Request: {prompt}
{sources_text}

Generate the LaTeX content:"""
        
        # Generate content
        response = await self.llm_router.complete(
            query=user_prompt,
            context={'complexity': 'complex', 'system_prompt': system_prompt},
            temperature=0.7,
            max_tokens=2000
        )
        
        content = response['content']
        
        # Ensure LaTeX formatting
        if not content.strip().startswith('\\'):
            content = f"\\subsection{{{content_type.title()}}}\n\n{content}"
        
        return {
            'content': content,
            'terminology': {}  # Extract in production
        }
    
    async def _generate_equation(
        self,
        prompt: str,
        context: Dict,
        style_prefs: Dict
    ) -> Dict:
        """
        Generate LaTeX equation
        Requirements: 8.5
        """
        system_prompt = """You are a LaTeX expert specializing in mathematical notation.

Generate a properly formatted LaTeX equation based on the user's description.

Requirements:
1. Use appropriate math environment (equation, align, gather, etc.)
2. Use correct LaTeX math notation and symbols
3. Include equation labels if appropriate
4. Ensure proper spacing and formatting
5. For inline equations, use $...$ or \\(...\\)
6. For display equations, use \\begin{equation}...\\end{equation} or $$...$$

Provide ONLY the LaTeX code for the equation, no explanations."""
        
        user_prompt = f"""Generate a LaTeX equation for: {prompt}

LaTeX equation:"""
        
        response = await self.llm_router.complete(
            query=user_prompt,
            context={'complexity': 'medium', 'system_prompt': system_prompt},
            temperature=0.3,  # Lower temperature for precise formatting
            max_tokens=500
        )
        
        return {
            'content': response['content'].strip(),
            'terminology': {}
        }
    
    async def _generate_table(
        self,
        prompt: str,
        context: Dict,
        style_prefs: Dict
    ) -> Dict:
        """
        Generate LaTeX table
        Requirements: 8.2
        """
        system_prompt = """You are a LaTeX expert specializing in table formatting.

Generate a properly formatted LaTeX table based on the user's description.

Requirements:
1. Use appropriate table environment (tabular, table, longtable, etc.)
2. Include proper column specifications
3. Use \\hline for horizontal lines
4. Include caption and label if appropriate
5. Ensure proper alignment and spacing
6. Use booktabs package commands (\\toprule, \\midrule, \\bottomrule) for professional appearance

Provide ONLY the LaTeX code for the table, no explanations."""
        
        user_prompt = f"""Generate a LaTeX table for: {prompt}

LaTeX table:"""
        
        response = await self.llm_router.complete(
            query=user_prompt,
            context={'complexity': 'medium', 'system_prompt': system_prompt},
            temperature=0.3,
            max_tokens=1000
        )
        
        return {
            'content': response['content'].strip(),
            'terminology': {}
        }
    
    async def _generate_figure(
        self,
        prompt: str,
        context: Dict,
        style_prefs: Dict
    ) -> Dict:
        """
        Generate LaTeX figure environment
        Requirements: 8.2
        """
        system_prompt = """You are a LaTeX expert specializing in figure formatting.

Generate a properly formatted LaTeX figure environment based on the user's description.

Requirements:
1. Use \\begin{figure}...\\end{figure} environment
2. Include \\includegraphics command with appropriate options
3. Add caption and label
4. Use proper positioning options [htbp]
5. Include \\centering for centered figures

Provide ONLY the LaTeX code for the figure environment, no explanations."""
        
        user_prompt = f"""Generate a LaTeX figure environment for: {prompt}

LaTeX figure:"""
        
        response = await self.llm_router.complete(
            query=user_prompt,
            context={'complexity': 'simple', 'system_prompt': system_prompt},
            temperature=0.3,
            max_tokens=500
        )
        
        return {
            'content': response['content'].strip(),
            'terminology': {}
        }
    
    async def _refine_content(
        self,
        prompt: str,
        existing_content: str,
        context: Dict,
        style_prefs: Dict
    ) -> Dict:
        """
        Refine existing content based on feedback
        Requirements: 8.6
        """
        system_prompt = """You are an expert academic editor specializing in LaTeX documents.

Refine the provided LaTeX content based on the user's feedback while maintaining:
1. Existing structure and formatting
2. Citation integrity
3. Terminology consistency
4. LaTeX syntax correctness

Make targeted improvements without unnecessary changes."""
        
        user_prompt = f"""Existing Content:
```latex
{existing_content}
```

User Feedback: {prompt}

Provide the refined LaTeX content:"""
        
        response = await self.llm_router.complete(
            query=user_prompt,
            context={'complexity': 'complex', 'system_prompt': system_prompt},
            temperature=0.5,
            max_tokens=2000
        )
        
        return {
            'content': response['content'].strip(),
            'terminology': {}
        }
    
    def _build_style_instructions(self, style_prefs: Dict) -> str:
        """Build style instructions for LLM"""
        style = style_prefs.get('style', 'formal')
        
        style_map = {
            'formal': "Use formal academic language with precise terminology. Avoid contractions and colloquialisms.",
            'technical': "Use technical language appropriate for expert readers. Include detailed explanations of methods and concepts.",
            'concise': "Be concise and direct. Eliminate unnecessary words while maintaining clarity and completeness."
        }
        
        return style_map.get(style, style_map['formal'])
    
    def _extract_citations(self, content: str, sources: List[Dict]) -> List[Dict[str, str]]:
        """
        Extract citations from generated content
        Requirements: 8.3
        """
        citations = []
        
        # Find all \cite{} commands
        cite_pattern = r'\\cite\{([^}]+)\}'
        matches = re.finditer(cite_pattern, content)
        
        for match in matches:
            cite_key = match.group(1)
            
            # Find corresponding source
            source = None
            for s in sources:
                if s.get('document_id') == cite_key:
                    source = s
                    break
            
            if source:
                page = source.get('page')
                citations.append({
                    'cite_key': cite_key,
                    'document_id': source.get('document_id'),
                    'page': str(page) if page is not None else 'N/A',  # Convert to string
                    'text_excerpt': source.get('text', '')[:200]
                })
        
        return citations
    
    async def _store_in_memory(
        self,
        user_id: str,
        project_id: str,
        session_id: Optional[str],
        content: str,
        terminology: Dict
    ):
        """
        Store generated content in memory for consistency
        Requirements: 8.7
        """
        try:
            # Get memory instances from router
            stm_instance = self.memory_router.stm if hasattr(self.memory_router, 'stm') else None
            ltm_instance = self.memory_router.ltm if hasattr(self.memory_router, 'ltm') else None
            
            # Store in short-term memory if session active
            if session_id and stm_instance and hasattr(stm_instance, 'add'):
                stm_instance.add(
                    messages=[{"role": "assistant", "content": f"Generated content: {content[:200]}..."}],
                    user_id=user_id,
                    metadata={
                        'session_id': session_id,
                        'project_id': project_id,
                        'memory_type': 'generated_content'
                    }
                )
            
            # Store terminology in long-term memory
            if terminology and ltm_instance and hasattr(ltm_instance, 'store_project_finding'):
                for term, definition in terminology.items():
                    ltm_instance.store_project_finding(
                        finding=f"Term: {term} - {definition}",
                        user_id=user_id,
                        project_id=project_id,
                        finding_type='terminology'
                    )
        except Exception as e:
            logger.warning(f"Failed to store in memory: {e}")
    
    async def generate_bibliography(
        self,
        citation_ids: List[str],
        project_id: str,
        style: str = "APA"
    ) -> BibliographyResponse:
        """
        Generate BibTeX entries and formatted bibliography
        Requirements: 8.8
        """
        try:
            # In production, fetch citation metadata from database
            # For now, generate placeholder BibTeX entries
            
            bibtex_entries = []
            formatted_entries = []
            
            for cite_id in citation_ids:
                # Generate BibTeX entry (placeholder)
                bibtex = f"""@article{{{cite_id},
  author = {{Author, A.}},
  title = {{Document Title}},
  journal = {{Journal Name}},
  year = {{2024}},
  volume = {{1}},
  pages = {{1--10}}
}}"""
                bibtex_entries.append(bibtex)
                
                # Format according to style
                if style == "APA":
                    formatted = f"Author, A. (2024). Document Title. Journal Name, 1, 1-10."
                elif style == "MLA":
                    formatted = f"Author, A. \"Document Title.\" Journal Name 1 (2024): 1-10."
                elif style == "Chicago":
                    formatted = f"Author, A. \"Document Title.\" Journal Name 1 (2024): 1-10."
                elif style == "IEEE":
                    formatted = f"[{len(formatted_entries)+1}] A. Author, \"Document Title,\" Journal Name, vol. 1, pp. 1-10, 2024."
                else:
                    formatted = f"Author, A. (2024). Document Title. Journal Name, 1, 1-10."
                
                formatted_entries.append(formatted)
            
            formatted_bibliography = "\n\n".join(formatted_entries)
            
            return BibliographyResponse(
                success=True,
                bibtex_entries=bibtex_entries,
                formatted_bibliography=formatted_bibliography
            )
            
        except Exception as e:
            logger.error(f"Bibliography generation failed: {e}")
            raise HTTPException(status_code=500, detail=f"Bibliography generation failed: {str(e)}")


# Global instances
writing_assistant = None


def get_writing_assistant() -> AIWritingAssistant:
    """Get or create writing assistant instance"""
    global writing_assistant
    if writing_assistant is None:
        llm_router = LLMRouter(redis_client)
        mem_router = get_memory_router()  # Use lazy-loaded memory router
        rag_service = None  # Initialize if needed
        writing_assistant = AIWritingAssistant(llm_router, mem_router, rag_service)
    return writing_assistant


@router.post("/generate", response_model=GenerateResponse)
async def generate_latex_content(request: GenerateRequest):
    """
    Generate LaTeX-formatted content using AI
    Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6
    
    Args:
        request: GenerateRequest with prompt and context
    
    Returns:
        GenerateResponse with generated LaTeX content and citations
    """
    try:
        assistant = get_writing_assistant()
        
        result = await assistant.generate_content(
            prompt=request.prompt,
            user_id=request.user_id,
            project_id=request.project_id,
            content_type=request.content_type,
            style=request.style,
            document_ids=request.document_ids,
            existing_content=request.existing_content,
            session_id=request.session_id
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Content generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bibliography", response_model=BibliographyResponse)
async def generate_bibliography(request: BibliographyRequest):
    """
    Generate BibTeX entries and formatted bibliography
    Requirements: 8.8
    
    Args:
        request: BibliographyRequest with citation IDs and style
    
    Returns:
        BibliographyResponse with BibTeX entries and formatted bibliography
    """
    try:
        assistant = get_writing_assistant()
        
        result = await assistant.generate_bibliography(
            citation_ids=request.citation_ids,
            project_id=request.project_id,
            style=request.style
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bibliography generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Global compiler instance
compiler = LaTeXCompiler()


@router.post("/compile", response_model=CompileResponse)
async def compile_latex(request: CompileRequest, background_tasks: BackgroundTasks):
    """
    Compile LaTeX document to PDF
    Requirements: 7.3, 7.4, 7.5
    
    Args:
        request: CompileRequest with LaTeX content
        background_tasks: FastAPI background tasks
    
    Returns:
        CompileResponse with PDF URL or errors with AI-generated fixes
    """
    document_id = request.document_id or f"doc_{request.project_id}_{os.urandom(4).hex()}"
    
    try:
        result = await compiler.compile(request.content, document_id)
        
        # If compilation failed, generate AI fixes in background
        if not result.success and result.errors:
            ai_fixes = await compiler.generate_error_fixes(result.errors, request.content)
            result.ai_fixes = ai_fixes
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Compilation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
