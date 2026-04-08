"""
Researcher Agent
Conducts literature reviews, searches documents, extracts key findings
Requirements: 38.2
"""

import logging
from typing import Dict, List, Optional, Any
import asyncio

logger = logging.getLogger(__name__)


class ResearcherAgent:
    """
    Researcher agent for literature review and document analysis
    Requirements: 38.2
    
    Capabilities:
    - Semantic search across multiple documents
    - Key finding extraction and summarization
    - Research gap identification
    - Comparative analysis across papers
    """
    
    def __init__(self, rag_service, llm_router):
        """
        Initialize researcher agent
        
        Args:
            rag_service: RAG service for document retrieval
            llm_router: LLM router for response generation
        """
        self.rag_service = rag_service
        self.llm_router = llm_router
        
        logger.info("Researcher agent initialized")
    
    async def execute(
        self,
        query: str,
        project_id: str,
        document_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Execute research task
        Requirements: 38.2
        
        Args:
            query: Research query
            project_id: Project identifier
            document_ids: List of document IDs to search
        
        Returns:
            Dict with findings and research gaps
        """
        logger.info(f"Researcher agent executing for query: {query[:50]}...")
        
        try:
            # Step 1: Semantic search across documents
            search_results = await self.rag_service.search_service.search(
                query=query,
                project_id=project_id,
                document_ids=document_ids,
                limit=20,
                score_threshold=0.3
            )
            
            logger.info(f"Found {len(search_results)} relevant passages")
            
            # Step 2: Extract key findings
            findings = await self._extract_key_findings(query, search_results)
            
            # Step 3: Identify research gaps
            gaps = await self._identify_research_gaps(query, findings)
            
            logger.info(
                f"Researcher agent completed: "
                f"{len(findings)} findings, {len(gaps)} gaps"
            )
            
            return {
                "findings": findings,
                "gaps": gaps,
                "search_results": search_results
            }
            
        except Exception as e:
            logger.error(f"Researcher agent execution failed: {e}")
            raise
    
    async def _extract_key_findings(
        self,
        query: str,
        search_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Extract key findings from search results
        
        Args:
            query: Research query
            search_results: Search results from RAG
        
        Returns:
            List of key findings with metadata
        """
        if not search_results:
            return []
        
        try:
            # Build context from search results
            context_parts = []
            for i, result in enumerate(search_results[:10]):
                context_parts.append(
                    f"[Passage {i+1}] (Document: {result.get('document_id', 'unknown')}, "
                    f"Page: {result.get('page_number', 'N/A')}, Score: {result.get('score', 0):.2f})\n"
                    f"{result['text']}\n"
                )
            
            context = "\n".join(context_parts)
            
            # Generate findings using LLM
            prompt = f"""Based on the following passages from research papers, extract the key findings related to the query.

Query: {query}

Passages:
{context}

Extract 3-5 key findings. For each finding:
1. State the finding clearly
2. Cite the source passage number
3. Explain its relevance to the query

Format as JSON array:
[
  {{
    "finding": "Clear statement of the finding",
    "source_passage": 1,
    "document_id": "doc_id",
    "page_number": 5,
    "relevance": "Why this is relevant to the query"
  }}
]

Return ONLY the JSON array, no additional text."""
            
            response = await self.llm_router.complete(
                query=prompt,
                context={"document_count": len(search_results)},
                temperature=0.3,
                max_tokens=1000,
                use_cache=False
            )
            
            # Parse findings from response
            import json
            try:
                findings = json.loads(response['content'])
                
                # Enrich with metadata from search results
                for finding in findings:
                    passage_idx = finding.get("source_passage", 1) - 1
                    if 0 <= passage_idx < len(search_results):
                        result = search_results[passage_idx]
                        finding["document_id"] = result.get("document_id")
                        finding["page_number"] = result.get("page_number")
                        finding["score"] = result.get("score")
                
                logger.info(f"Extracted {len(findings)} key findings")
                return findings
                
            except json.JSONDecodeError:
                logger.warning("Failed to parse findings JSON, returning empty list")
                return []
            
        except Exception as e:
            logger.error(f"Error extracting key findings: {e}")
            return []
    
    async def _identify_research_gaps(
        self,
        query: str,
        findings: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Identify research gaps based on findings
        
        Args:
            query: Research query
            findings: Extracted key findings
        
        Returns:
            List of research gaps
        """
        if not findings:
            return []
        
        try:
            # Build findings summary
            findings_text = "\n".join([
                f"- {f.get('finding', '')}"
                for f in findings
            ])
            
            # Generate research gaps using LLM
            prompt = f"""Based on the following research query and key findings, identify 2-3 research gaps or areas that need further investigation.

Query: {query}

Key Findings:
{findings_text}

Identify research gaps - areas that are:
1. Not well covered in the current findings
2. Mentioned but need more investigation
3. Logical next steps for research

Format as JSON array of strings:
["Gap 1", "Gap 2", "Gap 3"]

Return ONLY the JSON array, no additional text."""
            
            response = await self.llm_router.complete(
                query=prompt,
                context={"document_count": len(findings)},
                temperature=0.5,
                max_tokens=500,
                use_cache=False
            )
            
            # Parse gaps from response
            import json
            try:
                gaps = json.loads(response['content'])
                logger.info(f"Identified {len(gaps)} research gaps")
                return gaps
            except json.JSONDecodeError:
                logger.warning("Failed to parse gaps JSON, returning empty list")
                return []
            
        except Exception as e:
            logger.error(f"Error identifying research gaps: {e}")
            return []
