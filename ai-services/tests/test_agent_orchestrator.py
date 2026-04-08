"""
Unit tests for agent orchestrator
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from agent_orchestrator import AgentOrchestrator, ResearchWorkflowState
from agents.researcher_agent import ResearcherAgent
from agents.writer_agent import WriterAgent
from agents.citation_agent import CitationAgent
from agents.reviewer_agent import ReviewerAgent


@pytest.fixture
def mock_rag_service():
    """Mock RAG service"""
    mock = Mock()
    mock.search_service = Mock()
    mock.search_service.search = AsyncMock(return_value=[
        {
            "document_id": "doc_1",
            "chunk_id": 1,
            "text": "Transformers use self-attention mechanism",
            "score": 0.9,
            "page_number": 3
        }
    ])
    return mock


@pytest.fixture
def mock_llm_router():
    """Mock LLM router"""
    mock = Mock()
    mock.complete = AsyncMock(return_value={
        "content": '["Finding 1", "Finding 2"]',
        "model": "gemini-balanced",
        "input_tokens": 100,
        "output_tokens": 50,
        "cost": 0.001
    })
    return mock


@pytest.fixture
def mock_memory_service():
    """Mock memory service"""
    return Mock()


@pytest.fixture
def researcher_agent(mock_rag_service, mock_llm_router):
    """Create researcher agent"""
    return ResearcherAgent(mock_rag_service, mock_llm_router)


@pytest.fixture
def writer_agent(mock_llm_router, mock_memory_service):
    """Create writer agent"""
    return WriterAgent(mock_llm_router, mock_memory_service)


@pytest.fixture
def citation_agent(mock_rag_service, mock_llm_router):
    """Create citation agent"""
    return CitationAgent(mock_rag_service, mock_llm_router)


@pytest.fixture
def reviewer_agent(mock_llm_router):
    """Create reviewer agent"""
    return ReviewerAgent(mock_llm_router)


@pytest.fixture
def orchestrator(researcher_agent, writer_agent, citation_agent, reviewer_agent):
    """Create agent orchestrator"""
    return AgentOrchestrator(
        researcher_agent=researcher_agent,
        writer_agent=writer_agent,
        citation_agent=citation_agent,
        reviewer_agent=reviewer_agent
    )


class TestResearcherAgent:
    """Test researcher agent"""
    
    @pytest.mark.asyncio
    async def test_execute_success(self, researcher_agent, mock_llm_router):
        """Test successful execution"""
        # Mock LLM responses
        mock_llm_router.complete = AsyncMock(side_effect=[
            # Findings extraction
            {
                "content": '[{"finding": "Test finding", "source_passage": 1, "relevance": "Relevant"}]',
                "model": "gemini-balanced",
                "input_tokens": 100,
                "output_tokens": 50,
                "cost": 0.001
            },
            # Gaps identification
            {
                "content": '["Gap 1", "Gap 2"]',
                "model": "gemini-balanced",
                "input_tokens": 100,
                "output_tokens": 50,
                "cost": 0.001
            }
        ])
        
        result = await researcher_agent.execute(
            query="What are transformers?",
            project_id="project_1",
            document_ids=["doc_1"]
        )
        
        assert "findings" in result
        assert "gaps" in result
        assert len(result["findings"]) > 0
        assert len(result["gaps"]) > 0


class TestWriterAgent:
    """Test writer agent"""
    
    @pytest.mark.asyncio
    async def test_execute_success(self, writer_agent, mock_llm_router):
        """Test successful execution"""
        mock_llm_router.complete = AsyncMock(return_value={
            "content": "\\section{Literature Review}\n\nTest content",
            "model": "gemini-balanced",
            "input_tokens": 100,
            "output_tokens": 200,
            "cost": 0.002
        })
        
        result = await writer_agent.execute(
            query="Write about transformers",
            research_findings=[{"finding": "Test finding"}],
            research_gaps=["Gap 1"]
        )
        
        assert "content" in result
        assert len(result["content"]) > 0
        assert "\\section" in result["content"]


class TestCitationAgent:
    """Test citation agent"""
    
    @pytest.mark.asyncio
    async def test_extract_citations(self, citation_agent):
        """Test citation extraction"""
        content = "Transformers use attention \\cite{doc_1}. They are effective \\cite{doc_2}."
        findings = [
            {"document_id": "doc_1", "page_number": 3, "finding": "Attention mechanism"},
            {"document_id": "doc_2", "page_number": 5, "finding": "Effectiveness"}
        ]
        
        result = await citation_agent.execute(content, findings)
        
        assert "citations" in result
        assert len(result["citations"]) == 2
        assert result["citations"][0]["cite_key"] == "doc_1"


class TestReviewerAgent:
    """Test reviewer agent"""
    
    @pytest.mark.asyncio
    async def test_execute_success(self, reviewer_agent, mock_llm_router):
        """Test successful execution"""
        mock_llm_router.complete = AsyncMock(return_value={
            "content": '{"quality_score": 0.85, "suggestions": ["Improve X"], "feedback": "Good work"}',
            "model": "gemini-balanced",
            "input_tokens": 100,
            "output_tokens": 100,
            "cost": 0.001
        })
        
        result = await reviewer_agent.execute(
            content="Test content",
            citations=[],
            citation_issues=[],
            research_gaps=[]
        )
        
        assert "quality_score" in result
        assert "suggestions" in result
        assert "feedback" in result
        assert 0.0 <= result["quality_score"] <= 1.0


class TestAgentOrchestrator:
    """Test agent orchestrator"""
    
    @pytest.mark.asyncio
    async def test_workflow_execution(self, orchestrator, mock_llm_router):
        """Test complete workflow execution"""
        # Mock all LLM responses
        mock_llm_router.complete = AsyncMock(side_effect=[
            # Researcher: findings
            {"content": '[{"finding": "Test", "source_passage": 1, "relevance": "Relevant"}]', "model": "gemini", "input_tokens": 100, "output_tokens": 50, "cost": 0.001},
            # Researcher: gaps
            {"content": '["Gap 1"]', "model": "gemini", "input_tokens": 100, "output_tokens": 50, "cost": 0.001},
            # Writer: content
            {"content": "\\section{Test}\n\nContent", "model": "gemini", "input_tokens": 100, "output_tokens": 200, "cost": 0.002},
            # Reviewer: quality
            {"content": '{"quality_score": 0.85, "suggestions": [], "feedback": "Good"}', "model": "gemini", "input_tokens": 100, "output_tokens": 100, "cost": 0.001}
        ])
        
        result = await orchestrator.execute_workflow(
            query="Test query",
            project_id="project_1",
            user_id="user_1",
            document_ids=["doc_1"],
            workflow_id="workflow_1"
        )
        
        assert result["workflow_id"] == "workflow_1"
        assert result["completed_at"] is not None
        assert "final_output" in result
        assert result["quality_score"] >= 0.8  # Should meet threshold
    
    @pytest.mark.asyncio
    async def test_workflow_iteration(self, orchestrator, mock_llm_router):
        """Test workflow iteration when quality is low"""
        # Mock responses with low quality first, then high quality
        mock_llm_router.complete = AsyncMock(side_effect=[
            # Iteration 1: Researcher findings
            {"content": '[{"finding": "Test", "source_passage": 1, "relevance": "Relevant"}]', "model": "gemini", "input_tokens": 100, "output_tokens": 50, "cost": 0.001},
            # Iteration 1: Researcher gaps
            {"content": '["Gap 1"]', "model": "gemini", "input_tokens": 100, "output_tokens": 50, "cost": 0.001},
            # Iteration 1: Writer
            {"content": "\\section{Test}\n\nContent", "model": "gemini", "input_tokens": 100, "output_tokens": 200, "cost": 0.002},
            # Iteration 1: Reviewer (low quality)
            {"content": '{"quality_score": 0.6, "suggestions": ["Improve X"], "feedback": "Needs work"}', "model": "gemini", "input_tokens": 100, "output_tokens": 100, "cost": 0.001},
            # Iteration 2: Writer (revision)
            {"content": "\\section{Test}\n\nImproved content", "model": "gemini", "input_tokens": 100, "output_tokens": 200, "cost": 0.002},
            # Iteration 2: Reviewer (high quality)
            {"content": '{"quality_score": 0.85, "suggestions": [], "feedback": "Good"}', "model": "gemini", "input_tokens": 100, "output_tokens": 100, "cost": 0.001}
        ])
        
        result = await orchestrator.execute_workflow(
            query="Test query",
            project_id="project_1",
            user_id="user_1",
            document_ids=["doc_1"],
            workflow_id="workflow_2"
        )
        
        assert result["iteration_count"] == 2  # Should iterate once
        assert result["quality_score"] >= 0.8
    
    def test_should_continue_max_iterations(self, orchestrator):
        """Test loop prevention - max iterations"""
        state: ResearchWorkflowState = {
            "query": "test",
            "project_id": "p1",
            "user_id": "u1",
            "document_ids": [],
            "research_findings": [],
            "research_gaps": [],
            "draft_content": "",
            "citations": [],
            "citation_issues": [],
            "review_feedback": "",
            "quality_score": 0.5,
            "improvement_suggestions": [],
            "final_output": "",
            "iteration_count": 3,
            "max_iterations": 3,
            "errors": [],
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "workflow_id": "w1"
        }
        
        result = orchestrator._should_continue(state)
        assert result == "end"  # Should stop at max iterations
    
    def test_should_continue_quality_threshold(self, orchestrator):
        """Test loop prevention - quality threshold"""
        state: ResearchWorkflowState = {
            "query": "test",
            "project_id": "p1",
            "user_id": "u1",
            "document_ids": [],
            "research_findings": [],
            "research_gaps": [],
            "draft_content": "",
            "citations": [],
            "citation_issues": [],
            "review_feedback": "",
            "quality_score": 0.85,
            "improvement_suggestions": [],
            "final_output": "",
            "iteration_count": 1,
            "max_iterations": 3,
            "errors": [],
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "workflow_id": "w1"
        }
        
        result = orchestrator._should_continue(state)
        assert result == "end"  # Should stop when quality threshold met
