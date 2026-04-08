"""
Memory System API Endpoints
Requirements: 39.7, 39.8
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import logging

from memory_service import get_memory_system, MemorySystem

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/memory", tags=["memory"])


# Request/Response Models

class StoreConversationRequest(BaseModel):
    user_message: str
    assistant_message: str
    user_id: str
    session_id: str
    document_context: Optional[List[str]] = None


class StoreResearchFindingRequest(BaseModel):
    finding: str
    user_id: str
    session_id: str
    document_id: str
    source_page: Optional[int] = None


class StoreProjectFindingRequest(BaseModel):
    finding: str
    user_id: str
    project_id: str
    document_id: Optional[str] = None
    finding_type: str = "key_concept"


class StorePreferenceRequest(BaseModel):
    preference_type: str
    preference_value: Any
    user_id: str
    project_id: Optional[str] = None


class StoreFeedbackRequest(BaseModel):
    feedback_type: str
    feedback_content: str
    user_id: str
    context: Optional[Dict] = None


class RetrieveContextRequest(BaseModel):
    query: str
    user_id: str
    session_id: Optional[str] = None
    project_id: Optional[str] = None



class DeleteMemoryRequest(BaseModel):
    user_id: str
    memory_id: str
    layer: str  # stm, ltm, or em


# Dependency to get memory system
def get_memory() -> MemorySystem:
    return get_memory_system()


# Endpoints

@router.post("/conversation")
async def store_conversation(
    request: StoreConversationRequest,
    memory: MemorySystem = Depends(get_memory)
):
    """
    Store conversation turn in short-term memory
    Requirements: 39.1, 39.3
    """
    try:
        memory_id = memory.short_term.store_conversation_turn(
            user_message=request.user_message,
            assistant_message=request.assistant_message,
            user_id=request.user_id,
            session_id=request.session_id,
            document_context=request.document_context
        )
        
        return {
            "success": True,
            "memory_id": memory_id,
            "message": "Conversation stored in short-term memory"
        }
    except Exception as e:
        logger.error(f"Error storing conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/research-finding")
async def store_research_finding(
    request: StoreResearchFindingRequest,
    memory: MemorySystem = Depends(get_memory)
):
    """
    Store research finding in short-term memory
    Requirements: 39.1, 39.3
    """
    try:
        memory_id = memory.short_term.store_research_finding(
            finding=request.finding,
            user_id=request.user_id,
            session_id=request.session_id,
            document_id=request.document_id,
            source_page=request.source_page
        )
        
        return {
            "success": True,
            "memory_id": memory_id,
            "message": "Research finding stored in short-term memory"
        }
    except Exception as e:
        logger.error(f"Error storing research finding: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/project-finding")
async def store_project_finding(
    request: StoreProjectFindingRequest,
    memory: MemorySystem = Depends(get_memory)
):
    """
    Store project finding in long-term memory
    Requirements: 39.2, 39.5
    """
    try:
        memory_id = memory.long_term.store_project_finding(
            finding=request.finding,
            user_id=request.user_id,
            project_id=request.project_id,
            document_id=request.document_id,
            finding_type=request.finding_type
        )
        
        return {
            "success": True,
            "memory_id": memory_id,
            "message": "Project finding stored in long-term memory"
        }
    except Exception as e:
        logger.error(f"Error storing project finding: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/preference")
async def store_preference(
    request: StorePreferenceRequest,
    memory: MemorySystem = Depends(get_memory)
):
    """
    Store user preference
    Requirements: 39.2, 39.5
    """
    try:
        if request.project_id:
            # Project-specific preference (long-term memory)
            memory_id = memory.long_term.store_project_preference(
                preference_type=request.preference_type,
                preference_value=request.preference_value,
                user_id=request.user_id,
                project_id=request.project_id
            )
            layer = "long-term"
        else:
            # Global user preference (episodic memory)
            memory_id = memory.episodic.store_user_preference(
                preference_type=request.preference_type,
                preference_value=request.preference_value,
                user_id=request.user_id
            )
            layer = "episodic"
        
        return {
            "success": True,
            "memory_id": memory_id,
            "layer": layer,
            "message": f"Preference stored in {layer} memory"
        }
    except Exception as e:
        logger.error(f"Error storing preference: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback")
async def store_feedback(
    request: StoreFeedbackRequest,
    memory: MemorySystem = Depends(get_memory)
):
    """
    Store user feedback in episodic memory
    Requirements: 39.2, 39.5
    """
    try:
        memory_id = memory.episodic.store_feedback(
            feedback_type=request.feedback_type,
            feedback_content=request.feedback_content,
            user_id=request.user_id,
            context=request.context
        )
        
        return {
            "success": True,
            "memory_id": memory_id,
            "message": "Feedback stored in episodic memory"
        }
    except Exception as e:
        logger.error(f"Error storing feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retrieve")
async def retrieve_context(
    request: RetrieveContextRequest,
    memory: MemorySystem = Depends(get_memory)
):
    """
    Retrieve relevant context using HMLR
    Requirements: 39.4
    """
    try:
        memories = memory.retrieve_context(
            query=request.query,
            user_id=request.user_id,
            session_id=request.session_id,
            project_id=request.project_id
        )
        
        return {
            "success": True,
            "count": len(memories),
            "memories": memories
        }
    except Exception as e:
        logger.error(f"Error retrieving context: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/all/{user_id}")
async def get_all_memories(
    user_id: str,
    memory: MemorySystem = Depends(get_memory)
):
    """
    View all memories for user
    Requirements: 39.7
    """
    try:
        memories = memory.privacy.get_user_memories(user_id)
        
        return {
            "success": True,
            "user_id": user_id,
            "memories": memories,
            "counts": {
                "short_term": len(memories.get("short_term", [])),
                "long_term": len(memories.get("long_term", [])),
                "episodic": len(memories.get("episodic", []))
            }
        }
    except Exception as e:
        logger.error(f"Error getting all memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete")
async def delete_memory(
    request: DeleteMemoryRequest,
    memory: MemorySystem = Depends(get_memory)
):
    """
    Delete specific memory
    Requirements: 39.7
    """
    try:
        success = memory.privacy.delete_memory(
            user_id=request.user_id,
            memory_id=request.memory_id,
            layer=request.layer
        )
        
        if success:
            return {
                "success": True,
                "message": f"Memory {request.memory_id} deleted from {request.layer}"
            }
        else:
            raise HTTPException(status_code=404, detail="Memory not found or deletion failed")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/{user_id}")
async def export_memories(
    user_id: str,
    memory: MemorySystem = Depends(get_memory)
):
    """
    Export all memories for user
    Requirements: 39.8
    """
    try:
        export_data = memory.privacy.export_memories(user_id)
        
        return {
            "success": True,
            "user_id": user_id,
            "data": export_data
        }
    except Exception as e:
        logger.error(f"Error exporting memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/clear/{user_id}")
async def clear_all_memories(
    user_id: str,
    memory: MemorySystem = Depends(get_memory)
):
    """
    Clear all memories for user
    Requirements: 39.7
    """
    try:
        success = memory.privacy.clear_all_memories(user_id)
        
        if success:
            return {
                "success": True,
                "message": f"All memories cleared for user {user_id}"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to clear memories")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/prune/{user_id}")
async def prune_memories(
    user_id: str,
    memory: MemorySystem = Depends(get_memory)
):
    """
    Prune low-value memories for user
    Requirements: 39.6
    """
    try:
        pruned_counts = memory.prune_all_layers(user_id)
        
        return {
            "success": True,
            "user_id": user_id,
            "pruned": pruned_counts,
            "total_pruned": sum(pruned_counts.values())
        }
    except Exception as e:
        logger.error(f"Error pruning memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/session/{user_id}/{session_id}")
async def clear_session(
    user_id: str,
    session_id: str,
    memory: MemorySystem = Depends(get_memory)
):
    """
    Clear session memories
    Requirements: 39.3
    """
    try:
        success = memory.short_term.clear_session(user_id, session_id)
        
        if success:
            return {
                "success": True,
                "message": f"Session {session_id} cleared for user {user_id}"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to clear session")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/context")
async def get_conversation_context(
    user_id: str,
    session_id: str,
    project_id: str,
    limit: int = 20,
    memory: MemorySystem = Depends(get_memory)
):
    """
    Get conversation context for session
    Requirements: 4.4
    """
    try:
        # Route query to get relevant memories
        memories = memory.router.route_query(
            query="recent conversation context",
            user_id=user_id,
            context={
                'session_id': session_id,
                'project_id': project_id
            }
        )
        
        # Limit results
        context = memories[:limit]
        
        return {
            "success": True,
            "context": context,
            "count": len(context)
        }
    except Exception as e:
        logger.error(f"Error getting conversation context: {e}")
        raise HTTPException(status_code=500, detail=str(e))
