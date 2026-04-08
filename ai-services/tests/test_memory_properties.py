"""
Property-based tests for Memory System
Requirements: 39.11
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import datetime
import uuid
from unittest.mock import Mock, patch, MagicMock
from qdrant_client.models import PointStruct, ScoredPoint

from memory_service import (
    ShortTermMemory,
    LongTermMemory,
    EpisodicMemory,
    MemoryRouter,
    MemorySystem
)


# Fixtures for mocking Qdrant

@pytest.fixture
def mock_qdrant_client():
    """Mock Qdrant client for testing without actual Qdrant connection"""
    client = MagicMock()
    
    # Mock collections
    mock_collections = MagicMock()
    mock_collections.collections = []
    client.get_collections.return_value = mock_collections
    
    # Mock create collection
    client.create_collection.return_value = True
    
    # Mock upsert
    client.upsert.return_value = True
    
    # Mock search - return empty results by default
    client.search.return_value = []
    
    # Mock scroll - return empty results by default
    client.scroll.return_value = ([], None)
    
    # Mock delete
    client.delete.return_value = True
    
    return client


@pytest.fixture
def mock_embedder():
    """Mock embedding generator"""
    embedder = MagicMock()
    embedder.get_embedding_dimension.return_value = 384
    embedder.generate_embedding.return_value = [0.1] * 384
    return embedder


# Test strategies

@st.composite
def user_id_strategy(draw):
    """Generate valid user IDs"""
    return f"user_{draw(st.integers(min_value=1, max_value=1000))}"


@st.composite
def session_id_strategy(draw):
    """Generate valid session IDs"""
    return f"session_{draw(st.uuids())}"


@st.composite
def project_id_strategy(draw):
    """Generate valid project IDs"""
    return f"project_{draw(st.integers(min_value=1, max_value=100))}"


@st.composite
def message_strategy(draw):
    """Generate valid message content"""
    return draw(st.text(min_size=10, max_size=500, alphabet=st.characters(blacklist_categories=('Cs',))))


@st.composite
def memory_content_strategy(draw):
    """Generate memory content with messages"""
    role = draw(st.sampled_from(["user", "assistant", "system"]))
    content = draw(message_strategy())
    return [{"role": role, "content": content}]


# Property 14: Memory Layer Consistency
# Validates: Requirements 39.11
# Test that reading after writing returns written value across all layers

@pytest.mark.property
class TestMemoryLayerConsistency:
    """
    Property 14: Memory Layer Consistency
    Validates: Requirements 39.11
    
    Test that reading after writing returns written value across all layers
    """
    
    @given(
        user_id=user_id_strategy(),
        session_id=session_id_strategy(),
        user_message=message_strategy(),
        assistant_message=message_strategy()
    )
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_short_term_memory_consistency(
        self,
        user_id,
        session_id,
        user_message,
        assistant_message,
        mock_qdrant_client,
        mock_embedder
    ):
        """
        Test that short-term memory returns what was written
        """
        # Mock Qdrant to return stored data
        stored_data = []
        
        def mock_upsert(collection_name, points):
            stored_data.extend(points)
            return True
        
        def mock_search(collection_name, query_vector, limit, query_filter):
            # Return stored points as search results
            results = []
            for point in stored_data:
                scored_point = MagicMock()
                scored_point.id = point.id
                scored_point.score = 0.95
                scored_point.payload = point.payload
                results.append(scored_point)
            return results[:limit]
        
        mock_qdrant_client.upsert.side_effect = mock_upsert
        mock_qdrant_client.search.side_effect = mock_search
        
        # Patch Qdrant and embedder
        with patch('memory_service.QdrantClient', return_value=mock_qdrant_client):
            with patch('memory_service.EmbeddingGenerator', return_value=mock_embedder):
                # Initialize short-term memory
                stm = ShortTermMemory()
                
                # Store conversation
                memory_id = stm.store_conversation_turn(
                    user_message=user_message,
                    assistant_message=assistant_message,
                    user_id=user_id,
                    session_id=session_id
                )
                
                # Verify memory was stored
                assert memory_id is not None
                
                # Retrieve recent context
                memories = stm.get_recent_context(
                    user_id=user_id,
                    session_id=session_id,
                    limit=10
                )
                
                # Property: Reading after writing returns written value
                assert len(memories) > 0, "Should retrieve at least one memory"
                
                # Find the stored memory
                found = False
                for memory in memories:
                    messages = memory.get("messages", [])
                    if any(user_message in msg.get("content", "") for msg in messages):
                        found = True
                        break
                
                assert found, "Should find the stored conversation in retrieved memories"

    
    @given(
        user_id=user_id_strategy(),
        project_id=project_id_strategy(),
        finding=message_strategy()
    )
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_long_term_memory_consistency(
        self,
        user_id,
        project_id,
        finding,
        mock_qdrant_client,
        mock_embedder
    ):
        """
        Test that long-term memory returns what was written
        """
        # Mock Qdrant to return stored data
        stored_data = []
        
        def mock_upsert(collection_name, points):
            stored_data.extend(points)
            return True
        
        def mock_search(collection_name, query_vector, limit, query_filter):
            results = []
            for point in stored_data:
                scored_point = MagicMock()
                scored_point.id = point.id
                scored_point.score = 0.95
                scored_point.payload = point.payload
                results.append(scored_point)
            return results[:limit]
        
        mock_qdrant_client.upsert.side_effect = mock_upsert
        mock_qdrant_client.search.side_effect = mock_search
        
        with patch('memory_service.QdrantClient', return_value=mock_qdrant_client):
            with patch('memory_service.EmbeddingGenerator', return_value=mock_embedder):
                # Initialize long-term memory
                ltm = LongTermMemory()
                
                # Store project finding
                memory_id = ltm.store_project_finding(
                    finding=finding,
                    user_id=user_id,
                    project_id=project_id,
                    finding_type="key_concept"
                )
                
                # Verify memory was stored
                assert memory_id is not None
                
                # Retrieve project context
                memories = ltm.get_project_context(
                    user_id=user_id,
                    project_id=project_id,
                    limit=10
                )
                
                # Property: Reading after writing returns written value
                assert len(memories) > 0, "Should retrieve at least one memory"
                
                # Find the stored memory
                found = False
                for memory in memories:
                    messages = memory.get("messages", [])
                    if any(finding in msg.get("content", "") for msg in messages):
                        found = True
                        break
                
                assert found, "Should find the stored finding in retrieved memories"
    
    @given(
        user_id=user_id_strategy(),
        preference_type=st.sampled_from(["citation_style", "writing_style", "research_interest"]),
        preference_value=st.sampled_from(["APA", "MLA", "formal", "technical", "NLP", "ML"])
    )
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_episodic_memory_consistency(
        self,
        user_id,
        preference_type,
        preference_value,
        mock_qdrant_client,
        mock_embedder
    ):
        """
        Test that episodic memory returns what was written
        """
        # Mock Qdrant to return stored data
        stored_data = []
        
        def mock_upsert(collection_name, points):
            stored_data.extend(points)
            return True
        
        def mock_search(collection_name, query_vector, limit, query_filter):
            results = []
            for point in stored_data:
                scored_point = MagicMock()
                scored_point.id = point.id
                scored_point.score = 0.95
                scored_point.payload = point.payload
                results.append(scored_point)
            return results[:limit]
        
        mock_qdrant_client.upsert.side_effect = mock_upsert
        mock_qdrant_client.search.side_effect = mock_search
        
        with patch('memory_service.QdrantClient', return_value=mock_qdrant_client):
            with patch('memory_service.EmbeddingGenerator', return_value=mock_embedder):
                # Initialize episodic memory
                em = EpisodicMemory()
                
                # Store user preference
                memory_id = em.store_user_preference(
                    preference_type=preference_type,
                    preference_value=preference_value,
                    user_id=user_id
                )
                
                # Verify memory was stored
                assert memory_id is not None
                
                # Retrieve user preferences
                memories = em.get_user_preferences(
                    user_id=user_id,
                    preference_type=preference_type
                )
                
                # Property: Reading after writing returns written value
                assert len(memories) > 0, "Should retrieve at least one memory"
                
                # Find the stored preference
                found = False
                for memory in memories:
                    metadata = memory.get("metadata", {})
                    if (metadata.get("preference_type") == preference_type and
                        metadata.get("preference_value") == preference_value):
                        found = True
                        break
                
                assert found, "Should find the stored preference in retrieved memories"



# Property 22: Memory Layer Routing Accuracy
# Validates: Requirements 39.11
# Test that preference queries retrieve from episodic layer with 80% accuracy

@pytest.mark.property
class TestMemoryLayerRoutingAccuracy:
    """
    Property 22: Memory Layer Routing Accuracy
    Validates: Requirements 39.11
    
    Test that preference queries retrieve from episodic layer with 80% accuracy
    """
    
    @given(
        user_id=user_id_strategy(),
        session_id=session_id_strategy(),
        project_id=project_id_strategy()
    )
    @settings(
        max_examples=20,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_preference_query_routing_accuracy(
        self,
        user_id,
        session_id,
        project_id,
        mock_qdrant_client,
        mock_embedder
    ):
        """
        Test that preference queries are routed to episodic layer
        """
        # Mock Qdrant
        stored_data = {}
        
        def mock_upsert(collection_name, points):
            if collection_name not in stored_data:
                stored_data[collection_name] = []
            stored_data[collection_name].extend(points)
            return True
        
        def mock_search(collection_name, query_vector, limit, query_filter):
            results = []
            if collection_name in stored_data:
                for point in stored_data[collection_name]:
                    scored_point = MagicMock()
                    scored_point.id = point.id
                    scored_point.score = 0.95
                    scored_point.payload = point.payload
                    results.append(scored_point)
            return results[:limit]
        
        mock_qdrant_client.upsert.side_effect = mock_upsert
        mock_qdrant_client.search.side_effect = mock_search
        
        with patch('memory_service.QdrantClient', return_value=mock_qdrant_client):
            with patch('memory_service.EmbeddingGenerator', return_value=mock_embedder):
                # Initialize memory system
                stm = ShortTermMemory()
                ltm = LongTermMemory()
                em = EpisodicMemory()
                router = MemoryRouter(stm, ltm, em)
                
                # Store preferences in episodic memory
                preference_queries = [
                    ("citation_style", "APA", "What citation style do I prefer?"),
                    ("writing_style", "formal", "What writing style do I like?"),
                    ("research_interest", "NLP", "What are my research interests?")
                ]
                
                for pref_type, pref_value, query in preference_queries:
                    # Store preference
                    em.store_user_preference(
                        preference_type=pref_type,
                        preference_value=pref_value,
                        user_id=user_id
                    )
                    
                    # Route query
                    context = {
                        "session_id": session_id,
                        "project_id": project_id
                    }
                    
                    memories = router.route_query(query, user_id, context)
                    
                    # Property: Preference queries should retrieve from episodic layer
                    # Check if any retrieved memory is from episodic layer
                    has_episodic = False
                    for memory in memories:
                        metadata = memory.get("metadata", {})
                        if metadata.get("memory_type") == "user_preference":
                            has_episodic = True
                            break
                    
                    assert has_episodic, f"Preference query '{query}' should retrieve from episodic layer"
    
    @given(
        user_id=user_id_strategy(),
        session_id=session_id_strategy()
    )
    @settings(
        max_examples=20,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_recent_query_routing_accuracy(
        self,
        user_id,
        session_id,
        mock_qdrant_client,
        mock_embedder
    ):
        """
        Test that recent queries are routed to short-term layer
        """
        stored_data = {}
        
        def mock_upsert(collection_name, points):
            if collection_name not in stored_data:
                stored_data[collection_name] = []
            stored_data[collection_name].extend(points)
            return True
        
        def mock_search(collection_name, query_vector, limit, query_filter):
            results = []
            if collection_name in stored_data:
                for point in stored_data[collection_name]:
                    scored_point = MagicMock()
                    scored_point.id = point.id
                    scored_point.score = 0.95
                    scored_point.payload = point.payload
                    results.append(scored_point)
            return results[:limit]
        
        mock_qdrant_client.upsert.side_effect = mock_upsert
        mock_qdrant_client.search.side_effect = mock_search
        
        with patch('memory_service.QdrantClient', return_value=mock_qdrant_client):
            with patch('memory_service.EmbeddingGenerator', return_value=mock_embedder):
                # Initialize memory system
                stm = ShortTermMemory()
                ltm = LongTermMemory()
                em = EpisodicMemory()
                router = MemoryRouter(stm, ltm, em)
                
                # Store recent conversation in short-term memory
                stm.store_conversation_turn(
                    user_message="What is transformer architecture?",
                    assistant_message="Transformers use self-attention mechanism...",
                    user_id=user_id,
                    session_id=session_id
                )
                
                # Route recent query
                recent_queries = [
                    "What did we just discuss?",
                    "What was the last topic?",
                    "Tell me about the previous conversation"
                ]
                
                for query in recent_queries:
                    context = {"session_id": session_id}
                    memories = router.route_query(query, user_id, context)
                    
                    # Property: Recent queries should retrieve from short-term layer
                    has_short_term = False
                    for memory in memories:
                        metadata = memory.get("metadata", {})
                        if metadata.get("session_id") == session_id:
                            has_short_term = True
                            break
                    
                    assert has_short_term, f"Recent query '{query}' should retrieve from short-term layer"
    
    @given(
        user_id=user_id_strategy(),
        project_id=project_id_strategy()
    )
    @settings(
        max_examples=20,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_general_query_routing_accuracy(
        self,
        user_id,
        project_id,
        mock_qdrant_client,
        mock_embedder
    ):
        """
        Test that general queries retrieve from long-term layer
        """
        stored_data = {}
        
        def mock_upsert(collection_name, points):
            if collection_name not in stored_data:
                stored_data[collection_name] = []
            stored_data[collection_name].extend(points)
            return True
        
        def mock_search(collection_name, query_vector, limit, query_filter):
            results = []
            if collection_name in stored_data:
                for point in stored_data[collection_name]:
                    scored_point = MagicMock()
                    scored_point.id = point.id
                    scored_point.score = 0.95
                    scored_point.payload = point.payload
                    results.append(scored_point)
            return results[:limit]
        
        mock_qdrant_client.upsert.side_effect = mock_upsert
        mock_qdrant_client.search.side_effect = mock_search
        
        with patch('memory_service.QdrantClient', return_value=mock_qdrant_client):
            with patch('memory_service.EmbeddingGenerator', return_value=mock_embedder):
                # Initialize memory system
                stm = ShortTermMemory()
                ltm = LongTermMemory()
                em = EpisodicMemory()
                router = MemoryRouter(stm, ltm, em)
                
                # Store project finding in long-term memory
                ltm.store_project_finding(
                    finding="Transformers use self-attention mechanism for sequence modeling",
                    user_id=user_id,
                    project_id=project_id,
                    finding_type="key_concept"
                )
                
                # Route general query
                general_queries = [
                    "What are the key concepts in this project?",
                    "Tell me about transformer architecture",
                    "What research findings do we have?"
                ]
                
                for query in general_queries:
                    context = {"project_id": project_id}
                    memories = router.route_query(query, user_id, context)
                    
                    # Property: General queries should retrieve from long-term layer
                    has_long_term = False
                    for memory in memories:
                        metadata = memory.get("metadata", {})
                        if metadata.get("project_id") == project_id:
                            has_long_term = True
                            break
                    
                    assert has_long_term, f"General query '{query}' should retrieve from long-term layer"
    
    def test_query_classification_accuracy(self, mock_qdrant_client, mock_embedder):
        """
        Test that query classifier correctly identifies query types
        """
        with patch('memory_service.QdrantClient', return_value=mock_qdrant_client):
            with patch('memory_service.EmbeddingGenerator', return_value=mock_embedder):
                # Initialize router
                stm = ShortTermMemory()
                ltm = LongTermMemory()
                em = EpisodicMemory()
                router = MemoryRouter(stm, ltm, em)
                
                # Test preference queries
                preference_queries = [
                    "What citation style do I prefer?",
                    "What format do I like?",
                    "What writing style do I want?"
                ]
                
                for query in preference_queries:
                    query_type = router.classify_query(query)
                    assert query_type == "preference", f"Query '{query}' should be classified as preference"
                
                # Test recent queries
                recent_queries = [
                    "What did we discuss recently?",
                    "What was the last topic?",
                    "Tell me about the previous conversation"
                ]
                
                for query in recent_queries:
                    query_type = router.classify_query(query)
                    assert query_type == "recent", f"Query '{query}' should be classified as recent"
                
                # Test general queries
                general_queries = [
                    "What are transformers?",
                    "Explain attention mechanism",
                    "Summarize the research findings"
                ]
                
                for query in general_queries:
                    query_type = router.classify_query(query)
                    assert query_type == "general", f"Query '{query}' should be classified as general"
