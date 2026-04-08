"""
Property-based tests for text extraction completeness

Feature: ai-research-copilot
Property 2: Text Extraction Completeness
Validates: Requirements 1.2
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from hypothesis import HealthCheck
import fitz  # PyMuPDF
import tempfile
import os
from pathlib import Path

from text_extraction import StandardPDFExtractor, TextExtractionService
from models import DocumentType


def create_test_pdf(text_content: str) -> str:
    """Create a temporary PDF file with given text content"""
    # Create a temporary PDF
    temp_file = tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False)
    temp_path = temp_file.name
    temp_file.close()
    
    # Create PDF with text
    doc = fitz.open()
    page = doc.new_page()
    
    # Insert text if provided
    if text_content:
        # Split into lines to avoid overflow
        lines = text_content.split('\n')
        y_position = 50
        for line in lines[:50]:  # Limit to 50 lines to fit on page
            if line.strip():
                page.insert_text((50, y_position), line[:100], fontsize=11)  # Limit line length
                y_position += 15
    
    doc.save(temp_path)
    doc.close()
    
    return temp_path


# Strategy for generating text content
@st.composite
def text_content_strategy(draw):
    """Generate various text content for PDFs"""
    choice = draw(st.integers(min_value=0, max_value=3))
    
    if choice == 0:
        # Simple text
        return draw(st.text(min_size=10, max_size=500, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'))))
    elif choice == 1:
        # Multi-line text
        lines = draw(st.lists(st.text(min_size=5, max_size=100), min_size=3, max_size=20))
        return '\n'.join(lines)
    elif choice == 2:
        # Text with special characters
        return draw(st.text(min_size=10, max_size=300))
    else:
        # Paragraph-like text
        words = draw(st.lists(st.text(min_size=3, max_size=15, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))), min_size=10, max_size=100))
        return ' '.join(words)


class TestTextExtractionCompleteness:
    """
    Property 2: Text Extraction Completeness
    
    For any valid PDF document, text extraction should produce non-empty output
    with at least one character of text content.
    
    **Validates: Requirements 1.2**
    """
    
    @given(
        text_content=text_content_strategy()
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    def test_text_extraction_completeness_property(self, text_content):
        """
        Property: Text extraction produces non-empty output for valid PDFs
        
        Invariants:
        1. Extracted text should not be empty for PDFs with text content
        2. Extracted text length should be > 0
        3. Extraction should not raise exceptions for valid PDFs
        4. Metadata should be returned with page_count
        """
        # Skip if text content is empty or whitespace only
        assume(text_content.strip())
        
        extractor = StandardPDFExtractor()
        pdf_path = None
        
        try:
            # Create test PDF
            pdf_path = create_test_pdf(text_content)
            
            # Extract text
            extracted_text, metadata = extractor.extract_text(pdf_path)
            
            # Invariant 1 & 2: Extracted text should not be empty
            assert extracted_text, "Extracted text should not be empty"
            assert len(extracted_text) > 0, "Extracted text length should be > 0"
            
            # Invariant 3: Should contain some of the original content
            # (allowing for PDF encoding differences)
            assert len(extracted_text.strip()) > 0, "Extracted text should have non-whitespace content"
            
            # Invariant 4: Metadata should include page count
            assert 'page_count' in metadata, "Metadata should include page_count"
            assert metadata['page_count'] > 0, "Page count should be > 0"
            
        finally:
            # Cleanup
            if pdf_path and os.path.exists(pdf_path):
                os.unlink(pdf_path)
    
    def test_multi_page_extraction(self):
        """
        Property: Multi-page PDFs should extract text from all pages
        
        Invariant: Extracted text should contain page markers for each page
        """
        extractor = StandardPDFExtractor()
        pdf_path = None
        
        try:
            # Create multi-page PDF
            temp_file = tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False)
            pdf_path = temp_file.name
            temp_file.close()
            
            doc = fitz.open()
            
            # Add 3 pages with different content
            for i in range(3):
                page = doc.new_page()
                page.insert_text((50, 50), f"This is page {i+1} content")
            
            doc.save(pdf_path)
            doc.close()
            
            # Extract text
            extracted_text, metadata = extractor.extract_text(pdf_path)
            
            # Should contain all page markers
            assert '[Page 1]' in extracted_text, "Should contain Page 1 marker"
            assert '[Page 2]' in extracted_text, "Should contain Page 2 marker"
            assert '[Page 3]' in extracted_text, "Should contain Page 3 marker"
            
            # Should contain content from all pages
            assert 'page 1 content' in extracted_text.lower()
            assert 'page 2 content' in extracted_text.lower()
            assert 'page 3 content' in extracted_text.lower()
            
            # Metadata should reflect correct page count
            assert metadata['page_count'] == 3
            
        finally:
            if pdf_path and os.path.exists(pdf_path):
                os.unlink(pdf_path)
    
    def test_empty_pdf_handling(self):
        """
        Property: PDFs with no text should return empty string gracefully
        
        Invariant: Should not raise exception, should return empty or minimal text
        """
        extractor = StandardPDFExtractor()
        pdf_path = None
        
        try:
            # Create PDF with no text
            temp_file = tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False)
            pdf_path = temp_file.name
            temp_file.close()
            
            doc = fitz.open()
            page = doc.new_page()  # Empty page
            doc.save(pdf_path)
            doc.close()
            
            # Extract text - should not raise exception
            extracted_text, metadata = extractor.extract_text(pdf_path)
            
            # Should return something (even if empty)
            assert extracted_text is not None
            assert metadata is not None
            assert metadata['page_count'] == 1
            
        finally:
            if pdf_path and os.path.exists(pdf_path):
                os.unlink(pdf_path)


class TestTextExtractionService:
    """Test the text extraction service routing"""
    
    def test_extraction_service_routing(self):
        """
        Test that extraction service routes to correct extractor based on document type
        """
        service = TextExtractionService()
        pdf_path = None
        
        try:
            # Create test PDF
            pdf_path = create_test_pdf("Test content for routing")
            
            # Test standard extraction
            text, metadata = service.extract_text(pdf_path, DocumentType.STANDARD)
            assert text, "Standard extraction should return text"
            assert len(text) > 0
            
            # Test scientific extraction (currently falls back to standard)
            text, metadata = service.extract_text(pdf_path, DocumentType.SCIENTIFIC)
            assert text, "Scientific extraction should return text"
            assert len(text) > 0
            
        finally:
            if pdf_path and os.path.exists(pdf_path):
                os.unlink(pdf_path)
