"""
Chat API endpoints for RAG queries
Requirements: 4.1, 4.2, 4.3, 4.6
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
import json
import asyncio

from rag_service import RAGService
from memory_service import MemoryRouter, ShortTermMemory, LongTermMemory, EpisodicMemory
from config import settings
import redis

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/rag", tags=["rag"])

# Initialize services
redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    decode_responses=True
)

rag_service = RAGService(cache_client=redis_client)

# Initialize memory system
stm = ShortTermMemory()
ltm = LongTermMemory()
em = EpisodicMemory()
memory_router = MemoryRouter(stm, ltm, em)


class RAGQueryRequest(BaseModel):
    query: str
    project_id: str
    document_ids: Optional[List[str]] = None
    use_voice_rag: bool = False
    verify_citations: bool = True
    session_id: Optional[str] = None
    user_id: Optional[str] = None


class RAGQueryResponse(BaseModel):
    query: str
    response: str
    citations: List[Dict[str, Any]]
    verification: Optional[Dict[str, Any]] = None
    retrieval_metadata: Dict[str, Any]
    model: str
    total_time: float
    input_tokens: int
    output_tokens: int
    cost: float


@router.post("/query", response_model=RAGQueryResponse)
async def rag_query(request: RAGQueryRequest):
    """
    Execute RAG query with retrieval and generation
    Requirements: 4.1, 4.2, 4.3
    """
    try:
        logger.info(f"RAG query: {request.query[:50]}... (project: {request.project_id})")
        
        # Load conversation context from memory if session_id provided
        conversation_context = []
        if request.session_id and request.user_id:
            memories = memory_router.route_query(
                query=request.query,
                user_id=request.user_id,
                context={
                    'session_id': request.session_id,
                    'project_id': request.project_id
                }
            )
            conversation_context = memories[:5]  # Last 5 relevant memories
        
        # Execute RAG query
        result = await rag_service.query(
            query=request.query,
            project_id=request.project_id,
            use_voice_rag=request.use_voice_rag,
            verify_citations=request.verify_citations
        )
        
        # Store in short-term memory if session provided
        if request.session_id and request.user_id:
            stm.store_conversation_turn(
                user_message=request.query,
                assistant_message=result['response'],
                user_id=request.user_id,
                session_id=request.session_id,
                document_context=request.document_ids
            )
        
        return RAGQueryResponse(**result)
        
    except Exception as e:
        logger.error(f"RAG query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query/stream")
async def rag_query_stream(request: RAGQueryRequest):
    """
    Execute RAG query with streaming response
    Requirements: 4.6
    """
    try:
        logger.info(f"RAG streaming query: {request.query[:50]}... (project: {request.project_id})")
        
        async def generate_stream():
            """Generate streaming response"""
            try:
                # Load conversation context from memory
                conversation_context = []
                if request.session_id and request.user_id:
                    memories = memory_router.route_query(
                        query=request.query,
                        user_id=request.user_id,
                        context={
                            'session_id': request.session_id,
                            'project_id': request.project_id
                        }
                    )
                    conversation_context = memories[:5]
                
                # Step 1: Retrieval (send immediately)
                yield json.dumps({
                    'type': 'status',
                    'message': 'Retrieving relevant documents...'
                }) + '\n'
                
                # Execute retrieval
                if request.use_voice_rag and rag_service.voice_rag:
                    retrieval_result = await rag_service.voice_rag.retrieve_dual(
                        query=request.query,
                        project_id=request.project_id
                    )
                    retrieved_docs = (
                        retrieval_result.get('slow_results') or
                        retrieval_result['fast_results']
                    )
                    retrieval_metadata = {
                        'method': 'voice_rag',
                        'fast_latency': retrieval_result['fast_latency'],
                        'confidence': retrieval_result['confidence']
                    }
                else:
                    retrieved_docs, retrieval_metadata = await rag_service.agentic_retriever.retrieve(
                        query=request.query,
                        project_id=request.project_id,
                        limit=10
                    )
                    retrieval_metadata['method'] = 'agentic'
                
                # Send retrieval complete
                yield json.dumps({
                    'type': 'retrieval_complete',
                    'document_count': len(retrieved_docs),
                    'metadata': retrieval_metadata
                }) + '\n'
                
                # Step 2: Generate response with streaming
                yield json.dumps({
                    'type': 'status',
                    'message': 'Generating response...'
                }) + '\n'
                
                # For now, generate full response (streaming LLM tokens requires LiteLLM streaming support)
                generation_result = await rag_service.response_generator.generate_response(
                    query=request.query,
                    retrieved_docs=retrieved_docs
                )
                
                # Stream response in chunks
                response_text = generation_result['response']
                chunk_size = 50  # Characters per chunk
                
                for i in range(0, len(response_text), chunk_size):
                    chunk = response_text[i:i+chunk_size]
                    yield json.dumps({
                        'type': 'token',
                        'content': chunk
                    }) + '\n'
                    await asyncio.sleep(0.05)  # Simulate streaming delay
                
                # Step 3: Send citations
                if generation_result['citations']:
                    yield json.dumps({
                        'type': 'citations',
                        'citations': generation_result['citations']
                    }) + '\n'
                
                # Step 4: Citation verification (if requested)
                if request.verify_citations and generation_result['citations']:
                    yield json.dumps({
                        'type': 'status',
                        'message': 'Verifying citations...'
                    }) + '\n'
                    
                    verification_result = await rag_service.citation_verifier.verify_citations(
                        response_text=generation_result['response'],
                        citations=generation_result['citations']
                    )
                    
                    yield json.dumps({
                        'type': 'verification',
                        'verification': verification_result
                    }) + '\n'
                
                # Step 5: Send completion
                yield json.dumps({
                    'type': 'complete',
                    'model': generation_result['model'],
                    'input_tokens': generation_result['input_tokens'],
                    'output_tokens': generation_result['output_tokens'],
                    'cost': generation_result['cost']
                }) + '\n'
                
                # Store in memory
                if request.session_id and request.user_id:
                    stm.store_conversation_turn(
                        user_message=request.query,
                        assistant_message=response_text,
                        user_id=request.user_id,
                        session_id=request.session_id,
                        document_context=request.document_ids
                    )
                
            except Exception as e:
                logger.error(f"Streaming error: {e}")
                yield json.dumps({
                    'type': 'error',
                    'error': str(e)
                }) + '\n'
        
        return StreamingResponse(
            generate_stream(),
            media_type='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no'
            }
        )
        
    except Exception as e:
        logger.error(f"RAG streaming query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'service': 'rag',
        'version': '1.0.0'
    }
