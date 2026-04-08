"""
Property-based tests for duplicate detection accuracy

Feature: ai-research-copilot
Property 4: Duplicate Detection Accuracy
Validates: Requirements 1.11
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from hypothesis import HealthCheck
import hashlib
import io

from document_service import DocumentService


# Strategy for generating file content
@st.composite
def file_content_strategy(draw):
    """Generate various file contents"""
    choice = draw(st.integers(min_value=0, max_value=3))
    
    if choice == 0:
        # Random bytes
        size = draw(st.integers(min_value=100, max_value=10000))
        return draw(st.binary(min_size=size, max_size=size))
    elif choice == 1:
        # Text content as bytes
        text = draw(st.text(min_size=100, max_size=5000))
        return text.encode('utf-8')
    elif choice == 2:
        # Repeated pattern
        pattern = draw(st.binary(min_size=10, max_size=100))
        repeats = draw(st.integers(min_value=10, max_value=100))
        return pattern * repeats
    else:
        # Mixed content
        parts = draw(st.lists(st.binary(min_size=10, max_size=100), min_size=5, max_size=20))
        return b''.join(parts)


class TestDuplicateDetectionAccuracy:
    """
    Property 4: Duplicate Detection Accuracy
    
    For any document content, the system should:
    1. Calculate consistent SHA-256 hash
    2. Detect identical documents as duplicates
    3. Detect different documents as non-duplicates
    4. Handle hash collisions gracefully (extremely rare)
    
    **Validates: Requirements 1.11**
    """
    
    @given(
        content=file_content_strategy()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow], deadline=None)
    def test_hash_consistency_property(self, content):
        """
        Property: Hash calculation is deterministic
        
        Invariant: Same content should produce same hash
        """
        assume(len(content) > 0)
        
        service = DocumentService()
        
        # Calculate hash twice
        hash1 = service.calculate_file_hash(content)
        hash2 = service.calculate_file_hash(content)
        
        # Invariant: Deterministic hashing
        assert hash1 == hash2, "Hash should be deterministic"
        assert len(hash1) == 64, "SHA-256 hash should be 64 hex characters"
        assert all(c in '0123456789abcdef' for c in hash1), "Hash should be valid hex"
    
    @given(
        content=file_content_strategy()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow], deadline=None)
    def test_identical_content_detection_property(self, content):
        """
        Property: Identical content produces identical hash
        
        Invariant: Exact copies should be detected as duplicates
        """
        assume(len(content) > 0)
        
        service = DocumentService()
        
        # Create two copies of the same content
        content_copy = bytes(content)  # Create a copy
        
        hash1 = service.calculate_file_hash(content)
        hash2 = service.calculate_file_hash(content_copy)
        
        # Invariant: Identical content -> identical hash
        assert hash1 == hash2, "Identical content should produce identical hash"
    
    @given(
        content1=file_content_strategy(),
        content2=file_content_strategy()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow], deadline=None)
    def test_different_content_detection_property(self, content1, content2):
        """
        Property: Different content produces different hash (with high probability)
        
        Invariant: Different content should produce different hashes
        (collision probability is negligible for SHA-256)
        """
        # Skip if contents are identical
        assume(content1 != content2)
        assume(len(content1) > 0 and len(content2) > 0)
        
        service = DocumentService()
        
        hash1 = service.calculate_file_hash(content1)
        hash2 = service.calculate_file_hash(content2)
        
        # Invariant: Different content -> different hash (with overwhelming probability)
        assert hash1 != hash2, "Different content should produce different hashes"
    
    @given(
        content=file_content_strategy(),
        modification_position=st.integers(min_value=0, max_value=100)
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow], deadline=None)
    def test_single_byte_change_detection_property(self, content, modification_position):
        """
        Property: Even single byte change produces different hash
        
        Invariant: Avalanche effect - small change -> completely different hash
        """
        assume(len(content) > 100)
        
        # Ensure modification position is within bounds
        modification_position = modification_position % len(content)
        
        service = DocumentService()
        
        # Original hash
        original_hash = service.calculate_file_hash(content)
        
        # Modify single byte
        modified_content = bytearray(content)
        modified_content[modification_position] = (modified_content[modification_position] + 1) % 256
        modified_content = bytes(modified_content)
        
        modified_hash = service.calculate_file_hash(modified_content)
        
        # Invariant: Single byte change -> different hash
        assert original_hash != modified_hash, \
            "Single byte change should produce different hash (avalanche effect)"
        
        # Hashes should be completely different (not just 1 character)
        diff_count = sum(c1 != c2 for c1, c2 in zip(original_hash, modified_hash))
        assert diff_count > 10, \
            f"Hash should change significantly, only {diff_count} characters differ"
    
    @given(
        content=file_content_strategy()
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow], deadline=None)
    def test_hash_length_property(self, content):
        """
        Property: Hash always has fixed length
        
        Invariant: SHA-256 hash is always 64 hex characters (256 bits)
        """
        assume(len(content) > 0)
        
        service = DocumentService()
        hash_value = service.calculate_file_hash(content)
        
        # Invariant: Fixed length
        assert len(hash_value) == 64, f"SHA-256 hash should be 64 characters, got {len(hash_value)}"
    
    @given(
        size=st.integers(min_value=1, max_value=100000)
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow], deadline=None)
    def test_hash_independent_of_size_property(self, size):
        """
        Property: Hash length is independent of content size
        
        Invariant: Hash is always 64 characters regardless of input size
        """
        service = DocumentService()
        
        # Create content of specific size
        content = b'x' * size
        hash_value = service.calculate_file_hash(content)
        
        # Invariant: Fixed length regardless of input size
        assert len(hash_value) == 64, \
            f"Hash should be 64 characters for {size} byte input, got {len(hash_value)}"
    
    def test_empty_content_handling(self):
        """
        Property: Empty content should produce valid hash
        
        Invariant: Even empty content should hash consistently
        """
        service = DocumentService()
        
        # Hash of empty content
        hash1 = service.calculate_file_hash(b'')
        hash2 = service.calculate_file_hash(b'')
        
        # Should be consistent
        assert hash1 == hash2
        assert len(hash1) == 64
        
        # Known SHA-256 hash of empty string
        expected = hashlib.sha256(b'').hexdigest()
        assert hash1 == expected
    
    def test_known_hash_values(self):
        """
        Test against known SHA-256 hash values
        
        Ensures our implementation matches standard SHA-256
        """
        service = DocumentService()
        
        test_cases = [
            (b'hello', '2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824'),
            (b'world', '486ea46224d1bb4fb680f34f7c9ad96a8f24ec88be73ea8e5a6c65260e9cb8a7'),
            (b'test', '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08'),
        ]
        
        for content, expected_hash in test_cases:
            calculated_hash = service.calculate_file_hash(content)
            assert calculated_hash == expected_hash, \
                f"Hash mismatch for {content}: expected {expected_hash}, got {calculated_hash}"


class TestDuplicateDetectionIntegration:
    """Integration tests for duplicate detection in document upload flow"""
    
    @given(
        content=file_content_strategy()
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow], deadline=None)
    def test_duplicate_detection_workflow_property(self, content):
        """
        Property: Duplicate detection workflow is consistent
        
        Invariant: Same content uploaded twice should be detected as duplicate
        """
        assume(len(content) > 100)
        
        service = DocumentService()
        
        # Calculate hash for first upload
        hash1 = service.calculate_file_hash(content)
        
        # Simulate second upload with same content
        hash2 = service.calculate_file_hash(content)
        
        # Invariant: Should detect as duplicate
        assert hash1 == hash2, "Duplicate content should have same hash"
    
    def test_hash_collision_resistance(self):
        """
        Property: Hash collisions are extremely rare
        
        Test that similar but different content produces different hashes
        """
        service = DocumentService()
        
        # Create similar content
        base_content = b"This is a test document for duplicate detection. " * 100
        
        # Create variations
        variations = [
            base_content,
            base_content + b" ",  # Extra space
            base_content[:-1],  # One byte shorter
            base_content.replace(b"test", b"TEST"),  # Case change
            base_content + b"extra",  # Extra content
        ]
        
        # Calculate hashes
        hashes = [service.calculate_file_hash(content) for content in variations]
        
        # All hashes should be different
        assert len(set(hashes)) == len(hashes), \
            "All variations should produce different hashes"
    
    def test_hash_format_validation(self):
        """
        Property: Hash format is always valid
        
        Invariant: Hash should be valid hexadecimal string
        """
        service = DocumentService()
        
        test_contents = [
            b"short",
            b"medium length content for testing",
            b"x" * 10000,  # Long content
            b"\x00\x01\x02\x03",  # Binary content
            "Unicode: 你好世界".encode('utf-8'),  # Unicode
        ]
        
        for content in test_contents:
            hash_value = service.calculate_file_hash(content)
            
            # Validate format
            assert len(hash_value) == 64
            assert all(c in '0123456789abcdef' for c in hash_value), \
                f"Invalid hash format: {hash_value}"
            
            # Should be lowercase hex
            assert hash_value == hash_value.lower()
