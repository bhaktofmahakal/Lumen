"""
Initialize Qdrant collections for AI Research Copilot
"""

import logging
from qdrant_client import QdrantClient
from qdrant_client.http import models
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_qdrant_collections():
    """Initialize Qdrant collections"""
    try:
        # Connect to Qdrant
        client = QdrantClient(url=settings.QDRANT_URL, timeout=30)
        logger.info(f"Connected to Qdrant at {settings.QDRANT_URL}")
        
        # Get existing collections
        existing_collections = {col.name for col in client.get_collections().collections}
        logger.info(f"Existing collections: {existing_collections}")
        
        # Define collections to create
        collections = [
            {
                "name": "documents",
                "description": "Document embeddings for semantic search",
                "vector_size": settings.EMBEDDING_DIMENSION,
                "distance": models.Distance.COSINE
            },
            {
                "name": "short_term_memory",
                "description": "Short-term memory for session context",
                "vector_size": settings.EMBEDDING_DIMENSION,
                "distance": models.Distance.COSINE
            },
            {
                "name": "long_term_memory",
                "description": "Long-term memory for project context",
                "vector_size": settings.EMBEDDING_DIMENSION,
                "distance": models.Distance.COSINE
            },
            {
                "name": "episodic_memory",
                "description": "Episodic memory for user history",
                "vector_size": settings.EMBEDDING_DIMENSION,
                "distance": models.Distance.COSINE
            }
        ]
        
        # Create collections if they don't exist
        for collection in collections:
            if collection["name"] not in existing_collections:
                logger.info(f"Creating collection: {collection['name']}")
                client.create_collection(
                    collection_name=collection["name"],
                    vectors_config=models.VectorParams(
                        size=collection["vector_size"],
                        distance=collection["distance"]
                    )
                )
                logger.info(f"✓ Created collection: {collection['name']}")
            else:
                logger.info(f"✓ Collection already exists: {collection['name']}")
        
        logger.info("Qdrant initialization completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize Qdrant: {e}")
        return False


if __name__ == "__main__":
    success = init_qdrant_collections()
    exit(0 if success else 1)
