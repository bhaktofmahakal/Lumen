"""
Unit tests for AI-Assisted LaTeX Writing
Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.8
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from latex_api import AIWritingAssistant, GenerateResponse, BibliographyResponse


@pytest.fixture
def mock_llm_router():
    """Mock LLM router"""
    router = Mock()
    router.complete = AsyncMock(return_value={
        'content': '\\section{Introduction}\n\nThis is generated content \\cite{doc_1}.',
        'model': 'gemini-1.5-flash',
        'tokens': 100
    })
    return router


@pytest.fixture
def mock_memory_router():
    """Mock memory router"""
    router = Mock()
    router.route_query = Mock(return_value=[
        {
            'id': 'mem_1',
            'text': 'Previous research finding',
            'metadata': {'memory_type': 'project_finding'},
            'score': 0.9
        }
    ])
    
    # Mock em (episodic memory) instance
    mock_em = Mock()
    mock_em.get_user_preferences = Mock(return_value=[])  # Return empty list by default
    router.em = mock_em
    
    # Mock ltm (long-term memory) instance
    mock_ltm = Mock()
    mock_ltm.search = Mock(return_value=[])  # Return empty list by default
    mock_ltm.store_project_finding = Mock(return_value='mem_id')
    router.ltm = mock_ltm
    
    # Mock stm (short-term memory) instance
    mock_stm = Mock()
    mock_stm.add = Mock(return_value='mem_id')
    router.stm = mock_stm
    
    return router


@pytest.fixture
def mock_rag_service():
    """Mock RAG service"""
    service = Mock()
    service.query = AsyncMock(return_value={
        'results': [
            {
                'document_id': 'doc_1',
                'page': 3,
                'text': 'Transformers use self-attention mechanism.',
                'score': 0.95
            }
        ]
    })
    return service


@pytest.fixture
def writing_assistant(mock_llm_router, mock_memory_router, mock_rag_service):
    """Create writing assistant instance"""
    return AIWritingAssistant(mock_llm_router, mock_memory_router, mock_rag_service)


class TestAIWritingAssistant:
    """Test AI Writing Assistant functionality"""
    
    @pytest.mark.asyncio
    async def test_generate_section_basic(self, writing_assistant):
        """
        Test basic section generation
        Requirements: 8.1, 8.2
        """
        result = await writing_assistant.generate_content(
            prompt="Write an introduction about transformers",
            user_id="user_1",
            project_id="project_1",
            content_type="section",
            style="formal"
        )
        
        assert isinstance(result, GenerateResponse)
        assert result.success is True
        assert len(result.content) > 0
        assert '\\section' in result.content or '\\subsection' in result.content
        assert result.generation_time >= 0  # Changed from > 0 to >= 0 for fast mock responses
    
    @pytest.mark.asyncio
    async def test_generate_with_citations(self, writing_assistant):
        """
        Test content generation with citations
        Requirements: 8.3
        """
        result = await writing_assistant.generate_content(
            prompt="Write about transformer architecture",
            user_id="user_1",
            project_id="project_1",
            content_type="section",
            document_ids=["doc_1", "doc_2"]
        )
        
        assert result.success is True
        # Check if citations are present
        if result.citations:
            assert len(result.citations) > 0
            assert 'cite_key' in result.citations[0]
            assert 'document_id' in result.citations[0]
    
    @pytest.mark.asyncio
    async def test_generate_with_style(self, writing_assistant):
        """
        Test style customization
        Requirements: 8.4
        """
        styles = ['formal', 'technical', 'concise']
        
        for style in styles:
            result = await writing_assistant.generate_content(
                prompt="Explain attention mechanism",
                user_id="user_1",
                project_id="project_1",
                style=style
            )
            
            assert result.success is True
            assert len(result.content) > 0
    
    @pytest.mark.asyncio
    async def test_generate_equation(self, writing_assistant, mock_llm_router):
        """
        Test equation generation
        Requirements: 8.5
        """
        # Mock equation response
        mock_llm_router.complete.return_value = {
            'content': '\\begin{equation}\nE = mc^2\n\\end{equation}',
            'model': 'gemini-1.5-flash',
            'tokens': 50
        }
        
        result = await writing_assistant.generate_content(
            prompt="Generate Einstein's mass-energy equivalence equation",
            user_id="user_1",
            project_id="project_1",
            content_type="equation"
        )
        
        assert result.success is True
        assert 'equation' in result.content.lower() or '$' in result.content
    
    @pytest.mark.asyncio
    async def test_generate_table(self, writing_assistant, mock_llm_router):
        """
        Test table generation
        Requirements: 8.2
        """
        # Mock table response
        mock_llm_router.complete.return_value = {
            'content': '\\begin{table}\n\\begin{tabular}{ll}\nA & B \\\\\n\\end{tabular}\n\\end{table}',
            'model': 'gemini-1.5-flash',
            'tokens': 80
        }
        
        result = await writing_assistant.generate_content(
            prompt="Create a comparison table",
            user_id="user_1",
            project_id="project_1",
            content_type="table"
        )
        
        assert result.success is True
        assert 'table' in result.content.lower() or 'tabular' in result.content.lower()
    
    @pytest.mark.asyncio
    async def test_iterative_refinement(self, writing_assistant, mock_llm_router):
        """
        Test iterative content refinement
        Requirements: 8.6
        """
        existing_content = "\\section{Introduction}\n\nTransformers are neural networks."
        
        # Mock refined response
        mock_llm_router.complete.return_value = {
            'content': existing_content + '\n\nThey use self-attention mechanism \\cite{doc_1}.',
            'model': 'gemini-1.5-flash',
            'tokens': 120
        }
        
        result = await writing_assistant.generate_content(
            prompt="Add more details about the attention mechanism",
            user_id="user_1",
            project_id="project_1",
            existing_content=existing_content,
            document_ids=["doc_1"]
        )
        
        assert result.success is True
        assert len(result.content) > len(existing_content)
    
    @pytest.mark.asyncio
    async def test_bibliography_generation(self, writing_assistant):
        """
        Test bibliography generation
        Requirements: 8.8
        """
        result = await writing_assistant.generate_bibliography(
            citation_ids=["doc_1", "doc_2"],
            project_id="project_1",
            style="APA"
        )
        
        assert isinstance(result, BibliographyResponse)
        assert result.success is True
        assert len(result.bibtex_entries) == 2
        assert len(result.formatted_bibliography) > 0
    
    @pytest.mark.asyncio
    async def test_bibliography_styles(self, writing_assistant):
        """
        Test different bibliography styles
        Requirements: 8.8
        """
        styles = ['APA', 'MLA', 'Chicago', 'IEEE']
        
        for style in styles:
            result = await writing_assistant.generate_bibliography(
                citation_ids=["doc_1"],
                project_id="project_1",
                style=style
            )
            
            assert result.success is True
            assert len(result.bibtex_entries) > 0
    
    @pytest.mark.asyncio
    async def test_context_gathering(self, writing_assistant, mock_rag_service):
        """
        Test context gathering from documents and memory
        Requirements: 8.1, 8.3
        """
        context = await writing_assistant._gather_context(
            user_id="user_1",
            project_id="project_1",
            session_id="session_1",
            document_ids=["doc_1"],
            prompt="Test prompt"
        )
        
        assert 'memories' in context
        assert 'sources' in context
        assert 'terminology' in context
        
        # Verify RAG service was called
        mock_rag_service.query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_style_preferences_retrieval(self, writing_assistant):
        """
        Test retrieval of user style preferences
        Requirements: 8.4
        """
        # Mock memory router's memory instances
        mock_em = Mock()
        mock_em.get_user_preferences = Mock(return_value=[
            {
                'metadata': {
                    'preference_value': 'technical'
                }
            }
        ])
        
        mock_ltm = Mock()
        mock_ltm.search = Mock(return_value=[])
        
        writing_assistant.memory_router.em = mock_em
        writing_assistant.memory_router.ltm = mock_ltm
        
        style_prefs = await writing_assistant._get_style_preferences(
            user_id="user_1",
            project_id="project_1",
            requested_style="formal"
        )
        
        assert 'style' in style_prefs
        assert style_prefs['style'] == 'technical'  # User preference overrides
    
    @pytest.mark.asyncio
    async def test_citation_extraction(self, writing_assistant):
        """
        Test citation extraction from generated content
        Requirements: 8.3
        """
        content = "Transformers \\cite{doc_1} use attention \\cite{doc_2}."
        sources = [
            {'document_id': 'doc_1', 'page': 3, 'text': 'Source 1'},
            {'document_id': 'doc_2', 'page': 5, 'text': 'Source 2'}
        ]
        
        citations = writing_assistant._extract_citations(content, sources)
        
        assert len(citations) == 2
        assert citations[0]['cite_key'] == 'doc_1'
        assert citations[1]['cite_key'] == 'doc_2'
        assert citations[0]['page'] == '3'  # Page is now a string
        assert citations[1]['page'] == '5'  # Page is now a string
    
    @pytest.mark.asyncio
    async def test_memory_storage(self, writing_assistant):
        """
        Test storing generated content in memory
        Requirements: 8.7
        """
        # Mock memory router's memory instances
        mock_stm = Mock()
        mock_stm.add = Mock(return_value='mem_id_1')
        
        mock_ltm = Mock()
        mock_ltm.store_project_finding = Mock(return_value='mem_id_2')
        
        writing_assistant.memory_router.stm = mock_stm
        writing_assistant.memory_router.ltm = mock_ltm
        
        await writing_assistant._store_in_memory(
            user_id="user_1",
            project_id="project_1",
            session_id="session_1",
            content="Generated content",
            terminology={'term1': 'definition1'}
        )
        
        # Verify memory storage was called
        mock_stm.add.assert_called_once()
        mock_ltm.store_project_finding.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_error_handling(self, writing_assistant, mock_llm_router):
        """
        Test error handling in content generation
        """
        # Mock LLM failure
        mock_llm_router.complete.side_effect = Exception("LLM API error")
        
        with pytest.raises(Exception) as exc_info:
            await writing_assistant.generate_content(
                prompt="Test prompt",
                user_id="user_1",
                project_id="project_1"
            )
        
        assert "Content generation failed" in str(exc_info.value) or "LLM API error" in str(exc_info.value)


class TestContentTypes:
    """Test different content type generation"""
    
    @pytest.mark.asyncio
    async def test_section_formatting(self, writing_assistant, mock_llm_router):
        """Test section has proper LaTeX structure"""
        mock_llm_router.complete.return_value = {
            'content': 'Plain text without LaTeX',
            'model': 'gemini-1.5-flash',
            'tokens': 50
        }
        
        result = await writing_assistant.generate_content(
            prompt="Write a section",
            user_id="user_1",
            project_id="project_1",
            content_type="section"
        )
        
        # Should add LaTeX formatting if not present
        assert '\\' in result.content
    
    @pytest.mark.asyncio
    async def test_paragraph_generation(self, writing_assistant):
        """Test paragraph generation"""
        result = await writing_assistant.generate_content(
            prompt="Write a paragraph about AI",
            user_id="user_1",
            project_id="project_1",
            content_type="paragraph"
        )
        
        assert result.success is True
        assert len(result.content) > 0


class TestStyleInstructions:
    """Test style instruction building"""
    
    def test_formal_style(self, writing_assistant):
        """Test formal style instructions"""
        style_prefs = {'style': 'formal'}
        instructions = writing_assistant._build_style_instructions(style_prefs)
        
        assert 'formal' in instructions.lower()
        assert len(instructions) > 0
    
    def test_technical_style(self, writing_assistant):
        """Test technical style instructions"""
        style_prefs = {'style': 'technical'}
        instructions = writing_assistant._build_style_instructions(style_prefs)
        
        assert 'technical' in instructions.lower()
    
    def test_concise_style(self, writing_assistant):
        """Test concise style instructions"""
        style_prefs = {'style': 'concise'}
        instructions = writing_assistant._build_style_instructions(style_prefs)
        
        assert 'concise' in instructions.lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
