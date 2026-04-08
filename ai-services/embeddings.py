"""
Embedding generation using sentence-transformers
Requirements: 1.5
"""

from typing import List, Optional
import logging
import numpy as np

from config import settings

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """
    Generate embeddings for text chunks using sentence-transformers
    Requirements: 1.5
    """
    
    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize embedding generator
        
        Args:
            model_name: Name of sentence-transformers model
                       Default: all-MiniLM-L6-v2 (384 dimensions)
        """
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self.embedding_dimension = settings.EMBEDDING_DIMENSION
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load sentence-transformers model"""
        try:
            from sentence_transformers import SentenceTransformer
            
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Model loaded successfully. Dimension: {self.embedding_dimension}")
            
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Text to embed
        
        Returns:
            List of floats representing the embedding vector
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding")
            return [0.0] * self.embedding_dimension
        
        try:
            # Generate embedding
            embedding = self.model.encode(text, convert_to_numpy=True)
            
            # Convert to list and ensure correct dimension
            embedding_list = embedding.tolist()
            
            # Validate dimension
            if len(embedding_list) != self.embedding_dimension:
                logger.error(
                    f"Embedding dimension mismatch: expected {self.embedding_dimension}, "
                    f"got {len(embedding_list)}"
                )
                raise ValueError("Embedding dimension mismatch")
            
            # Validate value range (should be roughly [-1, 1] for normalized embeddings)
            embedding_array = np.array(embedding_list)
            if np.any(np.abs(embedding_array) > 2.0):
                logger.warning("Embedding values outside expected range [-1, 1]")
            
            return embedding_list
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    def generate_embeddings_batch(
        self,
        texts: List[str],
        batch_size: int = 32,
        show_progress: bool = False
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches
        Requirements: 1.5 (batch processing for efficiency)
        
        Args:
            texts: List of texts to embed
            batch_size: Number of texts to process in each batch
            show_progress: Whether to show progress bar
        
        Returns:
            List of embedding vectors
        """
        if not texts:
            logger.warning("Empty text list provided for batch embedding")
            return []
        
        try:
            # Filter out empty texts
            valid_texts = [t if t and t.strip() else " " for t in texts]
            
            logger.info(f"Generating embeddings for {len(valid_texts)} texts in batches of {batch_size}")
            
            # Generate embeddings in batches
            embeddings = self.model.encode(
                valid_texts,
                batch_size=batch_size,
                show_progress_bar=show_progress,
                convert_to_numpy=True
            )
            
            # Convert to list of lists
            embeddings_list = embeddings.tolist()
            
            # Validate dimensions
            for i, emb in enumerate(embeddings_list):
                if len(emb) != self.embedding_dimension:
                    logger.error(
                        f"Embedding {i} dimension mismatch: expected {self.embedding_dimension}, "
                        f"got {len(emb)}"
                    )
                    raise ValueError(f"Embedding dimension mismatch at index {i}")
            
            logger.info(f"Successfully generated {len(embeddings_list)} embeddings")
            return embeddings_list
            
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            raise
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings produced by this model"""
        return self.embedding_dimension
    
    def validate_embedding(self, embedding: List[float]) -> bool:
        """
        Validate an embedding vector
        
        Args:
            embedding: Embedding vector to validate
        
        Returns:
            True if valid, False otherwise
        """
        # Check dimension
        if len(embedding) != self.embedding_dimension:
            logger.error(f"Invalid embedding dimension: {len(embedding)}")
            return False
        
        # Check value range (normalized embeddings should be roughly [-1, 1])
        embedding_array = np.array(embedding)
        if np.any(np.isnan(embedding_array)) or np.any(np.isinf(embedding_array)):
            logger.error("Embedding contains NaN or Inf values")
            return False
        
        # Check if all zeros (likely an error)
        if np.all(embedding_array == 0):
            logger.warning("Embedding is all zeros")
            return False
        
        return True

