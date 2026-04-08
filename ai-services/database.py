"""
Database connection and operations for MySQL
"""

import pymysql
from pymysql.cursors import DictCursor
from contextlib import asynccontextmanager
from typing import Optional, Dict, List, Any
import logging

from config import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """MySQL database manager"""
    
    def __init__(self):
        self.connection_params = {
            'host': settings.DB_HOST,
            'port': settings.DB_PORT,
            'user': settings.DB_USER,
            'password': settings.DB_PASSWORD,
            'database': settings.DB_NAME,
            'charset': 'utf8mb4',
            'cursorclass': DictCursor,
            'autocommit': False
        }
    
    def get_connection(self):
        """Get database connection"""
        return pymysql.connect(**self.connection_params)
    
    async def insert_document(self, document_data: Dict[str, Any]) -> str:
        """Insert document metadata"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                sql = """
                INSERT INTO documents (
                    document_id, project_id, user_id, filename, file_path, file_size, 
                    file_hash, title, authors, publication_date, doi, 
                    arxiv_id, pubmed_id, document_type, status, page_count,
                    created_at, updated_at
                ) VALUES (
                    %(document_id)s, %(project_id)s, %(user_id)s, %(filename)s, %(file_path)s, %(file_size)s,
                    %(file_hash)s, %(title)s, %(authors)s, %(publication_date)s, %(doi)s,
                    %(arxiv_id)s, %(pubmed_id)s, %(document_type)s, %(status)s, %(page_count)s,
                    NOW(), NOW()
                )
                """
                cursor.execute(sql, document_data)
                conn.commit()
                return document_data['document_id']
        except Exception as e:
            conn.rollback()
            logger.error(f"Error inserting document: {e}")
            raise
        finally:
            conn.close()
    
    async def get_document(self, document_id: str) -> Optional[Dict]:
        """Get document by ID"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                sql = "SELECT * FROM documents WHERE document_id = %s"
                cursor.execute(sql, (document_id,))
                return cursor.fetchone()
        finally:
            conn.close()
    
    async def update_document_status(self, document_id: str, status: str, error_message: Optional[str] = None):
        """Update document processing status"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                if error_message:
                    sql = """
                    UPDATE documents 
                    SET status = %s, error_message = %s, updated_at = NOW()
                    WHERE document_id = %s
                    """
                    cursor.execute(sql, (status, error_message, document_id))
                else:
                    sql = """
                    UPDATE documents 
                    SET status = %s, updated_at = NOW()
                    WHERE document_id = %s
                    """
                    cursor.execute(sql, (status, document_id))
                conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Error updating document status: {e}")
            raise
        finally:
            conn.close()
    
    async def check_duplicate_document(self, file_hash: str, project_id: str) -> Optional[Dict]:
        """Check if document with same hash exists in project"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                sql = """
                SELECT * FROM documents 
                WHERE file_hash = %s AND project_id = %s
                LIMIT 1
                """
                cursor.execute(sql, (file_hash, project_id))
                return cursor.fetchone()
        finally:
            conn.close()
    
    async def get_project_documents(self, project_id: str) -> List[Dict]:
        """Get all documents for a project"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                sql = """
                SELECT * FROM documents 
                WHERE project_id = %s
                ORDER BY created_at DESC
                """
                cursor.execute(sql, (project_id,))
                return cursor.fetchall()
        finally:
            conn.close()


# Global database manager instance
db_manager = DatabaseManager()
