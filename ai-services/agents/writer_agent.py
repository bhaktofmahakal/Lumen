"""
Writer Agent
Drafts sections, generates LaTeX-formatted content, maintains consistency
Requirements: 38.4
"""

import logging
from typing import Dict, List, Optional, Any
import asyncio

logger = logging.getLogger(__name__)


class WriterAgent:
    """
    Writer agent for content generation and LaTeX formatting
    Requirements: 38.4
    
    Capabilities:
    - Section drafting based on research findings
    - LaTeX formatting (equations, tables, figures)
    - Terminology consistency across document
    - Writing style adaptation (formal, technical, concise)
    - Iterative refinement based on feedback
    """
    
    def __init__(self, llm_router, memory_service):
        """
        Initialize writer agent
        
        Args:
            llm_router: LLM router for content generation
            memory_service: Memory service for context and terminology
        """
        self.llm_router = llm_router
        self.memory_service = memory_service
        
        logger.info("Writer agent initialized")
    
    async def execute(
        self,
        query: str,
        research_findings: List[Dict[str, Any]],
        research_gaps: List[str],
        review_feedback: str = "",
        iteration_count: int = 0
    ) -> Dict[str, Any]:
        """
        Execute writing task
        Requirements: 38.4
        
        Args:
            query: Original research query
            research_findings: Key findings from researcher agent
            research_gaps: Research gaps identified
            review_feedback: Feedback from reviewer (for iterations)
            iteration_count: Current iteration number
        
        Returns:
            Dict with generated content
        """
        logger.info(
            f"Writer agent executing (iteration {iteration_count}): "
            f"{len(research_findings)} findings, {len(research_gaps)} gaps"
        )
        
        try:
            # Generate content based on findings
            content = await self._generate_content(
                query=query,
                findings=research_findings,
                gaps=research_gaps,
                feedback=review_feedback,
                iteration=iteration_count
            )
            
            logger.info(f"Writer agent completed: {len(content)} chars generated")
            
            return {
                "content": content
            }
            
        except Exception as e:
            logger.error(f"Writer agent execution failed: {e}")
            raise
    
    async def _generate_content(
        self,
        query: str,
        findings: List[Dict[str, Any]],
        gaps: List[str],
        feedback: str,
        iteration: int
    ) -> str:
        """
        Generate LaTeX-formatted content
        
        Args:
            query: Research query
            findings: Key findings
            gaps: Research gaps
            feedback: Review feedback
            iteration: Iteration number
        
        Returns:
            Generated LaTeX content
        """
        try:
            # Build findings summary
            findings_text = "\n".join([
                f"{i+1}. {f.get('finding', '')} "
                f"(Source: Document {f.get('document_id', 'unknown')}, "
                f"Page {f.get('page_number', 'N/A')})"
                for i, f in enumerate(findings)
            ])
            
            # Build gaps summary
            gaps_text = "\n".join([
                f"- {gap}"
                for gap in gaps
            ])
            
            # Build prompt based on iteration
            if iteration == 0:
                # First iteration - generate initial draft
                prompt = f"""Write a comprehensive literature review section in LaTeX format based on the following research query and findings.

Research Query: {query}

Key Findings:
{findings_text}

Research Gaps:
{gaps_text}

Requirements:
1. Write in formal academic style
2. Use proper LaTeX formatting (sections, citations, equations if needed)
3. Structure: Introduction → Key Findings → Research Gaps → Conclusion
4. Include inline citations using \\cite{{}} format (use document IDs as citation keys)
5. Maintain terminology consistency
6. Length: 2-3 pages (approximately 1000-1500 words)

Generate the LaTeX content:"""
            else:
                # Subsequent iterations - incorporate feedback
                prompt = f"""Revise the following literature review based on the reviewer's feedback.

Original Query: {query}

Key Findings:
{findings_text}

Research Gaps:
{gaps_text}

Reviewer Feedback:
{feedback}

Requirements:
1. Address all points in the reviewer feedback
2. Maintain formal academic style and LaTeX formatting
3. Ensure terminology consistency
4. Keep inline citations using \\cite{{}} format
5. Improve clarity and completeness

Generate the revised LaTeX content:"""
            
            # Generate content using LLM
            response = await self.llm_router.complete(
                query=prompt,
                context={"document_count": len(findings)},
                temperature=0.7,
                max_tokens=2000,
                use_cache=False
            )
            
            content = response['content']
            
            # Ensure LaTeX formatting
            if not content.strip().startswith("\\"):
                # Wrap in basic LaTeX structure if not already formatted
                content = f"""\\section{{Literature Review}}

{content}
"""
            
            logger.info(f"Generated content: {len(content)} chars")
            return content
            
        except Exception as e:
            logger.error(f"Error generating content: {e}")
            raise
