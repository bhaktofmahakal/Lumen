"""
Agent Orchestration with LangGraph
Multi-agent workflow for autonomous research assistance
Requirements: 38.1, 38.7, 38.8, 38.12, 4.12
"""

import logging
import time
from typing import Dict, List, Optional, Any, TypedDict
from datetime import datetime
import asyncio

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

logger = logging.getLogger(__name__)


class ResearchWorkflowState(TypedDict):
    """
    State schema for research workflow
    Requirements: 38.1, 38.7
    """
    # Input
    query: str
    project_id: str
    user_id: str
    document_ids: List[str]
    
    # Research phase
    research_findings: List[Dict[str, Any]]
    research_gaps: List[str]
    
    # Writing phase
    draft_content: str
    
    # Citation phase
    citations: List[Dict[str, Any]]
    citation_issues: List[Dict[str, Any]]
    
    # Review phase
    review_feedback: str
    quality_score: float
    improvement_suggestions: List[str]
    
    # Final output
    final_output: str
    
    # Iteration tracking
    iteration_count: int
    max_iterations: int
    
    # Error tracking
    errors: List[Dict[str, Any]]
    
    # Metadata
    started_at: str
    completed_at: Optional[str]
    workflow_id: str


class AgentOrchestrator:
    """
    LangGraph-based agent orchestrator
    Requirements: 38.1, 38.7, 38.8, 38.12
    """
    
    def __init__(
        self,
        researcher_agent,
        writer_agent,
        citation_agent,
        reviewer_agent,
        checkpointer: Optional[MemorySaver] = None
    ):
        """
        Initialize agent orchestrator
        
        Args:
            researcher_agent: Researcher agent instance
            writer_agent: Writer agent instance
            citation_agent: Citation agent instance
            reviewer_agent: Reviewer agent instance
            checkpointer: Optional checkpointer for state persistence
        """
        self.researcher_agent = researcher_agent
        self.writer_agent = writer_agent
        self.citation_agent = citation_agent
        self.reviewer_agent = reviewer_agent
        self.checkpointer = checkpointer or MemorySaver()
        
        # Build workflow graph
        self.workflow = self._build_workflow()
        self.app = self.workflow.compile(checkpointer=self.checkpointer)
        
        logger.info("Agent orchestrator initialized with LangGraph")
    
    def _build_workflow(self) -> StateGraph:
        """
        Build LangGraph workflow
        Requirements: 38.1, 38.7
        
        Returns:
            StateGraph workflow
        """
        # Create state graph
        workflow = StateGraph(ResearchWorkflowState)
        
        # Add nodes for each agent
        workflow.add_node("researcher", self._researcher_node)
        workflow.add_node("writer", self._writer_node)
        workflow.add_node("citation", self._citation_node)
        workflow.add_node("reviewer", self._reviewer_node)
        
        # Define edges (workflow transitions)
        workflow.add_edge("researcher", "writer")
        workflow.add_edge("writer", "citation")
        workflow.add_edge("citation", "reviewer")
        
        # Conditional edge for iteration
        workflow.add_conditional_edges(
            "reviewer",
            self._should_continue,
            {
                "continue": "writer",  # Iterate if improvements needed
                "end": END  # Complete if quality threshold met
            }
        )
        
        # Set entry point
        workflow.set_entry_point("researcher")
        
        return workflow
    
    async def _researcher_node(self, state: ResearchWorkflowState) -> Dict[str, Any]:
        """
        Researcher agent node with error recovery
        Requirements: 38.2, 38.8, 4.12
        """
        logger.info(f"Executing researcher agent for query: {state['query'][:50]}...")
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Execute researcher agent
                result = await self.researcher_agent.execute(
                    query=state["query"],
                    project_id=state["project_id"],
                    document_ids=state["document_ids"]
                )
                
                logger.info(
                    f"Researcher agent completed: "
                    f"{len(result.get('findings', []))} findings, "
                    f"{len(result.get('gaps', []))} gaps"
                )
                
                return {
                    "research_findings": result.get("findings", []),
                    "research_gaps": result.get("gaps", [])
                }
                
            except Exception as e:
                logger.error(f"Researcher agent error (attempt {attempt + 1}/{max_retries}): {e}")
                
                if attempt == max_retries - 1:
                    # Final failure - return partial results
                    return {
                        "research_findings": [],
                        "research_gaps": [],
                        "errors": state.get("errors", []) + [{
                            "agent": "researcher",
                            "error": str(e),
                            "timestamp": datetime.now().isoformat()
                        }]
                    }
                
                # Exponential backoff
                await asyncio.sleep(2 ** attempt)
        
        return {}
        return {}
    
    async def _writer_node(self, state: ResearchWorkflowState) -> Dict[str, Any]:
        """
        Writer agent node with error recovery
        Requirements: 38.4, 38.8, 4.12
        """
        logger.info("Executing writer agent...")
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Execute writer agent
                result = await self.writer_agent.execute(
                    query=state["query"],
                    research_findings=state["research_findings"],
                    research_gaps=state["research_gaps"],
                    review_feedback=state.get("review_feedback", ""),
                    iteration_count=state.get("iteration_count", 0)
                )
                
                logger.info(f"Writer agent completed: {len(result.get('content', ''))} chars")
                
                return {
                    "draft_content": result.get("content", "")
                }
                
            except Exception as e:
                logger.error(f"Writer agent error (attempt {attempt + 1}/{max_retries}): {e}")
                
                if attempt == max_retries - 1:
                    return {
                        "draft_content": "",
                        "errors": state.get("errors", []) + [{
                            "agent": "writer",
                            "error": str(e),
                            "timestamp": datetime.now().isoformat()
                        }]
                    }
                
                await asyncio.sleep(2 ** attempt)
        
        return {}
    
    async def _citation_node(self, state: ResearchWorkflowState) -> Dict[str, Any]:
        """
        Citation agent node with error recovery
        Requirements: 38.5, 38.8, 4.12
        """
        logger.info("Executing citation agent...")
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Execute citation agent
                result = await self.citation_agent.execute(
                    content=state["draft_content"],
                    research_findings=state["research_findings"]
                )
                
                logger.info(
                    f"Citation agent completed: "
                    f"{len(result.get('citations', []))} citations, "
                    f"{len(result.get('issues', []))} issues"
                )
                
                return {
                    "citations": result.get("citations", []),
                    "citation_issues": result.get("issues", [])
                }
                
            except Exception as e:
                logger.error(f"Citation agent error (attempt {attempt + 1}/{max_retries}): {e}")
                
                if attempt == max_retries - 1:
                    return {
                        "citations": [],
                        "citation_issues": [],
                        "errors": state.get("errors", []) + [{
                            "agent": "citation",
                            "error": str(e),
                            "timestamp": datetime.now().isoformat()
                        }]
                    }
                
                await asyncio.sleep(2 ** attempt)
        
        return {}
    
    async def _reviewer_node(self, state: ResearchWorkflowState) -> Dict[str, Any]:
        """
        Reviewer agent node with error recovery
        Requirements: 38.6, 38.8, 4.12
        """
        logger.info("Executing reviewer agent...")
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Execute reviewer agent
                result = await self.reviewer_agent.execute(
                    content=state["draft_content"],
                    citations=state["citations"],
                    citation_issues=state["citation_issues"],
                    research_gaps=state["research_gaps"]
                )
                
                quality_score = result.get("quality_score", 0.0)
                
                logger.info(
                    f"Reviewer agent completed: quality_score={quality_score:.2f}, "
                    f"{len(result.get('suggestions', []))} suggestions"
                )
                
                # Increment iteration count
                iteration_count = state.get("iteration_count", 0) + 1
                
                return {
                    "review_feedback": result.get("feedback", ""),
                    "quality_score": quality_score,
                    "improvement_suggestions": result.get("suggestions", []),
                    "iteration_count": iteration_count
                }
                
            except Exception as e:
                logger.error(f"Reviewer agent error (attempt {attempt + 1}/{max_retries}): {e}")
                
                if attempt == max_retries - 1:
                    return {
                        "review_feedback": "",
                        "quality_score": 0.0,
                        "improvement_suggestions": [],
                        "iteration_count": state.get("iteration_count", 0) + 1,
                        "errors": state.get("errors", []) + [{
                            "agent": "reviewer",
                            "error": str(e),
                            "timestamp": datetime.now().isoformat()
                        }]
                    }
                
                await asyncio.sleep(2 ** attempt)
        
        return {}
    
    def _should_continue(self, state: ResearchWorkflowState) -> str:
        """
        Determine if workflow should continue iterating
        Requirements: 38.12
        
        Loop prevention:
        - Max 3 iterations
        - Quality threshold 0.8
        
        Args:
            state: Current workflow state
        
        Returns:
            "continue" or "end"
        """
        iteration_count = state.get("iteration_count", 0)
        max_iterations = state.get("max_iterations", 3)
        quality_score = state.get("quality_score", 0.0)
        quality_threshold = 0.8
        
        # Check quality threshold FIRST (higher priority)
        if quality_score >= quality_threshold:
            logger.info(f"Quality threshold ({quality_threshold}) met (score: {quality_score:.2f}), ending workflow")
            return "end"
        
        # Prevent infinite loops - max iterations
        if iteration_count >= max_iterations:
            logger.info(f"Max iterations ({max_iterations}) reached, ending workflow")
            return "end"
        
        # Continue iteration
        logger.info(
            f"Quality score ({quality_score:.2f}) below threshold ({quality_threshold}), "
            f"continuing iteration {iteration_count}/{max_iterations}"
        )
        return "continue"
    
    async def execute_workflow(
        self,
        query: str,
        project_id: str,
        user_id: str,
        document_ids: List[str],
        workflow_id: str,
        max_iterations: int = 3
    ) -> Dict[str, Any]:
        """
        Execute research workflow
        Requirements: 38.1, 38.7, 38.8, 38.12
        
        Args:
            query: Research query
            project_id: Project identifier
            user_id: User identifier
            document_ids: List of document IDs to search
            workflow_id: Unique workflow identifier
            max_iterations: Maximum iterations (default: 3)
        
        Returns:
            Workflow result with final output and metadata
        """
        logger.info(f"Starting workflow {workflow_id} for query: {query[:50]}...")
        
        # Initialize state
        initial_state: ResearchWorkflowState = {
            "query": query,
            "project_id": project_id,
            "user_id": user_id,
            "document_ids": document_ids,
            "research_findings": [],
            "research_gaps": [],
            "draft_content": "",
            "citations": [],
            "citation_issues": [],
            "review_feedback": "",
            "quality_score": 0.0,
            "improvement_suggestions": [],
            "final_output": "",
            "iteration_count": 0,
            "max_iterations": max_iterations,
            "errors": [],
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "workflow_id": workflow_id
        }
        
        # Execute workflow with checkpointing
        config = {
            "configurable": {"thread_id": workflow_id},
            "recursion_limit": max(max_iterations * 10, 50)  # Set recursion limit based on max_iterations
        }
        
        try:
            result = await asyncio.to_thread(
                self.app.invoke,
                initial_state,
                config=config
            )
            
            # Mark as completed
            result["completed_at"] = datetime.now().isoformat()
            
            # Set final output
            result["final_output"] = result.get("draft_content", "")
            
            logger.info(
                f"Workflow {workflow_id} completed: "
                f"iterations={result.get('iteration_count', 0)}, "
                f"quality={result.get('quality_score', 0.0):.2f}, "
                f"errors={len(result.get('errors', []))}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Workflow {workflow_id} failed: {e}")
            raise
    
    async def resume_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        Resume workflow from checkpoint
        Requirements: 38.7
        
        Args:
            workflow_id: Workflow identifier
        
        Returns:
            Workflow result
        """
        logger.info(f"Resuming workflow {workflow_id} from checkpoint...")
        
        config = {"configurable": {"thread_id": workflow_id}}
        
        try:
            result = await asyncio.to_thread(
                self.app.invoke,
                None,  # Resume from checkpoint
                config=config
            )
            
            result["completed_at"] = datetime.now().isoformat()
            result["final_output"] = result.get("draft_content", "")
            
            logger.info(f"Workflow {workflow_id} resumed and completed")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to resume workflow {workflow_id}: {e}")
            raise
    
    def get_workflow_state(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current workflow state from checkpoint
        Requirements: 38.7
        
        Args:
            workflow_id: Workflow identifier
        
        Returns:
            Current state or None if not found
        """
        try:
            config = {"configurable": {"thread_id": workflow_id}}
            # LangGraph 0.0.20 doesn't have get_state, so we'll return None
            # In production, upgrade to newer version with get_state support
            logger.warning("get_state not available in LangGraph 0.0.20")
            return None
        except Exception as e:
            logger.error(f"Failed to get workflow state: {e}")
            return None
