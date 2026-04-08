"""
File storage management for uploaded documents
"""

import os
import aiofiles
from pathlib import Path
from typing import BinaryIO
import logging

from config import settings

logger = logging.getLogger(__name__)


class StorageManager:
    """Manages file storage for uploaded documents"""
    
    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    def get_document_path(self, document_id: str, filename: str) -> Path:
        """Get full path for document storage"""
        # Create subdirectory based on first 2 chars of document_id for better organization
        subdir = self.upload_dir / document_id[:2]
        subdir.mkdir(parents=True, exist_ok=True)
        return subdir / f"{document_id}_{filename}"
    
    async def save_file(self, document_id: str, filename: str, file_content: bytes) -> str:
        """Save uploaded file to storage"""
        try:
            file_path = self.get_document_path(document_id, filename)
            
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_content)
            
            logger.info(f"Saved file to {file_path}")
            return str(file_path)
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            raise
    
    async def read_file(self, document_id: str, filename: str) -> bytes:
        """Read file from storage"""
        try:
            file_path = self.get_document_path(document_id, filename)
            
            async with aiofiles.open(file_path, 'rb') as f:
                content = await f.read()
            
            return content
        except Exception as e:
            logger.error(f"Error reading file: {e}")
            raise
    
    async def delete_file(self, document_id: str, filename: str):
        """Delete file from storage"""
        try:
            file_path = self.get_document_path(document_id, filename)
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted file {file_path}")
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            raise
    
    def file_exists(self, document_id: str, filename: str) -> bool:
        """Check if file exists in storage"""
        file_path = self.get_document_path(document_id, filename)
        return file_path.exists()


# Global storage manager instance
storage_manager = StorageManager()
