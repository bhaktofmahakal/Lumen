"""
Unit tests for LLM Router
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from llm_router import (
    QueryComplexityAnalyzer,
    LLMCache,
    CostTracker,
    LLMRouter
)
import json


class TestQueryComplexityAnalyzer:
    """Test query complexity analysis"""
    
    def test_simple_query(self):
        """Test simple query classification"""
        analyzer = QueryComplexityAnalyzer()
        query = "What is the main finding?"
        complexity = analyzer.analyze_complexity(query)
        assert complexity == "simple"
    
    def test_medium_query(self):
        """Test medium complexity query"""
        analyzer = QueryComplexityAnalyzer()
        query = "Explain the methodology used in the study and compare it with previous approaches. " * 10
        complexity = analyzer.analyze_complexity(query)
        assert complexity in ["medium", "complex"]
    
    def test_complex_query_with_context(self):
        """Test complex query with multiple documents"""
        analyzer = QueryComplexityAnalyzer()
        query = "Compare the findings across all papers"
        context = {"document_count": 15, "has_images": True}
        complexity = analyzer.analyze_complexity(query, context)
        assert complexity == "complex"
    
    def test_medium_query_with_documents(self):
        """Test medium complexity with moderate document count"""
        analyzer = QueryComplexityAnalyzer()
        query = "What are the key findings?"
        context = {"document_count": 7}
        complexity = analyzer.analyze_complexity(query, context)
        assert complexity == "medium"


class TestLLMCache:
    """Test LLM caching layer"""
    
    @pytest.fixture
    def redis_mock(self):
        """Mock Redis client"""
        return Mock()
    
    @pytest.fixture
    def cache(self, redis_mock):
        """Create cache instance"""
        return LLMCache(redis_mock)
    
    def test_cache_key_generation(self, cache):
        """Test cache key generation"""
        key = cache.get_cache_key("test query", "groq-fast")
        assert key.startswith("llm_cache:")
        assert len(key) > 10
    
    def test_cache_miss(self, cache, redis_mock):
        """Test cache miss"""
        redis_mock.get.return_value = None
        result = cache.get("test query", "groq-fast")
        assert result is None
    
    def test_cache_hit(self, cache, redis_mock):
        """Test cache hit"""
        cached_data = {"content": "test response", "model": "groq-fast"}
        redis_mock.get.return_value = json.dumps(cached_data)
        result = cache.get("test query", "groq-fast")
        assert result == cached_data
    
    def test_cache_set(self, cache, redis_mock):
        """Test caching response"""
        response = {"content": "test response", "model": "groq-fast"}
        cache.set("test query", "groq-fast", response)
        redis_mock.setex.assert_called_once()
        args = redis_mock.setex.call_args[0]
        assert args[1] == 3600  # TTL


class TestCostTracker:
    """Test cost tracking"""
    
    @pytest.fixture
    def redis_mock(self):
        """Mock Redis client"""
        return Mock()
    
    @pytest.fixture
    def tracker(self, redis_mock):
        """Create cost tracker instance"""
        return CostTracker(redis_mock)
    
    def test_track_usage_groq(self, tracker, redis_mock):
        """Test tracking Groq usage"""
        cost = tracker.track_usage("groq-fast", 1000, 500)
        assert cost > 0
        assert redis_mock.hincrby.called
        assert redis_mock.hincrbyfloat.called
    
    def test_track_usage_gemini(self, tracker, redis_mock):
        """Test tracking Gemini usage"""
        cost = tracker.track_usage("gemini-quality", 1000, 500)
        assert cost > 0
        # Gemini Pro should be more expensive than Groq
        groq_cost = tracker.track_usage("groq-fast", 1000, 500)
        assert cost > groq_cost
    
    def test_track_usage_ollama_free(self, tracker, redis_mock):
        """Test tracking Ollama usage (should be free)"""
        cost = tracker.track_usage("ollama-local", 1000, 500)
        assert cost == 0.0
    
    def test_get_daily_cost(self, tracker, redis_mock):
        """Test getting daily cost"""
        redis_mock.hgetall.return_value = {
            b"groq-fast:tokens": b"10000",
            b"groq-fast:cost": b"0.15"
        }
        costs = tracker.get_daily_cost("2025-01-15")
        assert "groq-fast:cost" in costs
        assert costs["groq-fast:cost"] == 0.15


class TestLLMRouter:
    """Test LLM router"""
    
    @pytest.fixture
    def redis_mock(self):
        """Mock Redis client"""
        return Mock()
    
    @pytest.fixture
    def router(self, redis_mock):
        """Create router instance"""
        with patch('llm_router.Router'):
            return LLMRouter(redis_mock)
    
    def test_route_simple_query(self, router):
        """Test routing simple query to Groq"""
        model = router.route_query("What is the main finding?")
        assert model == "groq-fast"
    
    def test_route_complex_query(self, router):
        """Test routing complex query to Gemini Pro"""
        query = "Provide a comprehensive analysis of all methodologies" * 20
        context = {"document_count": 15, "has_images": True}
        model = router.route_query(query, context)
        assert model == "gemini-quality"
    
    def test_route_medium_query(self, router):
        """Test routing medium query to Gemini Flash"""
        query = "Compare the findings in these papers" * 10
        context = {"document_count": 7}
        model = router.route_query(query, context)
        assert model == "gemini-balanced"
    
    def test_route_self_hosted(self, router):
        """Test routing to Ollama when self-hosted is preferred"""
        context = {"self_hosted": True}
        model = router.route_query("Any query", context)
        assert model == "ollama-local"
    
    @pytest.mark.asyncio
    async def test_complete_with_cache_hit(self, router, redis_mock):
        """Test completion with cache hit"""
        cached_response = {
            "content": "cached response",
            "model": "groq-fast",
            "cached": True
        }
        router.cache.get = Mock(return_value=cached_response)
        
        result = await router.complete("test query")
        assert result == cached_response
        assert result["cached"] == True
    
    @pytest.mark.asyncio
    async def test_complete_with_cache_miss(self, router, redis_mock):
        """Test completion with cache miss"""
        router.cache.get = Mock(return_value=None)
        router.cache.set = Mock()
        
        # Mock LiteLLM response
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="test response"))]
        mock_response.usage = Mock(prompt_tokens=100, completion_tokens=50)
        router.router.completion = Mock(return_value=mock_response)
        
        result = await router.complete("test query", use_cache=True)
        
        assert result["content"] == "test response"
        assert result["input_tokens"] == 100
        assert result["output_tokens"] == 50
        assert result["cached"] == False
        router.cache.set.assert_called_once()
    
    def test_get_usage_stats(self, router, redis_mock):
        """Test getting usage statistics"""
        redis_mock.hgetall.return_value = {
            b"groq-fast:tokens": b"10000",
            b"groq-fast:cost": b"0.15"
        }
        stats = router.get_usage_stats("2025-01-15")
        assert "groq-fast:cost" in stats
