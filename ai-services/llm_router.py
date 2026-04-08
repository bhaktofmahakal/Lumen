"""
LLM Router with LiteLLM for intelligent multi-provider routing
Implements cost optimization and automatic fallback across Gemini, Groq, and Ollama
"""

import os
import hashlib
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import tiktoken
from litellm import Router, completion
from config import settings
import redis

logger = logging.getLogger(__name__)


class QueryComplexityAnalyzer:
    """Analyze query complexity to route to appropriate LLM provider"""
    
    def __init__(self):
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
    
    def analyze_complexity(self, query: str, context: Optional[Dict] = None) -> str:
        """
        Classify query complexity: simple, medium, or complex
        
        Args:
            query: User query text
            context: Optional context with document_count, has_images, etc.
            
        Returns:
            Complexity level: "simple", "medium", or "complex"
        """
        if context is None:
            context = {}
        
        # Token count
        token_count = len(self.tokenizer.encode(query))
        
        # Document count
        doc_count = context.get("document_count", 0)
        
        # Multimodal content
        has_images = context.get("has_images", False)
        
        # Calculate complexity score
        score = 0
        
        if token_count > 500:
            score += 2
        elif token_count > 100:
            score += 1
        
        if doc_count > 10:
            score += 2
        elif doc_count > 3:
            score += 1
        
        if has_images:
            score += 2
        
        # Classify
        if score >= 4:
            return "complex"
        elif score >= 1:
            return "medium"
        else:
            return "simple"


