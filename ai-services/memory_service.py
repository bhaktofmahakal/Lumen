"""
Memory System with Hierarchical Memory Layer Routing (HMLR)
Custom implementation using Qdrant directly
Requirements: 39.1, 39.2, 39.3, 39.4, 39.5, 39.6, 39.7, 39.8
"""

from typing import List, Dict, Optional, Any
import logging
from datetime import datetime, timedelta
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue, SearchRequest
)
import json
import hashlib

from config import settings
from embeddings import EmbeddingGenerator

logger = logging.getLogger(__name__)


class MemoryLayer:
    """Base class for memory layers using Qdrant"""
    
    def __init__(self, collection_name: str, embedding_model: str, ttl: Optional[int] = None):
        """
        Initialize memory layer
        
        Args:
            collection_name: Qdrant collection name for this layer
            embedding_model: Sentence-transformers model for embeddings
            ttl: Time-to-live in seconds (None for no expiration)
        """
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        self.ttl = ttl
        self.client = None
        self.embedder = None
        self._initialize()
    
    def _initialize(self):
        """Initialize Qdrant client and embedder"""
        try:
            # Connect to Qdrant
            self.client = QdrantClient(
                host=settings.QDRANT_HOST,
                port=settings.QDRANT_PORT
            )
            
            # Initialize embedder
            self.embedder = EmbeddingGenerator(model_name=self.embedding_model)
            
            # Create collection if not exists
            self._create_collection()
            
            logger.info(f"Initialized memory layer: {self.collection_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize memory layer {self.collection_name}: {e}")
            raise
    
    def _create_collection(self):
        """Create Qdrant collection if not exists"""
        try:
            collections = self.client.get_collections()
            collection_exists = any(
                c.name == self.collection_name 
                for c in collections.collections
            )
            
            if not collection_exists:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedder.get_embedding_dimension(),
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created collection: {self.collection_name}")
                
        except Exception as e:
            logger.error(f"Error creating collection: {e}")
            raise

    def add(self, messages: List[Dict], user_id: str, metadata: Optional[Dict] = None) -> str:
        """
        Add memory to layer
        
        Args:
            messages: List of message dicts with role and content
            user_id: User identifier
            metadata: Additional metadata
        
        Returns:
            Memory ID
        """
        try:
            if metadata is None:
                metadata = {}
            
            # Add timestamp
            metadata["timestamp"] = datetime.now().isoformat()
            metadata["access_count"] = 0
            metadata["user_id"] = user_id
            
            # Add TTL if configured
            if self.ttl:
                metadata["expires_at"] = (datetime.now() + timedelta(seconds=self.ttl)).isoformat()
            
            # Combine messages into text for embedding
            text = " ".join([msg.get("content", "") for msg in messages])
            
            # Generate embedding
            embedding = self.embedder.generate_embedding(text)
            
            # Generate unique ID
            memory_id = hashlib.md5(f"{user_id}_{text}_{datetime.now().isoformat()}".encode()).hexdigest()
            
            # Create payload
            payload = {
                "user_id": user_id,
                "messages": json.dumps(messages),
                "text": text,
                **metadata
            }
            
            # Store in Qdrant
            point = PointStruct(
                id=memory_id,
                vector=embedding,
                payload=payload
            )
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            logger.info(f"Added memory to {self.collection_name} for user {user_id}")
            return memory_id
            
        except Exception as e:
            logger.error(f"Error adding memory: {e}")
            raise
    
    def search(
        self,
        query: str,
        user_id: str,
        limit: int = 10,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Search memories in layer
        
        Args:
            query: Search query
            user_id: User identifier
            limit: Maximum results to return
            filters: Additional filters
        
        Returns:
            List of matching memories
        """
        try:
            # Generate query embedding
            query_embedding = self.embedder.generate_embedding(query)
            
            # Build filter
            filter_conditions = [
                FieldCondition(
                    key="user_id",
                    match=MatchValue(value=user_id)
                )
            ]
            
            if filters:
                for key, value in filters.items():
                    filter_conditions.append(
                        FieldCondition(
                            key=key,
                            match=MatchValue(value=value)
                        )
                    )
            
            query_filter = Filter(must=filter_conditions)
            
            # Search in Qdrant
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                query_filter=query_filter
            )
            
            # Format results
            formatted_results = []
            for result in results:
                memory = {
                    "id": result.id,
                    "score": result.score,
                    "messages": json.loads(result.payload.get("messages", "[]")),
                    "text": result.payload.get("text"),
                    "metadata": {
                        k: v for k, v in result.payload.items()
                        if k not in ["messages", "text", "user_id"]
                    }
                }
                formatted_results.append(memory)
            
            logger.info(f"Search in {self.collection_name} returned {len(formatted_results)} results")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching memory: {e}")
            return []

    def get_all(self, user_id: str) -> List[Dict]:
        """Get all memories for user"""
        try:
            # Scroll through all points for user
            results = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="user_id",
                            match=MatchValue(value=user_id)
                        )
                    ]
                ),
                limit=1000  # Max per scroll
            )
            
            # Format results
            formatted_results = []
            for point in results[0]:  # results is tuple (points, next_page_offset)
                memory = {
                    "id": point.id,
                    "messages": json.loads(point.payload.get("messages", "[]")),
                    "text": point.payload.get("text"),
                    "metadata": {
                        k: v for k, v in point.payload.items()
                        if k not in ["messages", "text", "user_id"]
                    }
                }
                formatted_results.append(memory)
            
            return formatted_results
        except Exception as e:
            logger.error(f"Error getting all memories: {e}")
            return []
    
    def delete(self, memory_id: str) -> bool:
        """Delete specific memory"""
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=[memory_id]
            )
            logger.info(f"Deleted memory {memory_id} from {self.collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting memory: {e}")
            return False
    
    def delete_all(self, user_id: str) -> bool:
        """Delete all memories for user"""
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="user_id",
                            match=MatchValue(value=user_id)
                        )
                    ]
                )
            )
            logger.info(f"Deleted all memories for user {user_id} from {self.collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting all memories: {e}")
            return False
    
    def _increment_access_count(self, memory_id: str):
        """Increment access count for memory (for pruning strategy)"""
        # Note: Qdrant doesn't support direct payload updates
        # This would need to be tracked separately in Redis or MySQL
        pass


class ShortTermMemory(MemoryLayer):
    """
    Short-term memory (session context)
    Requirements: 39.1, 39.2, 39.3
    
    Storage Duration: Current session only (cleared on session end)
    Content:
    - Recent chat messages (last 10-20 exchanges)
    - Current document context
    - Active research findings
    - Temporary agent state
    """
    
    def __init__(self):
        super().__init__(
            collection_name="short_term_memory",
            embedding_model="all-MiniLM-L6-v2",  # Fast, lightweight
            ttl=settings.MEMORY_SHORT_TERM_TTL  # 1 hour default
        )

    def store_conversation_turn(
        self,
        user_message: str,
        assistant_message: str,
        user_id: str,
        session_id: str,
        document_context: Optional[List[str]] = None
    ) -> str:
        """
        Store a conversation turn in short-term memory
        
        Args:
            user_message: User's message
            assistant_message: Assistant's response
            user_id: User identifier
            session_id: Session identifier
            document_context: List of document IDs in context
        
        Returns:
            Memory ID
        """
        messages = [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": assistant_message}
        ]
        
        metadata = {
            "session_id": session_id,
            "document_context": document_context or [],
            "memory_type": "conversation"
        }
        
        return self.add(messages, user_id, metadata)
    
    def store_research_finding(
        self,
        finding: str,
        user_id: str,
        session_id: str,
        document_id: str,
        source_page: Optional[int] = None
    ) -> str:
        """
        Store a research finding in short-term memory
        
        Args:
            finding: Research finding text
            user_id: User identifier
            session_id: Session identifier
            document_id: Source document ID
            source_page: Page number in source
        
        Returns:
            Memory ID
        """
        messages = [
            {"role": "system", "content": f"Research finding: {finding}"}
        ]
        
        metadata = {
            "session_id": session_id,
            "document_id": document_id,
            "source_page": source_page,
            "memory_type": "research_finding"
        }
        
        return self.add(messages, user_id, metadata)
    
    def get_recent_context(
        self,
        user_id: str,
        session_id: str,
        limit: int = 20
    ) -> List[Dict]:
        """
        Get recent conversation context for session
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            limit: Maximum messages to return
        
        Returns:
            List of recent messages
        """
        return self.search(
            query="recent conversation",
            user_id=user_id,
            limit=limit,
            filters={"session_id": session_id}
        )

    def clear_session(self, user_id: str, session_id: str) -> bool:
        """
        Clear all memories for a session
        
        Args:
            user_id: User identifier
            session_id: Session identifier
        
        Returns:
            True if successful
        """
        try:
            memories = self.get_all(user_id)
            for memory in memories:
                if memory.get("metadata", {}).get("session_id") == session_id:
                    self.delete(memory.get("id"))
            logger.info(f"Cleared session {session_id} for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error clearing session: {e}")
            return False


class LongTermMemory(MemoryLayer):
    """
    Long-term memory (project context)
    Requirements: 39.2, 39.5
    
    Storage Duration: Lifetime of project (until project deleted)
    Content:
    - Project research findings and document summaries
    - Key concepts and terminology
    - User preferences for project (citation style, writing style)
    - Research progress and milestones
    """
    
    def __init__(self):
        super().__init__(
            collection_name="long_term_memory",
            embedding_model="all-mpnet-base-v2",  # Higher quality for long-term
            ttl=settings.MEMORY_LONG_TERM_TTL  # 30 days default
        )
    
    def store_project_finding(
        self,
        finding: str,
        user_id: str,
        project_id: str,
        document_id: Optional[str] = None,
        finding_type: str = "key_concept"
    ) -> str:
        """
        Store project research finding
        
        Args:
            finding: Finding text
            user_id: User identifier
            project_id: Project identifier
            document_id: Source document ID
            finding_type: Type of finding (key_concept, methodology, result, etc.)
        
        Returns:
            Memory ID
        """
        messages = [
            {"role": "system", "content": f"Research finding: {finding}"}
        ]
        
        metadata = {
            "project_id": project_id,
            "document_id": document_id,
            "finding_type": finding_type,
            "memory_type": "project_finding"
        }
        
        return self.add(messages, user_id, metadata)

    def store_document_summary(
        self,
        summary: str,
        user_id: str,
        project_id: str,
        document_id: str,
        document_title: str
    ) -> str:
        """
        Store document summary
        
        Args:
            summary: Document summary text
            user_id: User identifier
            project_id: Project identifier
            document_id: Document identifier
            document_title: Document title
        
        Returns:
            Memory ID
        """
        messages = [
            {"role": "system", "content": f"Document summary for '{document_title}': {summary}"}
        ]
        
        metadata = {
            "project_id": project_id,
            "document_id": document_id,
            "document_title": document_title,
            "memory_type": "document_summary"
        }
        
        return self.add(messages, user_id, metadata)
    
    def store_project_preference(
        self,
        preference_type: str,
        preference_value: Any,
        user_id: str,
        project_id: str
    ) -> str:
        """
        Store project-specific user preference
        
        Args:
            preference_type: Type of preference (citation_style, writing_style, etc.)
            preference_value: Preference value
            user_id: User identifier
            project_id: Project identifier
        
        Returns:
            Memory ID
        """
        messages = [
            {"role": "system", "content": f"User prefers {preference_type}: {preference_value}"}
        ]
        
        metadata = {
            "project_id": project_id,
            "preference_type": preference_type,
            "preference_value": str(preference_value),
            "memory_type": "project_preference"
        }
        
        return self.add(messages, user_id, metadata)
    
    def get_project_context(
        self,
        user_id: str,
        project_id: str,
        limit: int = 20
    ) -> List[Dict]:
        """
        Get project context memories
        
        Args:
            user_id: User identifier
            project_id: Project identifier
            limit: Maximum results
        
        Returns:
            List of project memories
        """
        return self.search(
            query="project research context",
            user_id=user_id,
            limit=limit,
            filters={"project_id": project_id}
        )


class EpisodicMemory(MemoryLayer):
    """
    Episodic memory (user history)
    Requirements: 39.2, 39.5
    
    Storage Duration: Lifetime of user account
    Content:
    - User preferences across all projects
    - Feedback history and corrections
    - Research trajectory and learning patterns
    """
    
    def __init__(self):
        super().__init__(
            collection_name="episodic_memory",
            embedding_model="all-mpnet-base-v2",  # Higher quality for long-term
            ttl=None  # No expiration for user history
        )
    
    def store_user_preference(
        self,
        preference_type: str,
        preference_value: Any,
        user_id: str
    ) -> str:
        """
        Store global user preference
        
        Args:
            preference_type: Type of preference
            preference_value: Preference value
            user_id: User identifier
        
        Returns:
            Memory ID
        """
        messages = [
            {"role": "system", "content": f"User prefers {preference_type}: {preference_value}"}
        ]
        
        metadata = {
            "preference_type": preference_type,
            "preference_value": str(preference_value),
            "memory_type": "user_preference"
        }
        
        return self.add(messages, user_id, metadata)
    
    def store_feedback(
        self,
        feedback_type: str,
        feedback_content: str,
        user_id: str,
        context: Optional[Dict] = None
    ) -> str:
        """
        Store user feedback
        
        Args:
            feedback_type: Type of feedback (correction, rating, suggestion)
            feedback_content: Feedback text
            user_id: User identifier
            context: Additional context
        
        Returns:
            Memory ID
        """
        messages = [
            {"role": "user", "content": feedback_content}
        ]
        
        metadata = {
            "feedback_type": feedback_type,
            "memory_type": "feedback",
            **(context or {})
        }
        
        return self.add(messages, user_id, metadata)

    def store_research_trajectory(
        self,
        topic: str,
        user_id: str,
        project_id: Optional[str] = None
    ) -> str:
        """
        Store research trajectory (topics explored)
        
        Args:
            topic: Research topic
            user_id: User identifier
            project_id: Optional project identifier
        
        Returns:
            Memory ID
        """
        messages = [
            {"role": "system", "content": f"User researched topic: {topic}"}
        ]
        
        metadata = {
            "topic": topic,
            "project_id": project_id,
            "memory_type": "research_trajectory"
        }
        
        return self.add(messages, user_id, metadata)
    
    def get_user_preferences(
        self,
        user_id: str,
        preference_type: Optional[str] = None
    ) -> List[Dict]:
        """
        Get user preferences
        
        Args:
            user_id: User identifier
            preference_type: Optional filter by preference type
        
        Returns:
            List of preferences
        """
        filters = {"memory_type": "user_preference"}
        if preference_type:
            filters["preference_type"] = preference_type
        
        return self.search(
            query="user preferences",
            user_id=user_id,
            limit=20,
            filters=filters
        )


class MemoryRouter:
    """
    Hierarchical Memory Layer Routing (HMLR)
    Requirements: 39.4
    
    Routes queries to appropriate memory layers based on query type
    """
    
    def __init__(
        self,
        short_term: ShortTermMemory,
        long_term: LongTermMemory,
        episodic: EpisodicMemory
    ):
        self.stm = short_term
        self.ltm = long_term
        self.em = episodic
    
    def classify_query(self, query: str) -> str:
        """
        Classify query type for routing
        
        Args:
            query: Search query
        
        Returns:
            Query type: preference, recent, general
        """
        query_lower = query.lower()
        
        # Preference queries
        preference_keywords = ["prefer", "style", "format", "like", "want", "setting"]
        if any(keyword in query_lower for keyword in preference_keywords):
            return "preference"
        
        # Recent context queries
        recent_keywords = ["recent", "last", "previous", "earlier", "just", "ago"]
        if any(keyword in query_lower for keyword in recent_keywords):
            return "recent"
        
        return "general"

    def route_query(
        self,
        query: str,
        user_id: str,
        context: Dict
    ) -> List[Dict]:
        """
        Route query to appropriate memory layers
        Requirements: 39.4
        
        Args:
            query: Search query
            user_id: User identifier
            context: Query context (session_id, project_id, etc.)
        
        Returns:
            List of relevant memories from all layers
        """
        query_type = self.classify_query(query)
        memories = []
        
        # Always check short-term memory for recent context
        if context.get("session_id"):
            stm_results = self.stm.search(
                query=query,
                user_id=user_id,
                limit=5,
                filters={"session_id": context["session_id"]}
            )
            memories.extend(stm_results)
        
        # Check long-term memory for project-specific context
        if context.get("project_id"):
            ltm_results = self.ltm.search(
                query=query,
                user_id=user_id,
                limit=10,
                filters={"project_id": context["project_id"]}
            )
            memories.extend(ltm_results)
        
        # Check episodic memory for user preferences
        if query_type in ["preference", "general"]:
            em_results = self.em.search(
                query=query,
                user_id=user_id,
                limit=5
            )
            memories.extend(em_results)
        
        # Rank and deduplicate
        return self.rank_memories(memories)
    
    def rank_memories(self, memories: List[Dict]) -> List[Dict]:
        """
        Rank memories by relevance and recency
        
        Args:
            memories: List of memories from different layers
        
        Returns:
            Ranked and deduplicated memories (top 20)
        """
        # Remove duplicates by ID
        seen_ids = set()
        unique_memories = []
        for memory in memories:
            mem_id = memory.get("id")
            if mem_id and mem_id not in seen_ids:
                seen_ids.add(mem_id)
                unique_memories.append(memory)
        
        # Sort by score (descending) and timestamp (descending)
        sorted_memories = sorted(
            unique_memories,
            key=lambda m: (
                m.get("score", 0),
                m.get("metadata", {}).get("timestamp", "")
            ),
            reverse=True
        )
        
        # Return top 20
        return sorted_memories[:20]



class MemoryPruner:
    """
    Memory pruning strategy
    Requirements: 39.6
    
    Manages memory storage limits and maintains relevance
    """
    
    def __init__(self, memory_layer: MemoryLayer):
        self.memory_layer = memory_layer
    
    def calculate_retention_score(self, memory: Dict) -> float:
        """
        Calculate retention score (higher = keep, lower = prune)
        
        Args:
            memory: Memory dict with metadata
        
        Returns:
            Retention score (0-1)
        """
        # Recency score (0-1, higher for recent)
        timestamp_str = memory.get("metadata", {}).get("timestamp", "")
        if timestamp_str:
            try:
                timestamp = datetime.fromisoformat(timestamp_str)
                age_days = (datetime.now() - timestamp).days
                recency_score = 1.0 / (1.0 + age_days / 30.0)
            except:
                recency_score = 0.5
        else:
            recency_score = 0.5
        
        # Access frequency score (0-1, higher for frequently accessed)
        access_count = memory.get("metadata", {}).get("access_count", 0)
        frequency_score = min(access_count / 10.0, 1.0)
        
        # Relevance score (from vector similarity)
        relevance_score = memory.get("score", 0.5)
        
        # Weighted combination
        return (
            0.3 * recency_score +
            0.3 * frequency_score +
            0.4 * relevance_score
        )
    
    def prune_memories(self, user_id: str, max_memories: int = 10000) -> int:
        """
        Prune low-value memories when storage limit exceeded
        
        Args:
            user_id: User identifier
            max_memories: Maximum memories to keep
        
        Returns:
            Number of memories pruned
        """
        try:
            # Get all memories for user
            all_memories = self.memory_layer.get_all(user_id)
            
            if len(all_memories) <= max_memories:
                logger.info(f"No pruning needed: {len(all_memories)} <= {max_memories}")
                return 0
            
            # Calculate retention scores
            scored_memories = []
            for memory in all_memories:
                score = self.calculate_retention_score(memory)
                scored_memories.append((memory, score))
            
            # Sort by score (ascending - lowest scores first)
            scored_memories.sort(key=lambda x: x[1])
            
            # Prune bottom 20%
            prune_count = int(len(scored_memories) * 0.2)
            to_prune = scored_memories[:prune_count]
            
            # Delete low-value memories
            pruned = 0
            for memory, score in to_prune:
                if self.memory_layer.delete(memory.get("id")):
                    pruned += 1
            
            logger.info(f"Pruned {pruned} memories from {self.memory_layer.collection_name}")
            return pruned
            
        except Exception as e:
            logger.error(f"Error pruning memories: {e}")
            return 0



class MemoryPrivacyControls:
    """
    Privacy controls for memory management
    Requirements: 39.7, 39.8
    
    Provides user transparency and data control
    """
    
    def __init__(
        self,
        short_term: ShortTermMemory,
        long_term: LongTermMemory,
        episodic: EpisodicMemory
    ):
        self.stm = short_term
        self.ltm = long_term
        self.em = episodic
    
    def get_user_memories(self, user_id: str) -> Dict[str, List[Dict]]:
        """
        View all memories for user
        Requirements: 39.7
        
        Args:
            user_id: User identifier
        
        Returns:
            Dict with memories from all layers
        """
        try:
            return {
                "short_term": self.stm.get_all(user_id),
                "long_term": self.ltm.get_all(user_id),
                "episodic": self.em.get_all(user_id)
            }
        except Exception as e:
            logger.error(f"Error getting user memories: {e}")
            return {"short_term": [], "long_term": [], "episodic": []}
    
    def delete_memory(self, user_id: str, memory_id: str, layer: str) -> bool:
        """
        Delete specific memory
        Requirements: 39.7
        
        Args:
            user_id: User identifier
            memory_id: Memory identifier
            layer: Memory layer (stm, ltm, em)
        
        Returns:
            True if successful
        """
        try:
            memory_layer_map = {
                "stm": self.stm,
                "short_term": self.stm,
                "ltm": self.ltm,
                "long_term": self.ltm,
                "em": self.em,
                "episodic": self.em
            }
            
            memory_layer = memory_layer_map.get(layer)
            if not memory_layer:
                logger.error(f"Invalid memory layer: {layer}")
                return False
            
            return memory_layer.delete(memory_id)
            
        except Exception as e:
            logger.error(f"Error deleting memory: {e}")
            return False
    
    def export_memories(self, user_id: str) -> str:
        """
        Export all memories for user
        Requirements: 39.8
        
        Args:
            user_id: User identifier
        
        Returns:
            JSON string of all memories
        """
        try:
            memories = self.get_user_memories(user_id)
            return json.dumps(memories, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error exporting memories: {e}")
            return "{}"
    
    def clear_all_memories(self, user_id: str) -> bool:
        """
        Clear all memories for user
        Requirements: 39.7
        
        Args:
            user_id: User identifier
        
        Returns:
            True if successful
        """
        try:
            self.stm.delete_all(user_id)
            self.ltm.delete_all(user_id)
            self.em.delete_all(user_id)
            logger.info(f"Cleared all memories for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error clearing all memories: {e}")
            return False



class MemorySystem:
    """
    Complete memory system with HMLR
    Requirements: 39.1, 39.2, 39.3, 39.4, 39.5, 39.6, 39.7, 39.8
    
    Integrates all memory layers with routing and privacy controls
    """
    
    def __init__(self):
        """Initialize memory system with all layers"""
        logger.info("Initializing Memory System with HMLR")
        
        # Initialize memory layers
        self.short_term = ShortTermMemory()
        self.long_term = LongTermMemory()
        self.episodic = EpisodicMemory()
        
        # Initialize router
        self.router = MemoryRouter(
            short_term=self.short_term,
            long_term=self.long_term,
            episodic=self.episodic
        )
        
        # Initialize pruners
        self.stm_pruner = MemoryPruner(self.short_term)
        self.ltm_pruner = MemoryPruner(self.long_term)
        self.em_pruner = MemoryPruner(self.episodic)
        
        # Initialize privacy controls
        self.privacy = MemoryPrivacyControls(
            short_term=self.short_term,
            long_term=self.long_term,
            episodic=self.episodic
        )
        
        logger.info("Memory System initialized successfully")
    
    def retrieve_context(
        self,
        query: str,
        user_id: str,
        session_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> List[Dict]:
        """
        Retrieve relevant context from all memory layers using HMLR
        
        Args:
            query: Search query
            user_id: User identifier
            session_id: Optional session identifier
            project_id: Optional project identifier
        
        Returns:
            List of relevant memories
        """
        context = {
            "session_id": session_id,
            "project_id": project_id
        }
        
        return self.router.route_query(query, user_id, context)
    
    def prune_all_layers(self, user_id: str) -> Dict[str, int]:
        """
        Prune all memory layers for user
        
        Args:
            user_id: User identifier
        
        Returns:
            Dict with pruned counts per layer
        """
        return {
            "short_term": self.stm_pruner.prune_memories(user_id, max_memories=1000),
            "long_term": self.ltm_pruner.prune_memories(user_id, max_memories=5000),
            "episodic": self.em_pruner.prune_memories(user_id, max_memories=10000)
        }


# Global memory system instance
memory_system = None


def get_memory_system() -> MemorySystem:
    """Get or create global memory system instance"""
    global memory_system
    if memory_system is None:
        memory_system = MemorySystem()
    return memory_system
