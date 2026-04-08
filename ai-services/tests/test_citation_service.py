"""
Tests for Citation Management Service
Requirements: 13.1, 13.2, 13.3, 13.5, 13.9
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
import json

from citation_service import (
    CitationExtractor,
    CitationAPIClient,
    BibTeXGenerator,
    CitationExporter,
    CitationService
)


class TestCitationExtractor:
    """Test citation extraction from PDFs"""
    
    def test_extract_doi_from_pdf(self):
        """Test DOI extraction from PDF content"""
        extractor = CitationExtractor()
        
        # Mock PyMuPDF document
        mock_doc = MagicMock()
        mock_page = Mock()
        mock_page.get_text.return_value = "DOI: 10.1234/example.2024"
        mock_doc.__getitem__ = Mock(return_value=mock_page)
        mock_doc.page_count = 1
        
        doi = extractor._extract_doi(mock_doc)
        assert doi == "10.1234/example.2024"
    
    def test_extract_arxiv_id_from_pdf(self):
        """Test arXiv ID extraction from PDF content"""
        extractor = CitationExtractor()
        
        # Mock PyMuPDF document
        mock_doc = MagicMock()
        mock_page = Mock()
        mock_page.get_text.return_value = "arXiv:2401.12345"
        mock_doc.__getitem__ = Mock(return_value=mock_page)
        mock_doc.page_count = 1
        
        arxiv_id = extractor._extract_arxiv_id(mock_doc)
        assert arxiv_id == "2401.12345"
    
    def test_parse_authors(self):
        """Test author string parsing"""
        extractor = CitationExtractor()
        
        # Test comma-separated
        authors = extractor._parse_authors("John Doe, Jane Smith, Bob Johnson")
        assert len(authors) == 3
        assert "John Doe" in authors
        
        # Test 'and' separator
        authors = extractor._parse_authors("John Doe and Jane Smith")
        assert len(authors) == 2
        
        # Test empty string
        authors = extractor._parse_authors("")
        assert len(authors) == 0


class TestCitationAPIClient:
    """Test external citation API clients"""
    
    @patch('requests.get')
    def test_fetch_from_crossref(self, mock_get):
        """Test fetching metadata from Crossref API"""
        client = CitationAPIClient()
        
        # Mock Crossref response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'message': {
                'title': ['Test Paper'],
                'author': [
                    {'given': 'John', 'family': 'Doe'},
                    {'given': 'Jane', 'family': 'Smith'}
                ],
                'published-print': {'date-parts': [[2024]]},
                'container-title': ['Test Journal'],
                'volume': '10',
                'issue': '2',
                'page': '123-145',
                'DOI': '10.1234/test',
                'URL': 'https://doi.org/10.1234/test'
            }
        }
        mock_get.return_value = mock_response
        
        result = client.fetch_from_crossref('10.1234/test')
        
        assert result is not None
        assert result['title'] == 'Test Paper'
        assert len(result['authors']) == 2
        assert result['publication_year'] == 2024
        assert result['journal'] == 'Test Journal'

    @patch('requests.get')
    def test_fetch_from_semantic_scholar(self, mock_get):
        """Test fetching metadata from Semantic Scholar API"""
        client = CitationAPIClient()
        
        # Mock Semantic Scholar response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'title': 'Test Paper',
            'authors': [
                {'name': 'John Doe'},
                {'name': 'Jane Smith'}
            ],
            'year': 2024,
            'venue': 'Test Conference',
            'doi': '10.1234/test',
            'arxivId': '2401.12345',
            'url': 'https://semanticscholar.org/paper/test',
            'abstract': 'This is a test abstract.'
        }
        mock_get.return_value = mock_response
        
        result = client.fetch_from_semantic_scholar('10.1234/test', 'doi')
        
        assert result is not None
        assert result['title'] == 'Test Paper'
        assert len(result['authors']) == 2
        assert result['publication_year'] == 2024
    
    @patch('requests.get')
    def test_fetch_from_arxiv(self, mock_get):
        """Test fetching metadata from arXiv API"""
        client = CitationAPIClient()
        
        # Mock arXiv XML response
        xml_response = '''<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
            <entry>
                <title>Test Paper Title</title>
                <author><name>John Doe</name></author>
                <author><name>Jane Smith</name></author>
                <published>2024-01-15T00:00:00Z</published>
                <summary>This is a test abstract.</summary>
            </entry>
        </feed>'''
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = xml_response.encode('utf-8')
        mock_get.return_value = mock_response
        
        result = client.fetch_from_arxiv('2401.12345')
        
        assert result is not None
        assert result['title'] == 'Test Paper Title'
        assert len(result['authors']) == 2
        assert result['publication_year'] == 2024


class TestBibTeXGenerator:
    """Test BibTeX generation"""
    
    def test_generate_bibtex_article(self):
        """Test BibTeX generation for journal article"""
        generator = BibTeXGenerator()
        
        citation = {
            'title': 'Test Paper',
            'authors': ['John Doe', 'Jane Smith'],
            'publication_year': 2024,
            'journal': 'Test Journal',
            'volume': '10',
            'issue': '2',
            'pages': '123-145',
            'doi': '10.1234/test'
        }
        
        bibtex = generator.generate_bibtex(citation, 'Doe2024')
        
        assert '@article{Doe2024,' in bibtex
        assert 'title = {Test Paper}' in bibtex
        assert 'author = {John Doe and Jane Smith}' in bibtex
        assert 'year = {2024}' in bibtex
        assert 'journal = {Test Journal}' in bibtex
        assert 'doi = {10.1234/test}' in bibtex
    
    def test_format_apa_citation(self):
        """Test APA citation formatting"""
        generator = BibTeXGenerator()
        
        citation = {
            'authors': ['Doe, J.', 'Smith, J.'],
            'publication_year': 2024,
            'title': 'Test Paper',
            'journal': 'Test Journal',
            'volume': '10',
            'pages': '123-145',
            'doi': '10.1234/test'
        }
        
        formatted = generator.format_citation(citation, 'APA')
        
        assert 'Doe, J.' in formatted
        assert '(2024)' in formatted
        assert 'Test Paper' in formatted
        assert 'Test Journal' in formatted
    
    def test_format_mla_citation(self):
        """Test MLA citation formatting"""
        generator = BibTeXGenerator()
        
        citation = {
            'authors': ['Doe, John'],
            'title': 'Test Paper',
            'journal': 'Test Journal',
            'volume': '10',
            'issue': '2',
            'publication_year': 2024,
            'pages': '123-145'
        }
        
        formatted = generator.format_citation(citation, 'MLA')
        
        assert 'Doe, John' in formatted
        assert 'Test Paper' in formatted  # Title is in quotes in the output
        assert 'Test Journal' in formatted
        assert 'vol. 10' in formatted


class TestCitationExporter:
    """Test citation export functionality"""
    
    def test_export_bibtex(self):
        """Test BibTeX export"""
        exporter = CitationExporter()
        
        citations = [
            {
                'id': 1,
                'citation_key': 'Doe2024',
                'title': 'Test Paper 1',
                'authors': ['John Doe'],
                'publication_year': 2024,
                'journal': 'Test Journal',
                'doi': '10.1234/test1'
            },
            {
                'id': 2,
                'citation_key': 'Smith2024',
                'title': 'Test Paper 2',
                'authors': ['Jane Smith'],
                'publication_year': 2024,
                'journal': 'Test Journal',
                'doi': '10.1234/test2'
            }
        ]
        
        result = exporter.export_bibtex(citations)
        
        assert '@article{Doe2024,' in result
        assert '@article{Smith2024,' in result
        assert 'Test Paper 1' in result
        assert 'Test Paper 2' in result
    
    def test_export_ris(self):
        """Test RIS export"""
        exporter = CitationExporter()
        
        citations = [
            {
                'title': 'Test Paper',
                'authors': ['John Doe', 'Jane Smith'],
                'publication_year': 2024,
                'journal': 'Test Journal',
                'volume': '10',
                'doi': '10.1234/test'
            }
        ]
        
        result = exporter.export_ris(citations)
        
        assert 'TY  - JOUR' in result
        assert 'TI  - Test Paper' in result
        assert 'AU  - John Doe' in result
        assert 'AU  - Jane Smith' in result
        assert 'PY  - 2024' in result
        assert 'ER  - ' in result
    
    def test_export_endnote(self):
        """Test EndNote XML export"""
        exporter = CitationExporter()
        
        citations = [
            {
                'title': 'Test Paper',
                'authors': ['John Doe'],
                'publication_year': 2024,
                'journal': 'Test Journal',
                'doi': '10.1234/test'
            }
        ]
        
        result = exporter.export_endnote(citations)
        
        assert '<?xml version="1.0"' in result
        assert '<records>' in result
        assert '<title>Test Paper</title>' in result
        assert '<author>John Doe</author>' in result
        assert '</records>' in result


class TestCitationService:
    """Test citation service integration"""
    
    @pytest.mark.asyncio
    async def test_generate_citation_key(self):
        """Test citation key generation"""
        service = CitationService()
        
        metadata = {
            'authors': ['John Doe', 'Jane Smith'],
            'publication_year': 2024
        }
        
        key = service._generate_citation_key(metadata)
        assert key == 'Doe2024'
        
        # Test without authors
        metadata = {'publication_year': 2024}
        key = service._generate_citation_key(metadata)
        assert key == 'Unknown2024'
    
    @pytest.mark.asyncio
    @patch('citation_service.db_manager')
    async def test_check_duplicate(self, mock_db):
        """Test duplicate citation detection"""
        service = CitationService()
        
        # Mock database connection
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_result = Mock()
        mock_result.fetchone.return_value = {'id': 1, 'citation_key': 'Doe2024'}
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=False)
        mock_cursor.execute = Mock()
        mock_cursor.fetchone = Mock(return_value={'id': 1})
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.close = Mock()
        mock_db.get_connection.return_value = mock_conn
        
        duplicate = await service._check_duplicate('project_1', 'Doe2024')
        assert duplicate is not None
        assert duplicate['id'] == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
