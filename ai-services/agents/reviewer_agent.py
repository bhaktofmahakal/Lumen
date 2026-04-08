"""
Reviewer Agent
Reviews generated content, suggests improvements, ensures quality
Requirements: 38.6
"""

import logging
from typing import Dict, List, Optional, Any
import asyncio

logger = logging.getLogger(__name__)


class ReviewerAgent:
    """
    Reviewer agent for content quality assessment
    Requirements: 38.6
    
    Capabilities:
    - Content quality assessment
    - Clarity and coherence checking
    - Completeness verification
    - Improvement suggestions
    - Citation accuracy validation
    """
    
    def __init__(self, llm_router):
        """
        Initialize reviewer agent
        
        Args:
            llm_router: LLM router for content analysis
        """
        self.llm_router = llm_router
        
        logger.info("Reviewer agent initialized")
    
    async def execute(
        self,
        content: str,
        citations: List[Dict[str, Any]],
        citation_issues: List[Dict[str, Any]],
        research_gaps: List[str]
    ) -> Dict[str, Any]:
        """
        Execute review task
        Requirements: 38.6
        
        Args:
            content: Generated content to review
            citations: Citations in content
            citation_issues: Issues found by citation agent
            research_gaps: Research gaps to verify coverage
        
        Returns:
            Dict with feedback, quality score, and suggestions
        """
        logger.info("Reviewer agent executing...")
        
        try:
            # Analyze content quality
            review_result = await self._analyze_quality(
                content=content,
                citations=citations,
                citation_issues=citation_issues,
                research_gaps=research_gaps
            )
            
            quality_score = review_result.get("quality_score", 0.0)
            
            logger.info(
                f"Reviewer agent completed: quality_score={quality_score:.2f}, "
                f"{len(review_result.get('suggestions', []))} suggestions"
            )
            
            return review_result
            
        except Exception as e:
            logger.error(f"Reviewer agent execution failed: {e}")
            raise
    
    async def _analyze_quality(
        self,
        content: str,
        citations: List[Dict[str, Any]],
        citation_issues: List[Dict[str, Any]],
        research_gaps: List[str]
    ) -> Dict[str, Any]:
        """
        Analyze content quality and generate feedback
        
        Args:
            content: Content to review
            citations: Citations
            citation_issues: Citation issues
            research_gaps: Research gaps
        
        Returns:
            Review result with score and suggestions
        """
        try:
            # Build citation summary
            citation_summary = f"{len(citations)} citations"
            if citation_issues:
                citation_summary += f", {len(citation_issues)} issues"
            
            # Build gaps summary
            gaps_text = "\n".join([f"- {gap}" for gap in research_gaps])
            
            # Generate review using LLM
            prompt = f"""Review the following literature review content for quality and completeness.

Content:
{content}

Citations: {citation_summary}
Citation Issues: {len(citation_issues)}

Research Gaps to Cover:
{gaps_text}

Evaluate the content on:
1. Clarity and coherence (0-1)
2. Completeness (covers all research gaps) (0-1)
3. Citation accuracy (0-1)
4. Academic writing quality (0-1)
5. Structure and organization (0-1)

Provide:
1. Overall quality score (average of above, 0-1)
2. Specific improvement suggestions (if score < 0.8)
3. Brief feedback summary

Format as JSON:
{{
  "quality_score": 0.85,
  "clarity_score": 0.9,
  "completeness_score": 0.8,
  "citation_score": 0.85,
  "writing_score": 0.9,
  "structure_score": 0.8,
  "suggestions": [
    "Add more details on X",
    "Clarify the relationship between Y and Z"
  ],
  "feedback": "Brief summary of review"
}}

Return ONLY the JSON, no additional text."""
            
            response = await self.llm_router.complete(
                query=prompt,
                context={"document_count": len(citations)},
                temperature=0.3,
                max_tokens=1000,
                use_cache=False
            )
            
            # Parse review result
            import json
            try:
                result = json.loads(response['content'])
                
                # Ensure quality_score is present
                if "quality_score" not in result:
                    # Calculate from component scores
                    scores = [
                        result.get("clarity_score", 0.5),
                        result.get("completeness_score", 0.5),
                        result.get("citation_score", 0.5),
                        result.get("writing_score", 0.5),
                        result.get("structure_score", 0.5)
                    ]
                    result["quality_score"] = sum(scores) / len(scores)
                
                # Ensure suggestions is a list
                if "suggestions" not in result:
                    result["suggestions"] = []
                
                # Ensure feedback is present
                if "feedback" not in result:
                    result["feedback"] = "Review completed"
                
                logger.info(f"Quality analysis: score={result['quality_score']:.2f}")
                return result
                
            except json.JSONDecodeError:
                logger.warning("Failed to parse review JSON, returning default")
                return {
                    "quality_score": 0.5,
                    "suggestions": ["Unable to generate detailed review"],
                    "feedback": "Review parsing failed"
                }
            
        except Exception as e:
            logger.error(f"Error analyzing quality: {e}")
            return {
                "quality_score": 0.0,
                "suggestions": [],
                "feedback": f"Review failed: {str(e)}"
            }
