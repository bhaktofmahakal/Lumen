"""
RAG 2.0 System with LlamaIndex and Qdrant
Implements semantic search, query decomposition, agentic retrieval, and VoiceAgentRAG pattern
Requirements: 2.1, 2.2, 3.1, 3.2, 3.3, 4.1, 4.2, 4.5, 18.3
"""

import logging
import time
from typing import List, Dict, Optional, Any, Tuple
import asyncio
from datetime import datetime
from pydantic import BaseModel

from vector_store import QdrantVectorStore
from embeddings import EmbeddingGenerator
from llm_router import LLMRouter
from config import settings

logger = logging.getLogger(__name__)


class SemanticSearchResult(BaseModel):
    """Result from semantic search"""
    document_id: str
    chunk_id: int
    text: str
    score: float
    page_number: Optional[int] = None
    section: Optional[str] = None
    metadata: Dict[str, Any] = {}


class SemanticSearchService:
    """
    Semantic search service using Qdrant vector store
    Requirements: 2.1, 2.2
    """
    
    def __init__(
        self,
        vector_store: Optional[QdrantVectorStore] = None,
        embedding_generator: Optional[EmbeddingGenerator] = None
    ):
        """
        Initialize semantic search service
        
        Args:
            vector_store: Qdrant vector store instance
            embedding_generator: Embedding generator instance
        """
        self.vector_store = vector_store or QdrantVectorStore()
        self.embedding_generator = embedding_generator or EmbeddingGenerator()
    
    async def search(
        self,
        query: str,
        project_id: Optional[str] = None,
        document_ids: Optional[List[str]] = None,
        limit: int = 10,
        score_threshold: float = 0.0,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search across documents
        Requirements: 2.1, 2.2
        
        Args:
            query: Search query text
            project_id: Optional project ID to filter results
            document_ids: Optional list of document IDs to search within
            limit: Maximum number of results (default: 10)
            score_threshold: Minimum similarity score (0-1, default: 0.0)
            filters: Optional additional metadata filters
        
        Returns:
            List of search results with text, metadata, and similarity scores
            Results are ranked by similarity score in descending order
        """
        if not query or not query.strip():
            logger.warning("Empty query provided for semantic search")
            return []
        
        try:
            start_time = time.time()
            
            # Generate query embedding
            logger.info(f"Generating embedding for query: {query[:50]}...")
            query_embedding = self.embedding_generator.generate_embedding(query)
            
            # Build filter conditions
            filter_conditions = filters or {}
            
            if project_id:
                filter_conditions['project_id'] = project_id
            
            if document_ids:
                # For multiple document IDs, we'll need to search each separately
                # and merge results (Qdrant doesn't support OR on same field)
                if len(document_ids) == 1:
                    filter_conditions['document_id'] = document_ids[0]
                else:
                    # Search without document filter and filter in post-processing
                    pass
            
            # Perform search
            logger.info(f"Searching Qdrant with limit={limit}, threshold={score_threshold}")
            results = await asyncio.to_thread(
                self.vector_store.search,
                query_embedding=query_embedding,
                limit=limit * 2 if document_ids and len(document_ids) > 1 else limit,
                score_threshold=score_threshold,
                filter_conditions=filter_conditions if filter_conditions else None
            )
            
            # Post-filter by document IDs if needed
            if document_ids and len(document_ids) > 1:
                results = [
                    r for r in results
                    if r.get('document_id') in document_ids
                ][:limit]
            
            # Ensure results are sorted by score descending
            results = sorted(results, key=lambda x: x['score'], reverse=True)
            
            elapsed = time.time() - start_time
            logger.info(
                f"Semantic search completed in {elapsed:.2f}s, "
                f"returned {len(results)} results"
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            raise
    
    async def search_with_reranking(
        self,
        query: str,
        project_id: Optional[str] = None,
        limit: int = 10,
        rerank_top_k: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search with reranking for improved relevance
        Requirements: 4.2
        
        Args:
            query: Search query
            project_id: Optional project ID filter
            limit: Final number of results
            rerank_top_k: Number of candidates to retrieve before reranking
        
        Returns:
            Reranked search results
        """
        # First pass: retrieve more candidates
        candidates = await self.search(
            query=query,
            project_id=project_id,
            limit=rerank_top_k,
            score_threshold=0.0
        )
        
        if not candidates:
            return []
        
        # For now, return top results (reranking with cross-encoder can be added later)
        # This is a placeholder for future enhancement
        return candidates[:limit]


class QueryDecomposer:
    """
    Decompose complex queries into sub-queries
    Requirements: 4.1
    """
    
    def __init__(self, llm_router: LLMRouter):
        """
        Initialize query decomposer
        
        Args:
            llm_router: LLM router for query decomposition
        """
        self.llm_router = llm_router
    
    async def decompose_query(
        self,
        query: str,
        max_sub_queries: int = 3
    ) -> List[str]:
        """
        Decompose complex query into 2-3 sub-queries
        Requirements: 4.1
        
        Args:
            query: Complex query to decompose
            max_sub_queries: Maximum number of sub-queries (default: 3)
        
        Returns:
            List of sub-queries
        """
        try:
            # Check if query is simple enough (no decomposition needed)
            if len(query.split()) < 10:
                logger.info("Query is simple, no decomposition needed")
                return [query]
            
            # Use LLM to decompose query
            prompt = f"""Decompose the following research query into {max_sub_queries} simpler sub-queries that can be answered independently.

Query: {query}

Return ONLY the sub-queries, one per line, without numbering or explanation.
Each sub-query should be a complete, standalone question."""
            
            response = await self.llm_router.complete(
                query=prompt,
                context={"document_count": 0},
                temperature=0.3,
                max_tokens=200,
                use_cache=True
            )
            
            # Parse sub-queries from response
            content = response['content'].strip()
            sub_queries = [
                line.strip()
                for line in content.split('\n')
                if line.strip() and not line.strip().startswith('#')
            ]
            
            # Limit to max_sub_queries
            sub_queries = sub_queries[:max_sub_queries]
            
            # Fallback to original query if decomposition failed
            if not sub_queries:
                logger.warning("Query decomposition failed, using original query")
                return [query]
            
            logger.info(f"Decomposed query into {len(sub_queries)} sub-queries")
            return sub_queries
            
        except Exception as e:
            logger.error(f"Error decomposing query: {e}")
            # Fallback to original query
            return [query]


class AgenticRetriever:
    """
    Agentic retrieval with query planning, decomposition, and verification
    Requirements: 4.1, 4.2
    """
    
    def __init__(
        self,
        search_service: SemanticSearchService,
        query_decomposer: QueryDecomposer
    ):
        """
        Initialize agentic retriever
        
        Args:
            search_service: Semantic search service
            query_decomposer: Query decomposer
        """
        self.search_service = search_service
        self.query_decomposer = query_decomposer
    
    async def retrieve(
        self,
        query: str,
        project_id: Optional[str] = None,
        limit: int = 10,
        use_decomposition: bool = True
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Retrieve documents using agentic approach
        Requirements: 4.1, 4.2
        
        Args:
            query: User query
            project_id: Optional project ID filter
            limit: Maximum results per sub-query
            use_decomposition: Whether to decompose complex queries
        
        Returns:
            Tuple of (results, metadata)
            - results: List of retrieved documents
            - metadata: Retrieval metadata (sub_queries, timing, etc.)
        """
        start_time = time.time()
        metadata = {
            'original_query': query,
            'sub_queries': [],
            'decomposition_used': False,
            'total_candidates': 0,
            'final_results': 0
        }
        
        try:
            # Step 1: Query planning and decomposition
            if use_decomposition:
                sub_queries = await self.query_decomposer.decompose_query(query)
                metadata['sub_queries'] = sub_queries
                metadata['decomposition_used'] = len(sub_queries) > 1
            else:
                sub_queries = [query]
            
            # Step 2: Parallel retrieval for sub-queries
            logger.info(f"Executing {len(sub_queries)} sub-queries in parallel")
            
            search_tasks = [
                self.search_service.search(
                    query=sub_query,
                    project_id=project_id,
                    limit=limit,
                    score_threshold=0.3  # Filter low-quality results
                )
                for sub_query in sub_queries
            ]
            
            sub_results = await asyncio.gather(*search_tasks)
            
            # Step 3: Merge and deduplicate results
            all_results = []
            seen_ids = set()
            
            for results in sub_results:
                for result in results:
                    # Create unique ID from document_id and chunk_id
                    result_id = f"{result['document_id']}_{result['chunk_id']}"
                    
                    if result_id not in seen_ids:
                        seen_ids.add(result_id)
                        all_results.append(result)
            
            metadata['total_candidates'] = len(all_results)
            
            # Step 4: Rerank by score and limit
            all_results = sorted(all_results, key=lambda x: x['score'], reverse=True)
            final_results = all_results[:limit]
            
            metadata['final_results'] = len(final_results)
            metadata['retrieval_time'] = time.time() - start_time
            
            logger.info(
                f"Agentic retrieval completed: {len(final_results)} results "
                f"from {metadata['total_candidates']} candidates in "
                f"{metadata['retrieval_time']:.2f}s"
            )
            
            return final_results, metadata
            
        except Exception as e:
            logger.error(f"Error in agentic retrieval: {e}")
            raise


class VoiceAgentRAG:
    """
    Dual-agent RAG system for ultra-low latency
    Fast agent: prefetch and cache (<1s)
    Slow agent: comprehensive retrieval (2-5s)
    Requirements: 4.5, 18.3
    """
    
    def __init__(
        self,
        fast_retriever: SemanticSearchService,
        slow_retriever: AgenticRetriever,
        cache_client: Any  # Redis client
    ):
        """
        Initialize VoiceAgentRAG
        
        Args:
            fast_retriever: Fast semantic search service
            slow_retriever: Slow agentic retriever
            cache_client: Redis client for caching
        """
        self.fast_retriever = fast_retriever
        self.slow_retriever = slow_retriever
        self.cache = cache_client
        self.cache_ttl = 3600  # 1 hour
    
    def _get_cache_key(self, query: str, project_id: Optional[str]) -> str:
        """Generate cache key for query"""
        import hashlib
        content = f"{project_id}:{query}"
        return f"voicerag:{hashlib.md5(content.encode()).hexdigest()}"
    
    async def retrieve_fast(
        self,
        query: str,
        project_id: Optional[str] = None,
        limit: int = 5
    ) -> Tuple[List[Dict[str, Any]], bool, float]:
        """
        Fast retrieval with caching (<1s target)
        Requirements: 18.3
        
        Args:
            query: User query
            project_id: Optional project ID
            limit: Maximum results
        
        Returns:
            Tuple of (results, from_cache, latency)
        """
        start_time = time.time()
        
        # Check cache
        cache_key = self._get_cache_key(query, project_id)
        cached = self.cache.get(cache_key)
        
        if cached:
            import json
            results = json.loads(cached)
            latency = time.time() - start_time
            logger.info(f"Fast retrieval (cached): {latency:.3f}s")
            return results, True, latency
        
        # Fast search without decomposition
        results = await self.fast_retriever.search(
            query=query,
            project_id=project_id,
            limit=limit,
            score_threshold=0.4  # Higher threshold for fast results
        )
        
        # Cache results
        import json
        self.cache.setex(cache_key, self.cache_ttl, json.dumps(results))
        
        latency = time.time() - start_time
        logger.info(f"Fast retrieval (uncached): {latency:.3f}s")
        
        return results, False, latency
    
    async def retrieve_slow(
        self,
        query: str,
        project_id: Optional[str] = None,
        limit: int = 10
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any], float]:
        """
        Comprehensive retrieval with agentic approach (2-5s target)
        Requirements: 4.5
        
        Args:
            query: User query
            project_id: Optional project ID
            limit: Maximum results
        
        Returns:
            Tuple of (results, metadata, latency)
        """
        start_time = time.time()
        
        # Use agentic retrieval with decomposition
        results, metadata = await self.slow_retriever.retrieve(
            query=query,
            project_id=project_id,
            limit=limit,
            use_decomposition=True
        )
        
        latency = time.time() - start_time
        logger.info(f"Slow retrieval: {latency:.3f}s")
        
        return results, metadata, latency
    
    async def retrieve_dual(
        self,
        query: str,
        project_id: Optional[str] = None,
        confidence_threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        Dual-agent retrieval: return fast result immediately, update with slow result
        Requirements: 4.5, 18.3
        
        Args:
            query: User query
            project_id: Optional project ID
            confidence_threshold: Threshold for triggering slow agent (default: 0.7)
        
        Returns:
            Dict with fast_results, slow_results, and metadata
        """
        # Start both retrievals
        fast_task = self.retrieve_fast(query, project_id, limit=5)
        
        # Get fast results
        fast_results, from_cache, fast_latency = await fast_task
        
        # Calculate confidence from fast results
        confidence = 0.0
        if fast_results:
            # Confidence is average of top 3 scores
            top_scores = [r['score'] for r in fast_results[:3]]
            confidence = sum(top_scores) / len(top_scores) if top_scores else 0.0
        
        response = {
            'fast_results': fast_results,
            'fast_latency': fast_latency,
            'from_cache': from_cache,
            'confidence': confidence,
            'slow_triggered': False,
            'slow_results': None,
            'slow_latency': None
        }
        
        # Trigger slow agent if confidence is low
        if confidence < confidence_threshold:
            logger.info(
                f"Low confidence ({confidence:.2f} < {confidence_threshold}), "
                f"triggering slow agent"
            )
            response['slow_triggered'] = True
            
            slow_results, metadata, slow_latency = await self.retrieve_slow(
                query, project_id, limit=10
            )
            
            response['slow_results'] = slow_results
            response['slow_latency'] = slow_latency
            response['slow_metadata'] = metadata
        
        return response



class Citation(BaseModel):
    """Citation model"""
    document_id: str
    document_title: str
    authors: Optional[List[str]] = []
    page_number: Optional[int] = None
    section: Optional[str] = None
    text_excerpt: str
    inline_marker: str  # e.g., "[1]", "[Smith et al., 2023]"
    position_start: int  # Character position in response
    position_end: int


class ResponseGenerator:
    """
    Generate responses with citations using LiteLLM router
    Requirements: 3.1, 3.2, 3.3
    """
    
    def __init__(self, llm_router: LLMRouter):
        """
        Initialize response generator
        
        Args:
            llm_router: LLM router for response generation
        """
        self.llm_router = llm_router
    
    async def generate_response(
        self,
        query: str,
        retrieved_docs: List[Dict[str, Any]],
        citation_style: str = "numbered"
    ) -> Dict[str, Any]:
        """
        Generate response with citations
        Requirements: 3.1, 3.2, 3.3
        
        Args:
            query: User query
            retrieved_docs: Retrieved document chunks
            citation_style: Citation style (numbered, apa, mla)
        
        Returns:
            Dict with response text and citations
        """
        try:
            # Build context from retrieved documents
            context_parts = []
            for i, doc in enumerate(retrieved_docs[:10]):  # Limit to top 10
                context_parts.append(
                    f"[Source {i+1}] (Document: {doc.get('document_id', 'unknown')}, "
                    f"Page: {doc.get('page_number', 'N/A')})\n{doc['text']}\n"
                )
            
            context = "\n".join(context_parts)
            
            # Generate response with citations
            prompt = f"""Based on the following sources, answer the user's question. 
Include inline citations using [Source N] format after each statement.

Sources:
{context}

Question: {query}

Answer with citations:"""
            
            response = await self.llm_router.complete(
                query=prompt,
                context={"document_count": len(retrieved_docs)},
                temperature=0.3,
                max_tokens=1000,
                use_cache=True
            )
            
            # Extract citations from response
            citations = self._extract_citations(
                response['content'],
                retrieved_docs,
                citation_style
            )
            
            return {
                'response': response['content'],
                'citations': citations,
                'model': response['model'],
                'input_tokens': response['input_tokens'],
                'output_tokens': response['output_tokens'],
                'cost': response['cost']
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise
    
    def _extract_citations(
        self,
        response_text: str,
        retrieved_docs: List[Dict[str, Any]],
        citation_style: str
    ) -> List[Dict[str, Any]]:
        """
        Extract citations from response text
        Requirements: 3.2, 3.3
        
        Args:
            response_text: Generated response text
            retrieved_docs: Retrieved documents
            citation_style: Citation style
        
        Returns:
            List of citation objects
        """
        import re
        
        citations = []
        
        # Find all [Source N] markers
        pattern = r'\[Source (\d+)\]'
        matches = re.finditer(pattern, response_text)
        
        for match in matches:
            source_num = int(match.group(1))
            
            # Get corresponding document (1-indexed)
            if 0 < source_num <= len(retrieved_docs):
                doc = retrieved_docs[source_num - 1]
                
                citation = {
                    'document_id': doc.get('document_id', 'unknown'),
                    'document_title': doc.get('metadata', {}).get('title', 'Unknown'),
                    'authors': doc.get('metadata', {}).get('authors', []),
                    'page_number': doc.get('page_number'),
                    'section': doc.get('section'),
                    'text_excerpt': doc['text'][:200],  # First 200 chars
                    'inline_marker': f"[{source_num}]",
                    'position_start': match.start(),
                    'position_end': match.end()
                }
                
                citations.append(citation)
        
        return citations


class CitationVerifier:
    """
    Verify citations and perform fact-checking
    Requirements: 3.8, 3.9
    """
    
    def __init__(self, vector_store: QdrantVectorStore, embedding_generator: EmbeddingGenerator):
        """
        Initialize citation verifier
        
        Args:
            vector_store: Vector store for document lookup
            embedding_generator: Embedding generator
        """
        self.vector_store = vector_store
        self.embedding_generator = embedding_generator
    
    async def verify_citations(
        self,
        response_text: str,
        citations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Verify citations against source documents
        Requirements: 3.8, 3.9
        
        Args:
            response_text: Generated response text
            citations: List of citations
        
        Returns:
            Verification results with accuracy score and flagged issues
        """
        try:
            verification_results = {
                'total_citations': len(citations),
                'verified_citations': 0,
                'flagged_citations': [],
                'accuracy_score': 0.0
            }
            
            for citation in citations:
                # Extract statement associated with citation
                statement = self._extract_statement_for_citation(
                    response_text,
                    citation
                )
                
                # Verify statement against source document
                is_verified = await self._verify_statement(
                    statement,
                    citation
                )
                
                if is_verified:
                    verification_results['verified_citations'] += 1
                else:
                    verification_results['flagged_citations'].append({
                        'citation': citation,
                        'statement': statement,
                        'reason': 'Potential misattribution or unsupported claim'
                    })
            
            # Calculate accuracy score
            if verification_results['total_citations'] > 0:
                verification_results['accuracy_score'] = (
                    verification_results['verified_citations'] /
                    verification_results['total_citations']
                )
            
            logger.info(
                f"Citation verification: {verification_results['verified_citations']}/"
                f"{verification_results['total_citations']} verified, "
                f"accuracy: {verification_results['accuracy_score']:.2f}"
            )
            
            return verification_results
            
        except Exception as e:
            logger.error(f"Error verifying citations: {e}")
            raise
    
    def _extract_statement_for_citation(
        self,
        response_text: str,
        citation: Dict[str, Any]
    ) -> str:
        """Extract the statement associated with a citation"""
        # Get text around citation marker
        pos = citation['position_start']
        
        # Find sentence boundaries
        start = response_text.rfind('.', 0, pos) + 1
        end = response_text.find('.', pos)
        
        if start == 0:
            start = 0
        if end == -1:
            end = len(response_text)
        
        statement = response_text[start:end].strip()
        return statement
    
    async def _verify_statement(
        self,
        statement: str,
        citation: Dict[str, Any]
    ) -> bool:
        """
        Verify statement against cited source
        
        Args:
            statement: Statement to verify
            citation: Citation information
        
        Returns:
            True if verified, False if potential misattribution
        """
        try:
            # Generate embedding for statement
            statement_embedding = self.embedding_generator.generate_embedding(statement)
            
            # Search for similar content in cited document
            results = await asyncio.to_thread(
                self.vector_store.search,
                query_embedding=statement_embedding,
                limit=5,
                score_threshold=0.0,
                filter_conditions={'document_id': citation['document_id']}
            )
            
            # Check if any result has high similarity (>0.7)
            if results and results[0]['score'] > 0.7:
                return True
            
            # Check if statement appears in citation excerpt
            if statement.lower() in citation['text_excerpt'].lower():
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error verifying statement: {e}")
            return False


class RAGService:
    """
    Complete RAG service integrating all components
    Requirements: 2.1, 2.2, 3.1, 3.2, 3.3, 3.8, 3.9, 4.1, 4.2, 4.5, 18.2, 18.3
    """
    
    def __init__(
        self,
        vector_store: Optional[QdrantVectorStore] = None,
        embedding_generator: Optional[EmbeddingGenerator] = None,
        llm_router: Optional[LLMRouter] = None,
        cache_client: Optional[Any] = None
    ):
        """
        Initialize RAG service
        
        Args:
            vector_store: Qdrant vector store
            embedding_generator: Embedding generator
            llm_router: LLM router
            cache_client: Redis cache client
        """
        self.vector_store = vector_store or QdrantVectorStore()
        self.embedding_generator = embedding_generator or EmbeddingGenerator()
        self.llm_router = llm_router or LLMRouter()
        
        # Initialize components
        self.search_service = SemanticSearchService(
            self.vector_store,
            self.embedding_generator
        )
        
        self.query_decomposer = QueryDecomposer(self.llm_router)
        
        self.agentic_retriever = AgenticRetriever(
            self.search_service,
            self.query_decomposer
        )
        
        if cache_client:
            self.voice_rag = VoiceAgentRAG(
                self.search_service,
                self.agentic_retriever,
                cache_client
            )
        else:
            self.voice_rag = None
        
        self.response_generator = ResponseGenerator(self.llm_router)
        
        self.citation_verifier = CitationVerifier(
            self.vector_store,
            self.embedding_generator
        )
    
    async def query(
        self,
        query: str,
        project_id: Optional[str] = None,
        use_voice_rag: bool = False,
        verify_citations: bool = True
    ) -> Dict[str, Any]:
        """
        Complete RAG query with retrieval, generation, and verification
        Requirements: 2.1, 3.1, 3.8, 4.1, 4.5
        
        Args:
            query: User query
            project_id: Optional project ID filter
            use_voice_rag: Use VoiceAgentRAG for ultra-low latency
            verify_citations: Verify citations after generation
        
        Returns:
            Complete response with text, citations, and verification
        """
        start_time = time.time()
        
        try:
            # Step 1: Retrieval
            if use_voice_rag and self.voice_rag:
                retrieval_result = await self.voice_rag.retrieve_dual(
                    query=query,
                    project_id=project_id
                )
                
                # Use slow results if available, otherwise fast results
                retrieved_docs = (
                    retrieval_result.get('slow_results') or
                    retrieval_result['fast_results']
                )
                
                retrieval_metadata = {
                    'method': 'voice_rag',
                    'fast_latency': retrieval_result['fast_latency'],
                    'slow_latency': retrieval_result.get('slow_latency'),
                    'confidence': retrieval_result['confidence'],
                    'slow_triggered': retrieval_result['slow_triggered']
                }
            else:
                retrieved_docs, retrieval_metadata = await self.agentic_retriever.retrieve(
                    query=query,
                    project_id=project_id,
                    limit=10
                )
                retrieval_metadata['method'] = 'agentic'
            
            # Step 2: Response generation with citations
            generation_result = await self.response_generator.generate_response(
                query=query,
                retrieved_docs=retrieved_docs
            )
            
            # Step 3: Citation verification (optional)
            verification_result = None
            if verify_citations and generation_result['citations']:
                verification_result = await self.citation_verifier.verify_citations(
                    response_text=generation_result['response'],
                    citations=generation_result['citations']
                )
            
            total_time = time.time() - start_time
            
            return {
                'query': query,
                'response': generation_result['response'],
                'citations': generation_result['citations'],
                'verification': verification_result,
                'retrieval_metadata': retrieval_metadata,
                'model': generation_result['model'],
                'total_time': total_time,
                'input_tokens': generation_result['input_tokens'],
                'output_tokens': generation_result['output_tokens'],
                'cost': generation_result['cost']
            }
            
        except Exception as e:
            logger.error(f"Error in RAG query: {e}")
            raise
