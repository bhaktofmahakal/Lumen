"""
Vector storage in Qdrant for semantic search
Requirements: 1.6
"""

from typing import List, Dict, Optional, Any
import logging
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue
)

from config import settings
from models import TextChunk

logger = logging.getLogger(__name__)


class QdrantVectorStore:
    """
    Qdrant vector store for document embeddings
    Requirements: 1.6
    """
    
    def __init__(self, collection_name: str = "documents"):
        """
        Initialize Qdrant vector store
        
        Args:
            collection_name: Name of the Qdrant collection
        """
        self.collection_name = collection_name
        self.client = None
        self.embedding_dimension = settings.EMBEDDING_DIMENSION
        self._connect()
    
    def _connect(self):
        """Connect to Qdrant server"""
        try:
            logger.info(f"Connecting to Qdrant at {settings.QDRANT_URL}")
            self.client = QdrantClient(url=settings.QDRANT_URL)
            
            # Test connection
            collections = self.client.get_collections()
            logger.info(f"Connected to Qdrant. Collections: {len(collections.collections)}")
            
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            raise
    
    def create_collection(self, recreate: bool = False):
        """
        Create Qdrant collection with cosine distance
        Requirements: 1.6
        
        Args:
            recreate: If True, delete existing collection and create new one
        """
        try:
            # Check if collection exists
            collections = self.client.get_collections()
            collection_exists = any(
                c.name == self.collection_name 
                for c in collections.collections
            )
            
            if collection_exists:
                if recreate:
                    logger.info(f"Deleting existing collection: {self.collection_name}")
                    self.client.delete_collection(self.collection_name)
                else:
                    logger.info(f"Collection already exists: {self.collection_name}")
                    return
            
            # Create collection
            logger.info(f"Creating collection: {self.collection_name}")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_dimension,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"Collection created successfully: {self.collection_name}")
            
        except Exception as e:
            logger.error(f"Error creating collection: {e}")
            raise
    
    def upsert_chunks(
        self,
        chunks: List[TextChunk],
        batch_size: int = 100
    ) -> int:
        """
        Store text chunks with embeddings in Qdrant
        Requirements: 1.6 (batch upsert for efficiency)
        
        Args:
            chunks: List of TextChunk objects with embeddings
            batch_size: Number of chunks to upsert in each batch
        
        Returns:
            Number of chunks successfully stored
        """
        if not chunks:
            logger.warning("No chunks provided for upsert")
            return 0
        
        try:
            # Ensure collection exists
            self.create_collection(recreate=False)
            
            # Prepare points for upsert
            points = []
            for chunk in chunks:
                if not chunk.embedding:
                    logger.warning(f"Chunk {chunk.metadata.chunk_id} has no embedding, skipping")
                    continue
                
                # Create unique point ID
                point_id = f"{chunk.metadata.document_id}_{chunk.metadata.chunk_id}"
                
                # Create payload with metadata
                payload = {
                    'document_id': chunk.metadata.document_id,
                    'chunk_id': chunk.metadata.chunk_id,
                    'text': chunk.text,
                    'page_number': chunk.metadata.page_number,
                    'section': chunk.metadata.section
                }
                
                # Create point
                point = PointStruct(
                    id=point_id,
                    vector=chunk.embedding,
                    payload=payload
                )
                points.append(point)
            
            if not points:
                logger.warning("No valid points to upsert")
                return 0
            
            # Upsert in batches
            total_upserted = 0
            for i in range(0, len(points), batch_size):
                batch = points[i:i + batch_size]
                
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=batch
                )
                
                total_upserted += len(batch)
                logger.info(f"Upserted batch {i // batch_size + 1}: {len(batch)} points")
            
            logger.info(f"Successfully upserted {total_upserted} chunks to Qdrant")
            return total_upserted
            
        except Exception as e:
            logger.error(f"Error upserting chunks: {e}")
            raise
    
    def search(
        self,
        query_embedding: List[float],
        limit: int = 10,
        score_threshold: Optional[float] = None,
        filter_conditions: Optional[Dict[str, Any]] = None
    ) -> List[Dict]:
        """
        Search for similar chunks using query embedding
        
        Args:
            query_embedding: Query vector
            limit: Maximum number of results to return
            score_threshold: Minimum similarity score (0-1 for cosine)
            filter_conditions: Optional filters (e.g., {'document_id': 'doc123'})
        
        Returns:
            List of search results with text, metadata, and scores
        """
        try:
            # Build filter if provided
            query_filter = None
            if filter_conditions:
                conditions = []
                for key, value in filter_conditions.items():
                    conditions.append(
                        FieldCondition(
                            key=key,
                            match=MatchValue(value=value)
                        )
                    )
                query_filter = Filter(must=conditions)
            
            # Search
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=query_filter
            )
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'id': result.id,
                    'score': result.score,
                    'document_id': result.payload.get('document_id'),
                    'chunk_id': result.payload.get('chunk_id'),
                    'text': result.payload.get('text'),
                    'page_number': result.payload.get('page_number'),
                    'section': result.payload.get('section')
                })
            
            logger.info(f"Search returned {len(formatted_results)} results")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching Qdrant: {e}")
            raise
    
    def delete_document(self, document_id: str) -> bool:
        """
        Delete all chunks for a document
        
        Args:
            document_id: Document identifier
        
        Returns:
            True if successful
        """
        try:
            # Delete points with matching document_id
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key='document_id',
                            match=MatchValue(value=document_id)
                        )
                    ]
                )
            )
            
            logger.info(f"Deleted all chunks for document: {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document chunks: {e}")
            raise
    
    def get_collection_info(self) -> Dict:
        """Get information about the collection"""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                'name': info.config.params.vectors.size,
                'vectors_count': info.vectors_count,
                'points_count': info.points_count,
                'status': info.status
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {}

