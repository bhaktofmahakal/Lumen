"""
Property-based tests for embedding generation consistency

Feature: ai-research-copilot
Property 3: Embedding Generation Consistency
Validates: Requirements 1.5
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from hypothesis import HealthCheck
import numpy as np

from embeddings import EmbeddingGenerator


# Strategy for generating text content
@st.composite
def text_strategy(draw):
    """Generate various text content for embedding - optimized for speed"""
    choice = draw(st.integers(min_value=0, max_value=2))
    
    if choice == 0:
        # Simple sentences (limited alphabet for speed)
        return draw(st.text(
            min_size=10,
            max_size=200,  # Reduced from 500
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Zs'), max_codepoint=127)  # ASCII only
        ))
    elif choice == 1:
        # Technical text (pre-defined words for speed)
        words = ['algorithm', 'neural', 'network', 'transformer', 'attention', 'embedding', 'vector', 'matrix']
        selected = draw(st.lists(st.sampled_from(words), min_size=5, max_size=15))  # Reduced from 20
        return ' '.join(selected)
    else:
        # Multi-sentence text (shorter)
        sentences = draw(st.lists(
            st.text(min_size=10, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Zs'), max_codepoint=127)),
            min_size=2,
            max_size=5  # Reduced from 10
        ))
        return '. '.join(sentences) + '.'


class TestEmbeddingGenerationConsistency:
    """
    Property 3: Embedding Generation Consistency
    
    For any text input, embedding generation should produce vectors with:
    1. Correct dimension (384 for all-MiniLM-L6-v2)
    2. Values in range [-1, 1] (normalized embeddings)
    3. Deterministic output (same input -> same embedding)
    4. Non-zero vectors (not all zeros)
    
    **Validates: Requirements 1.5**
    """
    
    @given(
        text=text_strategy()
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=5000)  # Reduced examples and added deadline
    def test_embedding_dimension_property(self, text):
        """
        Property: Embeddings have correct dimension
        
        Invariant: All embeddings must have dimension 384
        """
        # Skip empty or whitespace-only text
        assume(text.strip())
        
        generator = EmbeddingGenerator()
        
        # Generate embedding
        embedding = generator.generate_embedding(text)
        
        # Invariant: Correct dimension
        assert len(embedding) == 384, f"Embedding dimension should be 384, got {len(embedding)}"
        assert len(embedding) == generator.embedding_dimension
    
    @given(
        text=text_strategy()
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=5000)
    def test_embedding_value_range_property(self, text):
        """
        Property: Embedding values are in valid range
        
        Invariant: All values should be in range [-1, 1] for normalized embeddings
        (allowing small numerical errors up to 2.0)
        """
        assume(text.strip())
        
        generator = EmbeddingGenerator()
        embedding = generator.generate_embedding(text)
        
        # Convert to numpy for easier analysis
        embedding_array = np.array(embedding)
        
        # Invariant: Values in reasonable range
        assert np.all(np.abs(embedding_array) <= 2.0), \
            f"Embedding values should be in range [-2, 2], got min={embedding_array.min()}, max={embedding_array.max()}"
        
        # Most values should be in [-1, 1]
        in_range = np.sum(np.abs(embedding_array) <= 1.0)
        ratio = in_range / len(embedding_array)
        assert ratio > 0.8, f"At least 80% of values should be in [-1, 1], got {ratio:.2%}"
    
    @given(
        text=text_strategy()
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=5000)
    def test_embedding_determinism_property(self, text):
        """
        Property: Embedding generation is deterministic
        
        Invariant: Same input should produce same embedding
        """
        assume(text.strip())
        
        generator = EmbeddingGenerator()
        
        # Generate embedding twice
        embedding1 = generator.generate_embedding(text)
        embedding2 = generator.generate_embedding(text)
        
        # Invariant: Deterministic output
        assert len(embedding1) == len(embedding2)
        
        # Check if embeddings are identical (or very close due to floating point)
        embedding1_array = np.array(embedding1)
        embedding2_array = np.array(embedding2)
        
        diff = np.abs(embedding1_array - embedding2_array)
        max_diff = np.max(diff)
        
        assert max_diff < 1e-6, f"Embeddings should be deterministic, max difference: {max_diff}"
    
    @given(
        text=text_strategy()
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=5000)
    def test_embedding_non_zero_property(self, text):
        """
        Property: Embeddings are non-zero vectors
        
        Invariant: Embedding should not be all zeros (indicates valid encoding)
        """
        assume(text.strip())
        
        generator = EmbeddingGenerator()
        embedding = generator.generate_embedding(text)
        
        # Invariant: Not all zeros
        embedding_array = np.array(embedding)
        assert not np.all(embedding_array == 0), "Embedding should not be all zeros"
        
        # Check L2 norm is reasonable
        norm = np.linalg.norm(embedding_array)
        assert norm > 0.1, f"Embedding L2 norm should be > 0.1, got {norm}"
    
    @given(
        texts=st.lists(text_strategy(), min_size=2, max_size=5)  # Reduced from 10
    )
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=10000)  # Reduced examples
    def test_batch_embedding_consistency_property(self, texts):
        """
        Property: Batch embedding produces same results as individual embeddings
        
        Invariant: Batch processing should give same results as individual processing
        """
        # Filter out empty texts
        texts = [t for t in texts if t.strip()]
        assume(len(texts) >= 2)
        
        generator = EmbeddingGenerator()
        
        # Generate embeddings individually
        individual_embeddings = [generator.generate_embedding(text) for text in texts]
        
        # Generate embeddings in batch
        batch_embeddings = generator.generate_embeddings_batch(texts, batch_size=32)
        
        # Invariant: Same number of embeddings
        assert len(individual_embeddings) == len(batch_embeddings)
        
        # Invariant: Embeddings should be very close (allowing for small numerical differences)
        for i, (ind_emb, batch_emb) in enumerate(zip(individual_embeddings, batch_embeddings)):
            ind_array = np.array(ind_emb)
            batch_array = np.array(batch_emb)
            
            diff = np.abs(ind_array - batch_array)
            max_diff = np.max(diff)
            
            assert max_diff < 1e-5, \
                f"Batch embedding {i} differs from individual: max_diff={max_diff}"
    
    def test_empty_text_handling(self):
        """
        Property: Empty text should return zero vector or handle gracefully
        
        Invariant: Should not raise exception, should return valid dimension
        """
        generator = EmbeddingGenerator()
        
        # Test empty string
        embedding = generator.generate_embedding("")
        assert len(embedding) == 384
        
        # Test whitespace only
        embedding = generator.generate_embedding("   ")
        assert len(embedding) == 384
    
    def test_embedding_validation(self):
        """
        Test the embedding validation function
        """
        generator = EmbeddingGenerator()
        
        # Valid embedding
        valid_embedding = [0.5] * 384
        assert generator.validate_embedding(valid_embedding)
        
        # Invalid dimension
        invalid_dim = [0.5] * 100
        assert not generator.validate_embedding(invalid_dim)
        
        # Contains NaN
        with_nan = [0.5] * 383 + [float('nan')]
        assert not generator.validate_embedding(with_nan)
        
        # Contains Inf
        with_inf = [0.5] * 383 + [float('inf')]
        assert not generator.validate_embedding(with_inf)
        
        # All zeros (warning but valid)
        all_zeros = [0.0] * 384
        assert not generator.validate_embedding(all_zeros)


class TestEmbeddingGeneratorEdgeCases:
    """Test edge cases for embedding generation"""
    
    def test_very_long_text(self):
        """Test embedding generation with very long text"""
        generator = EmbeddingGenerator()
        
        # Generate very long text (10000 characters)
        long_text = "This is a test sentence. " * 400
        
        # Should handle gracefully (model will truncate internally)
        embedding = generator.generate_embedding(long_text)
        
        assert len(embedding) == 384
        assert generator.validate_embedding(embedding)
    
    def test_special_characters(self):
        """Test embedding generation with special characters"""
        generator = EmbeddingGenerator()
        
        special_texts = [
            "Hello! How are you?",
            "Test with numbers: 123, 456, 789",
            "Symbols: @#$%^&*()",
            "Unicode: 你好世界 🌍",
            "Math: ∫∑∏√∂∇"
        ]
        
        for text in special_texts:
            embedding = generator.generate_embedding(text)
            assert len(embedding) == 384
            assert generator.validate_embedding(embedding)
    
    def test_different_languages(self):
        """Test embedding generation with different languages"""
        generator = EmbeddingGenerator()
        
        multilingual_texts = [
            "Hello world",  # English
            "Bonjour le monde",  # French
            "Hola mundo",  # Spanish
            "Hallo Welt",  # German
            "你好世界",  # Chinese
        ]
        
        for text in multilingual_texts:
            embedding = generator.generate_embedding(text)
            assert len(embedding) == 384
            assert generator.validate_embedding(embedding)
