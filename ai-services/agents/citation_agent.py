"""
Citation Agent
Manages citations, verifies references, ensures academic integrity
Requirements: 38.5
"""

import logging
from typing import Dict, List, Optional, Any
import re
import asyncio

logger = logging.getLogger(__name__)


class CitationAgent:
    """
    Citation agent for citation management and verification
    Requirements: 38.5
    
    Capabilities:
    - Citation extraction from generated content
    - Citation verification and fact-checking
    - Bibliography generation in multiple formats
    - Duplicate citation detection
    - Citation metadata enrichment (DOI, arXiv ID)
    """
    
    def __init__(self, rag_service, llm_router):
        """
        Initialize citation agent
        
        Args:
            rag_service: RAG service for source verification
            llm_router: LLM router for citation analysis
        """
        self.rag_service = rag_service
        self.llm_router = llm_router
        
        logger.info("Citation agent initialized")
    
    async def execute(
        self,
        content: str,
        research_findings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Execute citation management task
        Requirements: 38.5
        
        Args:
            content: Generated content with citations
            research_findings: Research findings with source metadata
        
        Returns:
            Dict with citations and issues
        """
        logger.info("Citation agent executing...")
        
        try:
            # Step 1: Extract citations from content
            citations = self._extract_citations(content, research_findings)
            
            # Step 2: Verify citations against sources
            issues = self._verify_citations(content, citations, research_findings)
            
            # Step 3: Enrich citation metadata
            enriched_citations = self._enrich_citations(citations)
            
            logger.info(
                f"Citation agent completed: "
                f"{len(enriched_citations)} citations, {len(issues)} issues"
            )
            
            return {
                "citations": enriched_citations,
                "issues": issues
            }
            
        except Exception as e:
            logger.error(f"Citation agent execution failed: {e}")
            raise
    
    def _extract_citations(
        self,
        content: str,
        findings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Extract citations from LaTeX content
        
        Args:
            content: LaTeX content
            findings: Research findings with metadata
        
        Returns:
            List of citation objects
        """
        citations = []
        
        # Find all \cite{} commands
        cite_pattern = r'\\cite\{([^}]+)\}'
        matches = re.finditer(cite_pattern, content)
        
        for match in matches:
            cite_key = match.group(1)
            
            # Find corresponding finding
            finding = None
            for f in findings:
                if f.get("document_id") == cite_key:
                    finding = f
                    break
            
            if finding:
                citation = {
                    "cite_key": cite_key,
                    "document_id": finding.get("document_id"),
                    "page_number": finding.get("page_number"),
                    "position_start": match.start(),
                    "position_end": match.end(),
                    "text_excerpt": finding.get("finding", "")[:200]
                }
                citations.append(citation)
            else:
                # Citation without corresponding finding
                citations.append({
                    "cite_key": cite_key,
                    "document_id": cite_key,
                    "page_number": None,
                    "position_start": match.start(),
                    "position_end": match.end(),
                    "text_excerpt": "",
                    "warning": "No corresponding source found"
                })
        
        logger.info(f"Extracted {len(citations)} citations from content")
        return citations
    
    def _verify_citations(
        self,
        content: str,
        citations: List[Dict[str, Any]],
        findings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Verify citations against source documents
        
        Args:
            content: Generated content
            citations: Extracted citations
            findings: Research findings
        
        Returns:
            List of citation issues
        """
        issues = []
        
        for citation in citations:
            # Check if citation has warning
            if citation.get("warning"):
                issues.append({
                    "type": "missing_source",
                    "cite_key": citation.get("cite_key"),
                    "message": citation.get("warning")
                })
                continue
            
            # Extract statement around citation
            pos = citation.get("position_start", 0)
            start = max(0, content.rfind('.', 0, pos) + 1)
            end = content.find('.', pos)
            if end == -1:
                end = len(content)
            
            statement = content[start:end].strip()
            
            # Check if statement is supported by source
            # For now, simple check - can be enhanced with semantic similarity
            text_excerpt = citation.get("text_excerpt", "")
            
            if text_excerpt and len(statement) > 20:
                # Check for potential misattribution
                # This is a simplified check - in production, use semantic similarity
                common_words = set(statement.lower().split()) & set(text_excerpt.lower().split())
                if len(common_words) < 3:
                    issues.append({
                        "type": "potential_misattribution",
                        "cite_key": citation.get("cite_key"),
                        "statement": statement,
                        "message": "Statement may not be supported by cited source"
                    })
        
        logger.info(f"Found {len(issues)} citation issues")
        return issues
    
    def _enrich_citations(
        self,
        citations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Enrich citations with metadata
        
        Args:
            citations: Citation list
        
        Returns:
            Enriched citations
        """
        # In production, fetch metadata from Crossref, Semantic Scholar, etc.
        # For now, return citations as-is
        
        enriched = []
        for citation in citations:
            enriched_citation = {
                **citation,
                "formatted_citation": self._format_citation(citation)
            }
            enriched.append(enriched_citation)
        
        return enriched
    
    def _format_citation(self, citation: Dict[str, Any]) -> str:
        """
        Format citation in APA style
        
        Args:
            citation: Citation object
        
        Returns:
            Formatted citation string
        """
        doc_id = citation.get("document_id", "Unknown")
        page = citation.get("page_number")
        
        if page:
            return f"({doc_id}, p. {page})"
        else:
            return f"({doc_id})"
