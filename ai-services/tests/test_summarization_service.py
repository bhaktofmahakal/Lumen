"""
Unit tests for document summarization and data extraction services
Requirements: 5.1, 5.2, 5.3, 5.7, 6.1, 6.2, 6.3, 6.5
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from summarization_service import (
    SummarizationService,
    ComparativeSummarizationService,
    DataExtractionService,
    DataExportService,
    SummaryLength,
    DocumentSummary,
    ComparativeSummary,
    ExtractedData
)


@pytest.fixture
def mock_llm_router():
    """Mock LLM router"""
    router = Mock()
    router.complete = AsyncMock()
    return router


@pytest.fixture
def mock_vector_store():
    """Mock vector store"""
    store = Mock()
    store.search = Mock()
    return store


@pytest.fixture
def mock_embedding_generator():
    """Mock embedding generator"""
    generator = Mock()
    generator.generate_embedding = Mock(return_value=[0.1] * 384)
    return generator


@pytest.fixture
def summarization_service(mock_llm_router, mock_vector_store, mock_embedding_generator):
    """Create summarization service with mocks"""
    return SummarizationService(
        llm_router=mock_llm_router,
        vector_store=mock_vector_store,
        embedding_generator=mock_embedding_generator
    )


@pytest.fixture
def comparative_service(mock_llm_router, summarization_service):
    """Create comparative summarization service"""
    return ComparativeSummarizationService(
        llm_router=mock_llm_router,
        summarization_service=summarization_service
    )


@pytest.fixture
def data_extraction_service(mock_llm_router, mock_vector_store):
    """Create data extraction service"""
    return DataExtractionService(
        llm_router=mock_llm_router,
        vector_store=mock_vector_store
    )


class TestSummarizationService:
    """Test document summarization service"""
    
    @pytest.mark.asyncio
    async def test_extract_sections(self, summarization_service, mock_vector_store, mock_llm_router):
        """Test extracting key sections from document"""
        # Mock vector store to return chunks
        mock_chunks = [
            {
                'document_id': 'doc1',
                'chunk_id': 0,
                'text': 'Abstract: This paper presents...',
                'score': 0.9
            },
            {
                'document_id': 'doc1',
                'chunk_id': 1,
                'text': 'Introduction: Machine learning has...',
                'score': 0.85
            }
        ]
        mock_vector_store.search.return_value = mock_chunks
        
        # Mock LLM response
        mock_llm_router.complete.return_value = {
            'content': '''
            {
                "abstract": "This paper presents a novel approach",
                "introduction": "Machine learning has revolutionized",
                "methods": "We used deep learning techniques",
                "results": "Our model achieved 95% accuracy",
                "conclusion": "We demonstrated significant improvements"
            }
            ''',
            'model': 'gemini-1.5-flash',
            'input_tokens': 100,
            'output_tokens': 50,
            'cost': 0.001
        }
        
        # Extract sections
        sections = await summarization_service.extract_sections(
            document_id='doc1',
            project_id='proj1'
        )
        
        # Verify
        assert len(sections) == 5
        assert 'abstract' in sections
        assert 'introduction' in sections
        assert sections['abstract'].section_name == 'Abstract'
        assert 'novel approach' in sections['abstract'].content
    
    @pytest.mark.asyncio
    async def test_generate_summary_brief(self, summarization_service, mock_vector_store, mock_llm_router):
        """Test generating brief summary"""
        # Mock extract_sections
        with patch.object(summarization_service, 'extract_sections') as mock_extract:
            from summarization_service import DocumentSection
            
            mock_extract.return_value = {
                'abstract': DocumentSection(
                    section_name='Abstract',
                    content='This paper presents a novel approach to machine learning.'
                ),
                'introduction': DocumentSection(
                    section_name='Introduction',
                    content='Machine learning has revolutionized many fields.'
                )
            }
            
            # Mock LLM response
            mock_llm_router.complete.return_value = {
                'content': '''
                {
                    "abstract": "Novel ML approach presented",
                    "introduction": "ML revolutionizes fields",
                    "methods": null,
                    "results": null,
                    "conclusion": null,
                    "key_findings": [
                        "Novel approach to ML",
                        "Significant improvements",
                        "Practical applications"
                    ]
                }
                ''',
                'model': 'gemini-1.5-flash',
                'input_tokens': 100,
                'output_tokens': 50,
                'cost': 0.001
            }
            
            # Generate summary
            summary = await summarization_service.generate_summary(
                document_id='doc1',
                project_id='proj1',
                length=SummaryLength.BRIEF,
                document_title='Test Paper'
            )
            
            # Verify
            assert summary.document_id == 'doc1'
            assert summary.document_title == 'Test Paper'
            assert summary.summary_length == SummaryLength.BRIEF
            assert summary.abstract is not None
            assert len(summary.key_findings) == 3
            assert 'Novel approach' in summary.key_findings[0]
    
    @pytest.mark.asyncio
    async def test_generate_summary_standard(self, summarization_service, mock_vector_store, mock_llm_router):
        """Test generating standard summary"""
        # Mock extract_sections
        with patch.object(summarization_service, 'extract_sections') as mock_extract:
            from summarization_service import DocumentSection
            
            mock_extract.return_value = {
                'abstract': DocumentSection(section_name='Abstract', content='Abstract content'),
                'introduction': DocumentSection(section_name='Introduction', content='Intro content'),
                'methods': DocumentSection(section_name='Methods', content='Methods content'),
                'results': DocumentSection(section_name='Results', content='Results content'),
                'conclusion': DocumentSection(section_name='Conclusion', content='Conclusion content')
            }
            
            # Mock LLM response
            mock_llm_router.complete.return_value = {
                'content': '''
                {
                    "abstract": "Standard abstract summary",
                    "introduction": "Standard intro summary",
                    "methods": "Standard methods summary",
                    "results": "Standard results summary",
                    "conclusion": "Standard conclusion summary",
                    "key_findings": ["Finding 1", "Finding 2", "Finding 3", "Finding 4", "Finding 5"]
                }
                ''',
                'model': 'gemini-1.5-flash',
                'input_tokens': 200,
                'output_tokens': 100,
                'cost': 0.002
            }
            
            # Generate summary
            summary = await summarization_service.generate_summary(
                document_id='doc1',
                length=SummaryLength.STANDARD
            )
            
            # Verify
            assert summary.summary_length == SummaryLength.STANDARD
            assert summary.abstract is not None
            assert summary.methods is not None
            assert summary.results is not None
            assert len(summary.key_findings) == 5


class TestComparativeSummarizationService:
    """Test comparative summarization service"""
    
    @pytest.mark.asyncio
    async def test_generate_comparative_summary(self, comparative_service, mock_llm_router):
        """Test generating comparative summary for multiple documents"""
        # Mock individual summaries
        with patch.object(comparative_service.summarization_service, 'generate_summary') as mock_summarize:
            mock_summarize.side_effect = [
                DocumentSummary(
                    document_id='doc1',
                    document_title='Paper 1',
                    summary_length=SummaryLength.STANDARD,
                    key_findings=['Finding A', 'Finding B'],
                    methods='Method X',
                    results='Result Y',
                    conclusion='Conclusion Z',
                    generated_at=datetime.utcnow().isoformat()
                ),
                DocumentSummary(
                    document_id='doc2',
                    document_title='Paper 2',
                    summary_length=SummaryLength.STANDARD,
                    key_findings=['Finding C', 'Finding D'],
                    methods='Method X',
                    results='Result W',
                    conclusion='Conclusion V',
                    generated_at=datetime.utcnow().isoformat()
                )
            ]
            
            # Mock LLM response
            mock_llm_router.complete.return_value = {
                'content': '''
                {
                    "similarities": ["Both use Method X", "Similar research questions"],
                    "differences": ["Different results", "Different conclusions"],
                    "common_themes": ["Machine learning", "Performance optimization"],
                    "unique_contributions": {
                        "Document 1": ["Novel approach A"],
                        "Document 2": ["Novel approach B"]
                    }
                }
                ''',
                'model': 'gemini-1.5-flash',
                'input_tokens': 300,
                'output_tokens': 150,
                'cost': 0.003
            }
            
            # Generate comparative summary
            summary = await comparative_service.generate_comparative_summary(
                document_ids=['doc1', 'doc2'],
                project_id='proj1'
            )
            
            # Verify
            assert len(summary.document_ids) == 2
            assert len(summary.similarities) == 2
            assert 'Method X' in summary.similarities[0]
            assert len(summary.differences) == 2
            assert len(summary.common_themes) == 2
            assert 'Document 1' in summary.unique_contributions
    
    @pytest.mark.asyncio
    async def test_comparative_summary_requires_multiple_docs(self, comparative_service):
        """Test that comparative summary requires at least 2 documents"""
        with pytest.raises(ValueError, match="at least 2 documents"):
            await comparative_service.generate_comparative_summary(
                document_ids=['doc1'],
                project_id='proj1'
            )


class TestDataExtractionService:
    """Test data extraction service"""
    
    @pytest.mark.asyncio
    async def test_extract_data(self, data_extraction_service, mock_vector_store, mock_llm_router):
        """Test extracting data from research paper"""
        # Mock vector store
        mock_chunks = [
            {
                'document_id': 'doc1',
                'chunk_id': 0,
                'text': 'We used deep learning with CNN architecture. Results showed 95% accuracy.',
                'score': 0.9
            }
        ]
        mock_vector_store.search.return_value = mock_chunks
        
        # Mock LLM response
        mock_llm_router.complete.return_value = {
            'content': '''
            {
                "methods": ["Deep learning", "CNN architecture"],
                "results": ["95% accuracy on test set", "Improved performance"],
                "datasets": ["ImageNet", "CIFAR-10"],
                "statistical_findings": [
                    {"metric": "accuracy", "value": "95%", "context": "test set"},
                    {"metric": "F1-score", "value": "0.93", "context": "validation"}
                ],
                "key_conclusions": ["Deep learning is effective", "CNN outperforms baseline"]
            }
            ''',
            'model': 'gemini-1.5-flash',
            'input_tokens': 200,
            'output_tokens': 100,
            'cost': 0.002
        }
        
        # Extract data
        data = await data_extraction_service.extract_data(
            document_id='doc1',
            project_id='proj1'
        )
        
        # Verify
        assert data.document_id == 'doc1'
        assert len(data.methods) == 2
        assert 'Deep learning' in data.methods
        assert len(data.results) == 2
        assert len(data.datasets) == 2
        assert 'ImageNet' in data.datasets
        assert len(data.statistical_findings) == 2
        assert data.statistical_findings[0]['metric'] == 'accuracy'
        assert len(data.key_conclusions) == 2
    
    @pytest.mark.asyncio
    async def test_extract_data_from_multiple(self, data_extraction_service):
        """Test extracting data from multiple documents"""
        # Mock extract_data
        with patch.object(data_extraction_service, 'extract_data') as mock_extract:
            mock_extract.side_effect = [
                ExtractedData(
                    document_id='doc1',
                    methods=['Method A'],
                    results=['Result A']
                ),
                ExtractedData(
                    document_id='doc2',
                    methods=['Method B'],
                    results=['Result B']
                )
            ]
            
            # Extract from multiple
            results = await data_extraction_service.extract_data_from_multiple(
                document_ids=['doc1', 'doc2'],
                project_id='proj1'
            )
            
            # Verify
            assert len(results) == 2
            assert results[0].document_id == 'doc1'
            assert results[1].document_id == 'doc2'


class TestDataExportService:
    """Test data export service"""
    
    def test_export_to_csv(self):
        """Test exporting data to CSV format"""
        # Create test data
        data = [
            ExtractedData(
                document_id='doc1',
                methods=['Method A', 'Method B'],
                results=['Result A'],
                datasets=['Dataset X'],
                statistical_findings=[{'metric': 'accuracy', 'value': '95%'}],
                key_conclusions=['Conclusion A']
            ),
            ExtractedData(
                document_id='doc2',
                methods=['Method C'],
                results=['Result B', 'Result C'],
                datasets=[],
                statistical_findings=[],
                key_conclusions=['Conclusion B']
            )
        ]
        
        # Export to CSV
        csv_content = DataExportService.export_to_csv(data)
        
        # Verify
        assert 'Document ID' in csv_content
        assert 'doc1' in csv_content
        assert 'doc2' in csv_content
        assert 'Method A; Method B' in csv_content
        assert 'Result A' in csv_content
    
    def test_export_to_json(self):
        """Test exporting data to JSON format"""
        import json
        
        # Create test data
        data = [
            ExtractedData(
                document_id='doc1',
                methods=['Method A'],
                results=['Result A'],
                datasets=['Dataset X'],
                statistical_findings=[],
                key_conclusions=['Conclusion A']
            )
        ]
        
        # Export to JSON
        json_content = DataExportService.export_to_json(data)
        
        # Verify
        parsed = json.loads(json_content)
        assert len(parsed) == 1
        assert parsed[0]['document_id'] == 'doc1'
        assert 'Method A' in parsed[0]['methods']
    
    def test_export_to_excel(self):
        """Test exporting data to Excel format"""
        # Create test data
        data = [
            ExtractedData(
                document_id='doc1',
                methods=['Method A'],
                results=['Result A'],
                datasets=['Dataset X'],
                statistical_findings=[],
                key_conclusions=['Conclusion A']
            )
        ]
        
        # Export to Excel
        try:
            excel_bytes = DataExportService.export_to_excel(data)
            
            # Verify
            assert isinstance(excel_bytes, bytes)
            assert len(excel_bytes) > 0
        except ValueError as e:
            # openpyxl not installed
            assert 'openpyxl' in str(e)
            pytest.skip("openpyxl not installed")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
