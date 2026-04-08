"""
Property-based tests for document upload validation

Feature: ai-research-copilot
Property 1: Document Upload Validation
Validates: Requirements 1.1
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from hypothesis import HealthCheck
import io
from fastapi import UploadFile

from document_service import DocumentValidator


# Strategy for generating file sizes
@st.composite
def file_size_strategy(draw):
    """Generate file sizes including edge cases"""
    # Generate sizes around the 50MB boundary
    max_size = 52428800  # 50MB
    
    choice = draw(st.integers(min_value=0, max_value=4))
    
    if choice == 0:
        # Valid sizes (under 50MB)
        return draw(st.integers(min_value=1, max_value=max_size - 1))
    elif choice == 1:
        # Exactly at boundary
        return max_size
    elif choice == 2:
        # Just over boundary
        return draw(st.integers(min_value=max_size + 1, max_value=max_size + 1000000))
    elif choice == 3:
        # Empty file
        return 0
    else:
        # Very large file
        return draw(st.integers(min_value=max_size * 2, max_value=max_size * 10))


# Strategy for generating filenames
@st.composite
def filename_strategy(draw):
    """Generate filenames with various extensions"""
    name = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    extension = draw(st.sampled_from(['pdf', 'PDF', 'txt', 'doc', 'docx', 'jpg', 'png']))
    return f"{name}.{extension}"


class TestDocumentUploadValidation:
    """
    Property 1: Document Upload Validation
    
    For any uploaded file, the system should accept valid PDFs under 50MB
    and reject all other files with appropriate error messages.
    
    **Validates: Requirements 1.1**
    """
    
    @given(
        filename=filename_strategy(),
        file_size=file_size_strategy()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    def test_file_validation_property(self, filename, file_size):
        """
        Property: Valid PDFs under 50MB are accepted, all others rejected
        
        Invariants:
        1. Files with .pdf extension are considered valid file type
        2. Files under 50MB (52428800 bytes) are considered valid size
        3. Files must be both valid type AND valid size to be accepted
        4. Invalid files must return descriptive error messages
        """
        validator = DocumentValidator()
        
        # Create mock UploadFile
        file_content = b'x' * file_size if file_size > 0 else b''
        mock_file = UploadFile(
            filename=filename,
            file=io.BytesIO(file_content)
        )
        
        # Test file type validation
        is_valid_type, type_error = validator.validate_file(mock_file)
        
        # Test file size validation
        is_valid_size, size_error = validator.validate_file_size(file_size)
        
        # Property assertions
        file_ext = filename.split('.')[-1].lower()
        max_size = 52428800  # 50MB
        
        # Invariant 1: PDF extension should pass type validation
        if file_ext == 'pdf':
            assert is_valid_type, f"PDF file should pass type validation: {filename}"
            assert type_error is None
        else:
            assert not is_valid_type, f"Non-PDF file should fail type validation: {filename}"
            assert type_error is not None
            assert "Invalid file type" in type_error or "Only pdf files are allowed" in type_error
        
        # Invariant 2: Files under 50MB should pass size validation
        if 0 < file_size <= max_size:
            assert is_valid_size, f"File under 50MB should pass size validation: {file_size} bytes"
            assert size_error is None
        elif file_size == 0:
            assert not is_valid_size, "Empty file should fail size validation"
            assert size_error is not None
            assert "empty" in size_error.lower()
        else:
            assert not is_valid_size, f"File over 50MB should fail size validation: {file_size} bytes"
            assert size_error is not None
            assert "exceeds maximum" in size_error.lower()
        
        # Invariant 3: Both type and size must be valid for acceptance
        should_accept = (file_ext == 'pdf') and (0 < file_size <= max_size)
        is_accepted = is_valid_type and is_valid_size
        
        assert is_accepted == should_accept, \
            f"Acceptance mismatch for {filename} ({file_size} bytes): " \
            f"expected {should_accept}, got {is_accepted}"
    
    @given(
        file_size=st.integers(min_value=1, max_value=52428800)
    )
    @settings(max_examples=50)
    def test_valid_pdf_acceptance(self, file_size):
        """
        Property: All valid PDFs under 50MB must be accepted
        
        This test focuses on the positive case - ensuring we don't
        incorrectly reject valid documents.
        """
        validator = DocumentValidator()
        
        # Create valid PDF file
        mock_file = UploadFile(
            filename="test_document.pdf",
            file=io.BytesIO(b'x' * file_size)
        )
        
        # Both validations should pass
        is_valid_type, type_error = validator.validate_file(mock_file)
        is_valid_size, size_error = validator.validate_file_size(file_size)
        
        assert is_valid_type, f"Valid PDF should pass type validation"
        assert type_error is None
        assert is_valid_size, f"File under 50MB should pass size validation"
        assert size_error is None
    
    @given(
        file_size=st.integers(min_value=52428801, max_value=104857600)  # 50MB to 100MB
    )
    @settings(max_examples=50, deadline=None)
    def test_oversized_pdf_rejection(self, file_size):
        """
        Property: All PDFs over 50MB must be rejected
        
        This test ensures we properly enforce the size limit.
        """
        validator = DocumentValidator()
        
        # Create oversized PDF file
        mock_file = UploadFile(
            filename="large_document.pdf",
            file=io.BytesIO(b'x' * file_size)
        )
        
        # Type validation should pass, size validation should fail
        is_valid_type, type_error = validator.validate_file(mock_file)
        is_valid_size, size_error = validator.validate_file_size(file_size)
        
        assert is_valid_type, "PDF should pass type validation"
        assert not is_valid_size, f"File over 50MB should fail size validation: {file_size} bytes"
        assert size_error is not None
        assert "exceeds maximum" in size_error.lower()
    
    @given(
        extension=st.sampled_from(['txt', 'doc', 'docx', 'jpg', 'png', 'xlsx', 'csv'])
    )
    @settings(max_examples=50)
    def test_non_pdf_rejection(self, extension):
        """
        Property: All non-PDF files must be rejected regardless of size
        
        This test ensures we only accept PDF files.
        """
        validator = DocumentValidator()
        
        # Create non-PDF file
        mock_file = UploadFile(
            filename=f"document.{extension}",
            file=io.BytesIO(b'x' * 1000)
        )
        
        # Type validation should fail
        is_valid_type, type_error = validator.validate_file(mock_file)
        
        assert not is_valid_type, f"Non-PDF file (.{extension}) should fail type validation"
        assert type_error is not None
        assert "Invalid file type" in type_error or "Only pdf files are allowed" in type_error
