"""
Unit tests for Template Service
Requirements: 9.1, 9.2, 9.3, 9.4, 9.5
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from template_service import (
    TemplateService,
    OutlineGenerator,
    TemplateCustomization,
    OutlineSection
)


@pytest.fixture
def template_service():
    """Create template service instance"""
    return TemplateService()


@pytest.fixture
def mock_llm_router():
    """Create mock LLM router"""
    router = Mock()
    router.complete = AsyncMock(return_value={
        'content': '## Introduction\nIntroduction section\n\n### Background\nBackground subsection',
        'model': 'gemini-balanced',
        'input_tokens': 100,
        'output_tokens': 50,
        'cost': 0.001
    })
    return router


@pytest.fixture
def mock_rag_service():
    """Create mock RAG service"""
    service = Mock()
    service.search_service = Mock()
    service.search_service.search = AsyncMock(return_value=[
        {
            'document_id': 'doc1',
            'text': 'Sample research content about transformers',
            'score': 0.9,
            'page_number': 1
        }
    ])
    return service


@pytest.fixture
def outline_generator(mock_llm_router, mock_rag_service):
    """Create outline generator instance"""
    return OutlineGenerator(mock_llm_router, mock_rag_service)


class TestTemplateService:
    """Test template service functionality"""
    
    @pytest.mark.asyncio
    async def test_list_templates_all(self, template_service):
        """Test listing all templates - Requirement 9.1"""
        with patch.object(template_service.db, 'fetch_all', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = [
                {
                    'template_id': 'template1',
                    'name': 'IEEE Article',
                    'template_type': 'article',
                    'is_builtin': True,
                    'usage_count': 10,
                    'customization_options': '{"paper_size": ["letter", "a4"]}',
                    'default_settings': '{"paper_size": "letter"}',
                    'tags': '["ieee", "journal"]'
                }
            ]
            
            templates = await template_service.list_templates()
            
            assert len(templates) == 1
            assert templates[0]['name'] == 'IEEE Article'
            assert templates[0]['is_builtin'] is True
            assert isinstance(templates[0]['customization_options'], dict)
    
    @pytest.mark.asyncio
    async def test_list_templates_by_type(self, template_service):
        """Test filtering templates by type - Requirement 9.1"""
        with patch.object(template_service.db, 'fetch_all', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = []
            
            await template_service.list_templates(template_type='thesis')
            
            # Verify query includes type filter
            call_args = mock_fetch.call_args
            assert 'template_type = %s' in call_args[0][0]
            assert 'thesis' in call_args[0][1]
    
    @pytest.mark.asyncio
    async def test_get_template(self, template_service):
        """Test getting template by ID - Requirement 9.2"""
        with patch.object(template_service.db, 'fetch_one', new_callable=AsyncMock) as mock_fetch, \
             patch.object(template_service.db, 'execute', new_callable=AsyncMock):
            
            mock_fetch.return_value = {
                'template_id': 'template1',
                'name': 'IEEE Article',
                'content': '\\documentclass{IEEEtran}...',
                'customization_options': '{"paper_size": ["letter", "a4"]}',
                'default_settings': '{"paper_size": "letter"}',
                'tags': None
            }
            
            template = await template_service.get_template('template1', 'user1')
            
            assert template is not None
            assert template['name'] == 'IEEE Article'
            assert '\\documentclass' in template['content']
    
    @pytest.mark.asyncio
    async def test_customize_template_paper_size(self, template_service):
        """Test template customization with paper size - Requirement 9.3"""
        with patch.object(template_service, 'get_template', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {
                'template_id': 'template1',
                'content': '\\documentclass[12pt]{article}\n\\begin{document}\nContent\n\\end{document}'
            }
            
            customization = TemplateCustomization(paper_size='a4')
            
            customized = await template_service.customize_template(
                'template1',
                customization,
                'user1'
            )
            
            assert 'a4paper' in customized
    
    @pytest.mark.asyncio
    async def test_customize_template_font_size(self, template_service):
        """Test template customization with font size - Requirement 9.3"""
        with patch.object(template_service, 'get_template', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {
                'template_id': 'template1',
                'content': '\\documentclass[12pt]{article}'
            }
            
            customization = TemplateCustomization(font_size='11pt')
            
            customized = await template_service.customize_template(
                'template1',
                customization,
                'user1'
            )
            
            assert '11pt' in customized
            assert '12pt' not in customized
    
    @pytest.mark.asyncio
    async def test_customize_template_margins(self, template_service):
        """Test template customization with margins - Requirement 9.3"""
        with patch.object(template_service, 'get_template', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {
                'template_id': 'template1',
                'content': '\\documentclass{article}\n\\begin{document}'
            }
            
            customization = TemplateCustomization(margins='1.5in')
            
            customized = await template_service.customize_template(
                'template1',
                customization,
                'user1'
            )
            
            assert 'geometry' in customized
            assert 'margin=1.5in' in customized
    
    @pytest.mark.asyncio
    async def test_save_custom_template(self, template_service):
        """Test saving custom template - Requirement 9.5"""
        with patch.object(template_service.db, 'execute', new_callable=AsyncMock) as mock_execute:
            template_id = await template_service.save_custom_template(
                name='My Custom Template',
                description='Custom template for my research',
                template_type='article',
                content='\\documentclass{article}...',
                user_id='user1',
                project_id='project1',
                is_public=False
            )
            
            assert template_id is not None
            assert len(template_id) == 36  # UUID length
            
            # Verify database insert was called
            mock_execute.assert_called_once()
            call_args = mock_execute.call_args[0]
            assert 'INSERT INTO latex_templates' in call_args[0]
    
    @pytest.mark.asyncio
    async def test_delete_template(self, template_service):
        """Test deleting custom template - Requirement 9.5"""
        with patch.object(template_service.db, 'execute', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = True
            
            success = await template_service.delete_template('template1', 'user1')
            
            assert success is True
            
            # Verify soft delete query
            call_args = mock_execute.call_args[0]
            assert 'UPDATE latex_templates' in call_args[0]
            assert 'deleted_at = NOW()' in call_args[0]


class TestOutlineGenerator:
    """Test outline generator functionality"""
    
    @pytest.mark.asyncio
    async def test_generate_outline_basic(self, outline_generator):
        """Test basic outline generation - Requirement 9.4"""
        with patch.object(outline_generator.db, 'execute', new_callable=AsyncMock):
            outline = await outline_generator.generate_outline(
                research_topic='Transformer architectures for NLP',
                project_id='project1',
                user_id='user1',
                document_type='article'
            )
            
            assert outline is not None
            assert outline.research_topic == 'Transformer architectures for NLP'
            assert len(outline.outline_structure) > 0
            assert outline.latex_content is not None
    
    @pytest.mark.asyncio
    async def test_generate_outline_with_documents(self, outline_generator):
        """Test outline generation with document context - Requirement 9.4"""
        with patch.object(outline_generator.db, 'execute', new_callable=AsyncMock):
            outline = await outline_generator.generate_outline(
                research_topic='Transformer architectures',
                project_id='project1',
                user_id='user1',
                document_ids=['doc1', 'doc2'],
                document_type='article'
            )
            
            assert outline is not None
            assert outline.source_document_ids == ['doc1', 'doc2']
            
            # Verify RAG service was called
            outline_generator.rag_service.search_service.search.assert_called_once()
    
    def test_parse_outline_structure(self, outline_generator):
        """Test parsing outline text into structure - Requirement 9.4"""
        outline_text = """## Introduction