class LLMCache:
    """Redis-based caching layer for LLM responses"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.ttl = 3600  # 1 hour TTL
    
    def get_cache_key(self, query: str, model: str) -> str:
        """Generate cache key from query and model"""
        content = f"{model}:{query}"
        return f"llm_cache:{hashlib.md5(content.encode()).hexdigest()}"
    
    def get(self, query: str, model: str) -> Optional[Dict]:
        """Get cached response"""
        key = self.get_cache_key(query, model)
        cached = self.redis.get(key)
        if cached:
            logger.info(f"Cache hit for query: {query[:50]}...")
            return json.loads(cached)
        return None
    
    def set(self, query: str, model: str, response: Dict):
        """Cache response with TTL"""
        key = self.get_cache_key(query, model)
        self.redis.setex(key, self.ttl, json.dumps(response))
        logger.info(f"Cached response for query: {query[:50]}...")


class CostTracker:
    """Track token usage and costs per provider"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        
        # Cost per 1M tokens (as of 2025)
        self.costs = {
            "groq-fast": {"input": 0.05, "output": 0.10},
            "gemini-balanced": {"input": 0.075, "output": 0.15},
            "gemini-quality": {"input": 0.35, "output": 0.70},
            "ollama-local": {"input": 0.0, "output": 0.0}
        }
    
    def track_usage(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """
        Track token usage and calculate cost
        
        Args:
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Total cost in USD
        """
        # Calculate cost
        input_cost = (input_tokens / 1_000_000) * self.costs[model]["input"]
        output_cost = (output_tokens / 1_000_000) * self.costs[model]["output"]
        total_cost = input_cost + output_cost
        
        # Store in Redis
        date_key = datetime.now().strftime("%Y-%m-%d")
        self.redis.hincrby(f"llm_usage:{date_key}", f"{model}:tokens", input_tokens + output_tokens)
        self.redis.hincrbyfloat(f"llm_usage:{date_key}", f"{model}:cost", total_cost)
        
        logger.info(f"Tracked usage: {model} - {input_tokens + output_tokens} tokens - ${total_cost:.4f}")
        
        return total_cost
    
    def get_daily_cost(self, date: str) -> Dict[str, float]:
        """Get cost breakdown for a specific date"""
        usage = self.redis.hgetall(f"llm_usage:{date}")
        return {
            k.decode(): float(v) for k, v in usage.items()
        }
    
    def get_monthly_cost(self, year: int, month: int) -> float:
        """Get total cost for a month"""
        total = 0.0
        for day in range(1, 32):
            try:
                date = f"{year}-{month:02d}-{day:02d}"
                daily = self.get_daily_cost(date)
                total += sum(v for k, v in daily.items() if k.endswith(":cost"))
            except:
                continue
        return total


class LLMRouter:
    """
    Intelligent LLM router using LiteLLM
    Routes queries to optimal provider based on complexity
    """
    
    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client
        self.cache = LLMCache(redis_client)
        self.cost_tracker = CostTracker(redis_client)
        self.complexity_analyzer = QueryComplexityAnalyzer()
        
        # Configure LiteLLM router
        self.router = self._configure_router()
    
    def _configure_router(self) -> Router:
        """Configure LiteLLM router with multiple providers"""
        
        model_list = []
        
        # Groq configuration (speed)
        if settings.GROQ_API_KEY:
            model_list.append({
                "model_name": "groq-fast",
                "litellm_params": {
                    "model": "groq/llama3-8b-8192",
                    "api_key": settings.GROQ_API_KEY,
                    "rpm": 30,  # Requests per minute
                    "tpm": 100000  # Tokens per minute
                }
            })
        
        # Gemini Flash configuration (balanced)
        if settings.GEMINI_API_KEY:
            model_list.append({
                "model_name": "gemini-balanced",
                "litellm_params": {
                    "model": "gemini/gemini-1.5-flash",
                    "api_key": settings.GEMINI_API_KEY,
                    "rpm": 15,
                    "tpm": 1000000
                }
            })
            
            # Gemini Pro configuration (quality)
            model_list.append({
                "model_name": "gemini-quality",
                "litellm_params": {
                    "model": "gemini/gemini-1.5-pro",
                    "api_key": settings.GEMINI_API_KEY,
                    "rpm": 5,
                    "tpm": 500000
                }
            })
        
        # Ollama configuration (local/self-hosted)
        if settings.OLLAMA_HOST:
            model_list.append({
                "model_name": "ollama-local",
                "litellm_params": {
                    "model": "ollama/llama3",
                    "api_base": settings.OLLAMA_HOST,
                    "rpm": 1000,  # No rate limit for local
                    "tpm": 10000000
                }
            })
        
        # Configure fallback chains
        fallbacks = []
        if settings.GROQ_API_KEY and settings.GEMINI_API_KEY:
            fallbacks.append({"groq-fast": ["gemini-balanced"]})
            fallbacks.append({"gemini-balanced": ["groq-fast"]})
            fallbacks.append({"gemini-quality": ["gemini-balanced", "groq-fast"]})
        
        if settings.OLLAMA_HOST:
            fallbacks.append({"ollama-local": ["groq-fast"]})
        
        logger.info(f"Configured LiteLLM router with {len(model_list)} providers")
        
        return Router(
            model_list=model_list,
            routing_strategy="usage-based-routing",  # Balance load across providers
            fallbacks=fallbacks if fallbacks else None
        )
    
    def route_query(self, query: str, context: Optional[Dict] = None) -> str:
        """
        Route query to optimal model based on complexity
        
        Args:
            query: User query
            context: Optional context with document_count, has_images, etc.
            
        Returns:
            Model name to use
        """
        if context is None:
            context = {}
        
        # Check if self-hosted mode is preferred
        if context.get("self_hosted", False) and settings.OLLAMA_HOST:
            return "ollama-local"
        
        # Analyze complexity
        complexity = self.complexity_analyzer.analyze_complexity(query, context)
        
        # Select model based on complexity
        model_map = {
            "simple": "groq-fast",
            "medium": "gemini-balanced",
            "complex": "gemini-quality"
        }
        
        model = model_map.get(complexity, "gemini-balanced")
        logger.info(f"Routed query (complexity: {complexity}) to {model}")
        
        return model
    
    async def complete(
        self,
        query: str,
        context: Optional[Dict] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Generate completion with automatic routing and caching
        
        Args:
            query: User query
            context: Optional context for routing
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            use_cache: Whether to use caching
            
        Returns:
            Response dict with content, model, tokens, cost
        """
        # Route to optimal model
        model = self.route_query(query, context)
        
        # Check cache
        if use_cache:
            cached = self.cache.get(query, model)
            if cached:
                return cached
        
        # Make completion
        try:
            response = self.router.completion(
                model=model,
                messages=[{"role": "user", "content": query}],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Extract response data
            content = response.choices[0].message.content
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            
            # Track cost
            cost = self.cost_tracker.track_usage(model, input_tokens, output_tokens)
            
            # Prepare result
            result = {
                "content": content,
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "cost": cost,
                "cached": False
            }
            
            # Cache result
            if use_cache:
                self.cache.set(query, model, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in LLM completion: {e}")
            raise
    
    def get_usage_stats(self, date: Optional[str] = None) -> Dict[str, Any]:
        """
        Get usage statistics for a specific date
        
        Args:
            date: Date in YYYY-MM-DD format (defaults to today)
            
        Returns:
            Usage statistics dict
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        return self.cost_tracker.get_daily_cost(date)
