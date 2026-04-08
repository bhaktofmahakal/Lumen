"""
Unit tests for RAG service components
Tests for query decomposition, agentic retrieval, and VoiceAgentRAG
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import asyncio

# Mock dependencies before importing
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def mock_vector_store():
    """Mock Qdrant vector store"""
    with patch('rag_service.QdrantVectorStore') as mock:
        instance = Mock()
        # Make search synchronous (not async) since it's called via asyncio.to_thread
        def mock_search(*args, **kwargs):
            return [
                {
                    'id': 'doc1_chunk1',
                    'score': 0.95,
                    'document_id': 'doc1',
                    'chunk_id': 1,
                    'text': 'Sample text about transformers',
                    'page_number': 1,
                    'section': 'Introduction'
                },
                {
                    'id': 'doc1_chunk2',
                    'score': 0.85,
                    'document_id': 'doc1',
                    'chunk_id': 2,
                    'text': 'More details about attention mechanism',
                    'page_number': 2,
                    'section': 'Methods'
                }
            ]
        instance.search = mock_search
        mock.return_value = instance
        yield instance


@pytest.fixture
def mock_embedding_generator():
    """Mock embedding generator"""
    with patch('rag_service.EmbeddingGenerator') as mock:
        instance = Mock()
        instance.generate_embedding = Mock(return_value=[0.1] * 384)
        mock.return_value = instance
        yield instance


@pytest.fixture
def mock_llm_router():
    """Mock LLM router"""
    mock = Mock()
    mock.complete = AsyncMock(return_value={
        'content': 'What are transformers?\nHow do attention mechanisms work?\nWhat are the applications of transformers?',
        'model': 'gemini-balanced',
        'input_tokens': 50,
        'output_tokens': 30,
        'cost': 0.001
    })
    return mock


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    mock = Mock()
    mock.get = Mock(return_value=None)
    mock.setex = Mock()
    return mock


@pytest.mark.asyncio
async def test_semantic_search_basic(mock_vector_store, mock_embedding_generator):
    """Test basic semantic search functionality"""
    from rag_service import SemanticSearchService
    
    service = SemanticSearchService(
        vector_store=mock_vector_store,
        embedding_generator=mock_embedding_generator
    )
    
    results = await service.search(
        query="What are transformers?",
        limit=10
    )
    
    assert len(results) == 2
    assert results[0]['score'] >= results[1]['score']  # Sorted by score
    assert all(0 <= r['score'] <= 1 for r in results)  # Valid score range


@pytest.mark.asyncio
async def test_semantic_search_with_filters(mock_vector_store, mock_embedding_generator):
    """Test semantic search with project and document filters"""
    from rag_service import SemanticSearchService
    
    service = SemanticSearchService(
        vector_store=mock_vector_store,
        embedding_generator=mock_embedding_generator
    )
    
    results = await service.search(
        query="transformers",
        project_id="project123",
        document_ids=["doc1"],
        limit=5
    )
    
    assert len(results) <= 5
    mock_embedding_generator.generate_embedding.assert_called_once()


@pytest.mark.asyncio
async def test_query_decomposition(mock_llm_router):
    """Test query decomposition into sub-queries"""
    from rag_service import QueryDecomposer
    
    decomposer = QueryDecomposer(llm_router=mock_llm_router)
    
    complex_query = "Explain the architecture of transformer models and their applications in natural language processing"
    
    sub_queries = await decomposer.decompose_query(complex_query, max_sub_queries=3)
    
    assert len(sub_queries) > 0
    assert len(sub_queries) <= 3
    assert all(isinstance(q, str) for q in sub_queries)


@pytest.mark.asyncio
async def test_query_decomposition_simple_query(mock_llm_router):
    """Test that simple queries are not decomposed"""
    from rag_service import QueryDecomposer
    
    decomposer = QueryDecomposer(llm_router=mock_llm_router)
    
    simple_query = "What is AI?"
    
    sub_queries = await decomposer.decompose_query(simple_query)
    
    # Simple query should not be decomposed
    assert len(sub_queries) == 1
    assert sub_queries[0] == simple_query


@pytest.mark.asyncio
async def test_agentic_retrieval(mock_vector_store, mock_embedding_generator, mock_llm_router):
    """Test agentic retrieval with query decomposition"""
    from rag_service import SemanticSearchService, QueryDecomposer, AgenticRetriever
    
    search_service = SemanticSearchService(
        vector_store=mock_vector_store,
        embedding_generator=mock_embedding_generator
    )
    
    query_decomposer = QueryDecomposer(llm_router=mock_llm_router)
    
    retriever = AgenticRetriever(
        search_service=search_service,
        query_decomposer=query_decomposer
    )
    
    results, metadata = await retriever.retrieve(
        query="Explain transformers in NLP",
        limit=10,
        use_decomposition=True
    )
    
    assert isinstance(results, list)
    assert isinstance(metadata, dict)
    assert 'sub_queries' in metadata
    assert 'retrieval_time' in metadata
    assert 'total_candidates' in metadata


@pytest.mark.asyncio
async def test_agentic_retrieval_deduplication(mock_vector_store, mock_embedding_generator, mock_llm_router):
    """Test that agentic retrieval deduplicates results"""
    from rag_service import SemanticSearchService, QueryDecomposer, AgenticRetriever
    
    # Mock vector store to return duplicate results (synchronous)
    def mock_search_dup(*args, **kwargs):
        return [
            {
                'id': 'doc1_chunk1',
                'score': 0.95,
                'document_id': 'doc1',
                'chunk_id': 1,
                'text': 'Sample text',
                'page_number': 1,
                'section': 'Intro'
            }
        ]
    mock_vector_store.search = mock_search_dup
    
    search_service = SemanticSearchService(
        vector_store=mock_vector_store,
        embedding_generator=mock_embedding_generator
    )
    
    query_decomposer = QueryDecomposer(llm_router=mock_llm_router)
    
    retriever = AgenticRetriever(
        search_service=search_service,
        query_decomposer=query_decomposer
    )
    
    results, metadata = await retriever.retrieve(
        query="Test query",
        limit=10,
        use_decomposition=True
    )
    
    # Should deduplicate results from multiple sub-queries
    result_ids = [r['id'] for r in results]
    assert len(result_ids) == len(set(result_ids)), "Results should be deduplicated"


@pytest.mark.asyncio
async def test_voice_agent_rag_fast_cached(mock_vector_store, mock_embedding_generator, mock_llm_router, mock_redis):
    """Test VoiceAgentRAG fast retrieval with cache hit"""
    from rag_service import SemanticSearchService, QueryDecomposer, AgenticRetriever, VoiceAgentRAG
    import json
    
    # Mock cache hit
    cached_results = [
        {
            'id': 'doc1_chunk1',
            'score': 0.95,
            'document_id': 'doc1',
            'chunk_id': 1,
            'text': 'Cached result',
            'page_number': 1,
            'section': 'Intro'
        }
    ]
    mock_redis.get = Mock(return_value=json.dumps(cached_results))
    
    search_service = SemanticSearchService(
        vector_store=mock_vector_store,
        embedding_generator=mock_embedding_generator
    )
    
    query_decomposer = QueryDecomposer(llm_router=mock_llm_router)
    
    slow_retriever = AgenticRetriever(
        search_service=search_service,
        query_decomposer=query_decomposer
    )
    
    voice_rag = VoiceAgentRAG(
        fast_retriever=search_service,
        slow_retriever=slow_retriever,
        cache_client=mock_redis
    )
    
    results, from_cache, latency = await voice_rag.retrieve_fast(
        query="What are transformers?",
        limit=5
    )
    
    assert from_cache is True
    assert len(results) == 1
    assert latency < 1.0  # Should be very fast from cache


@pytest.mark.asyncio
async def test_voice_agent_rag_dual_low_confidence(mock_vector_store, mock_embedding_generator, mock_llm_router, mock_redis):
    """Test VoiceAgentRAG dual retrieval triggers slow agent on low confidence"""
    from rag_service import SemanticSearchService, QueryDecomposer, AgenticRetriever, VoiceAgentRAG
    
    # Mock low-confidence results (synchronous)
    def mock_search_low(*args, **kwargs):
        return [
            {
                'id': 'doc1_chunk1',
                'score': 0.5,  # Low score
                'document_id': 'doc1',
                'chunk_id': 1,
                'text': 'Low confidence result',
                'page_number': 1,
                'section': 'Intro'
            }
        ]
    mock_vector_store.search = mock_search_low
    
    search_service = SemanticSearchService(
        vector_store=mock_vector_store,
        embedding_generator=mock_embedding_generator
    )
    
    query_decomposer = QueryDecomposer(llm_router=mock_llm_router)
    
    slow_retriever = AgenticRetriever(
        search_service=search_service,
        query_decomposer=query_decomposer
    )
    
    voice_rag = VoiceAgentRAG(
        fast_retriever=search_service,
        slow_retriever=slow_retriever,
        cache_client=mock_redis
    )
    
    response = await voice_rag.retrieve_dual(
        query="What are transformers?",
        confidence_threshold=0.7
    )
    
    assert response['confidence'] < 0.7
    assert response['slow_triggered'] is True
    assert response['slow_results'] is not None


@pytest.mark.asyncio
async def test_voice_agent_rag_dual_high_confidence(mock_vector_store, mock_embedding_generator, mock_llm_router, mock_redis):
    """Test VoiceAgentRAG dual retrieval skips slow agent on high confidence"""
    from rag_service import SemanticSearchService, QueryDecomposer, AgenticRetriever, VoiceAgentRAG
    
    # Mock high-confidence results (synchronous)
    def mock_search_high(*args, **kwargs):
        return [
            {
                'id': 'doc1_chunk1',
                'score': 0.95,  # High score
                'document_id': 'doc1',
                'chunk_id': 1,
                'text': 'High confidence result',
                'page_number': 1,
                'section': 'Intro'
            }
        ]
    mock_vector_store.search = mock_search_high
    
    search_service = SemanticSearchService(
        vector_store=mock_vector_store,
        embedding_generator=mock_embedding_generator
    )
    
    query_decomposer = QueryDecomposer(llm_router=mock_llm_router)
    
    slow_retriever = AgenticRetriever(
        search_service=search_service,
        query_decomposer=query_decomposer
    )
    
    voice_rag = VoiceAgentRAG(
        fast_retriever=search_service,
        slow_retriever=slow_retriever,
        cache_client=mock_redis
    )
    
    response = await voice_rag.retrieve_dual(
        query="What are transformers?",
        confidence_threshold=0.7
    )
    
    assert response['confidence'] >= 0.7
    assert response['slow_triggered'] is False
    assert response['slow_results'] is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