This is the introduction section

### Background
Background information

## Methodology
Research methodology

### Data Collection
How data was collected"""
        
        sections = outline_generator._parse_outline(outline_text)
        
        assert len(sections) == 2
        assert sections[0].title == 'Introduction'
        assert sections[0].level == 1
        assert len(sections[0].subsections) == 1
        assert sections[0].subsections[0].title == 'Background'
        assert sections[1].title == 'Methodology'
    
    def test_generate_latex_structure(self, outline_generator):
        """Test generating LaTeX from outline structure - Requirement 9.4"""
        outline_structure = [
            OutlineSection(
                title='Introduction',
                level=1,
                description='Introduction section',
                subsections=[
                    OutlineSection(
                        title='Background',
                        level=2,
                        description='Background info',
                        subsections=[]
                    )
                ]
            )
        ]
        
        latex = outline_generator._generate_latex_structure(outline_structure, 'article')
        
        assert '\\section{Introduction}' in latex
        assert '\\subsection{Background}' in latex
        assert '% Introduction section' in latex
    
    @pytest.mark.asyncio
    async def test_get_outline(self, outline_generator):
        """Test retrieving saved outline - Requirement 9.4"""
        with patch.object(outline_generator.db, 'fetch_one', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {
                'outline_id': 'outline1',
                'project_id': 'project1',
                'user_id': 'user1',
                'title': 'Test Outline',
                'research_topic': 'Test topic',
                'outline_structure': '[{"title": "Introduction", "level": 1, "description": "", "subsections": []}]',
                'source_document_ids': '["doc1"]',
                'latex_content': '\\section{Introduction}',
                'created_at': '2024-01-01T00:00:00'
            }
            
            outline = await outline_generator.get_outline('outline1', 'user1')
            
            assert outline is not None
            assert outline.outline_id == 'outline1'
            assert len(outline.outline_structure) == 1


class TestTemplateCustomization:
    """Test template customization functions"""
    
    def test_apply_paper_size(self):
        """Test applying paper size customization"""
        service = TemplateService()
        content = '\\documentclass[12pt]{article}'
        
        result = service._apply_paper_size(content, 'a4')
        
        assert 'a4paper' in result
    
    def test_apply_citation_style(self):
        """Test applying citation style customization"""
        service = TemplateService()
        content = '\\bibliographystyle{plain}'
        
        result = service._apply_citation_style(content, 'APA')
        
        assert 'apa' in result
        assert 'plain' not in result
    
    def test_apply_line_spacing(self):
        """Test applying line spacing customization"""
        service = TemplateService()
        content = '\\documentclass{article}\n\\begin{document}'
        
        result = service._apply_line_spacing(content, 'double')
        
        assert 'setspace' in result
        assert 'doublespacing' in result


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
