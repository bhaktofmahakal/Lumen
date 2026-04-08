"""
Semantic text chunking for document processing
Requirements: 1.5
"""

from typing import List, Dict, Optional
import logging
import re

from models import TextChunk, ChunkMetadata

logger = logging.getLogger(__name__)


class SemanticChunker:
    """
    Semantic text chunking using LlamaIndex
    Requirements: 1.5
    """
    
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        """
        Initialize semantic chunker
        
        Args:
            chunk_size: Target size for each chunk in tokens
            chunk_overlap: Number of overlapping tokens between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.llama_index_available = self._check_llama_index()
    
    def _check_llama_index(self) -> bool:
        """Check if LlamaIndex is available"""
        try:
            from llama_index.core.node_parser import SentenceSplitter
            return True
        except ImportError:
            logger.warning("LlamaIndex not available - using simple chunking")
            return False
    
    def chunk_with_llama_index(
        self,
        text: str,
        document_id: str,
        metadata: Optional[Dict] = None
    ) -> List[TextChunk]:
        """
        Chunk text using LlamaIndex SentenceSplitter
        Preserves semantic boundaries
        """
        try:
            from llama_index.core.node_parser import SentenceSplitter
            from llama_index.core.schema import Document
            
            # Create LlamaIndex document
            doc = Document(text=text, metadata=metadata or {})
            
            # Initialize sentence splitter
            splitter = SentenceSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            )
            
            # Split into nodes
            nodes = splitter.get_nodes_from_documents([doc])
            
            # Convert to TextChunk objects
            chunks = []
            for i, node in enumerate(nodes):
                chunk_metadata = ChunkMetadata(
                    document_id=document_id,
                    chunk_id=i,
                    page_number=node.metadata.get('page_number'),
                    section=node.metadata.get('section')
                )
                
                chunk = TextChunk(
                    text=node.text,
                    metadata=chunk_metadata
                )
                chunks.append(chunk)
            
            logger.info(f"Created {len(chunks)} semantic chunks using LlamaIndex")
            return chunks
            
        except Exception as e:
            logger.error(f"LlamaIndex chunking failed: {e}")
            raise
    
    def chunk_simple(
        self,
        text: str,
        document_id: str,
        metadata: Optional[Dict] = None
    ) -> List[TextChunk]:
        """
        Simple sentence-based chunking fallback
        Splits on sentence boundaries while respecting chunk size
        """
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        chunks = []
        current_chunk = []
        current_length = 0
        chunk_id = 0
        
        for sentence in sentences:
            sentence_length = len(sentence.split())
            
            # If adding this sentence exceeds chunk size, save current chunk
            if current_length + sentence_length > self.chunk_size and current_chunk:
                chunk_text = ' '.join(current_chunk)
                
                chunk_metadata = ChunkMetadata(
                    document_id=document_id,
                    chunk_id=chunk_id,
                    page_number=metadata.get('page_number') if metadata else None,
                    section=metadata.get('section') if metadata else None
                )
                
                chunk = TextChunk(
                    text=chunk_text,
                    metadata=chunk_metadata
                )
                chunks.append(chunk)
                
                # Start new chunk with overlap
                overlap_sentences = current_chunk[-2:] if len(current_chunk) >= 2 else current_chunk
                current_chunk = overlap_sentences + [sentence]
                current_length = sum(len(s.split()) for s in current_chunk)
                chunk_id += 1
            else:
                current_chunk.append(sentence)
                current_length += sentence_length
        
        # Add final chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            
            chunk_metadata = ChunkMetadata(
                document_id=document_id,
                chunk_id=chunk_id,
                page_number=metadata.get('page_number') if metadata else None,
                section=metadata.get('section') if metadata else None
            )
            
            chunk = TextChunk(
                text=chunk_text,
                metadata=chunk_metadata
            )
            chunks.append(chunk)
        
        logger.info(f"Created {len(chunks)} simple chunks")
        return chunks
    
    def chunk_text(
        self,
        text: str,
        document_id: str,
        metadata: Optional[Dict] = None
    ) -> List[TextChunk]:
        """
        Chunk text with semantic boundaries
        Requirements: 1.5
        
        Args:
            text: Text to chunk
            document_id: Document identifier
            metadata: Optional metadata to preserve in chunks
        
        Returns:
            List of TextChunk objects with metadata
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for chunking")
            return []
        
        # Try LlamaIndex first
        if self.llama_index_available:
            try:
                return self.chunk_with_llama_index(text, document_id, metadata)
            except Exception as e:
                logger.warning(f"LlamaIndex chunking failed, using simple chunking: {e}")
        
        # Fall back to simple chunking
        return self.chunk_simple(text, document_id, metadata)
    
    def chunk_by_pages(
        self,
        text: str,
        document_id: str,
        page_delimiter: str = "[Page "
    ) -> List[TextChunk]:
        """
        Chunk text by pages, then apply semantic chunking within each page
        
        Args:
            text: Text with page markers
            document_id: Document identifier
            page_delimiter: Delimiter marking page boundaries
        
        Returns:
            List of TextChunk objects with page numbers
        """
        # Split by pages
        pages = text.split(page_delimiter)
        
        all_chunks = []
        chunk_id = 0
        
        for page_text in pages:
            if not page_text.strip():
                continue
            
            # Extract page number
            page_match = re.match(r'(\d+)\]', page_text)
            page_number = int(page_match.group(1)) if page_match else None
            
            # Remove page marker
            if page_match:
                page_text = page_text[page_match.end():]
            
            # Chunk this page
            page_metadata = {'page_number': page_number}
            page_chunks = self.chunk_text(page_text, document_id, page_metadata)
            
            # Update chunk IDs to be globally unique
            for chunk in page_chunks:
                chunk.metadata.chunk_id = chunk_id
                chunk_id += 1
            
            all_chunks.extend(page_chunks)
        
        logger.info(f"Created {len(all_chunks)} chunks across {len(pages)} pages")
        return all_chunks


# Global semantic chunker instance
semantic_chunker = SemanticChunker()
