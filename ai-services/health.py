"""
Health check module for all services
"""

import logging
from typing import Dict, Any
import asyncio
from datetime import datetime, timezone

import pymysql
import redis.asyncio as redis
from qdrant_client import QdrantClient
from qdrant_client.http import models
import httpx

from config import settings

logger = logging.getLogger(__name__)


class HealthChecker:
    """Health checker for all infrastructure services"""
    
    def __init__(self):
        self.mysql_conn = None
        self.redis_client = None
        self.qdrant_client = None
        self.services_status = {}
    
    async def initialize(self):
        """Initialize connections to all services"""
        logger.info("Initializing service connections...")
        
        # Initialize Qdrant client
        try:
            self.qdrant_client = QdrantClient(
                url=settings.QDRANT_URL,
                timeout=10
            )
            logger.info("Qdrant client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant client: {e}")
        
        # Initialize Redis client
        try:
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
                decode_responses=True
            )
            logger.info("Redis client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Redis client: {e}")
    
    async def cleanup(self):
        """Cleanup connections"""
        if self.redis_client:
            await self.redis_client.close()
        logger.info("Connections cleaned up")
    
    async def check_mysql(self) -> Dict[str, Any]:
        """Check MySQL connection"""
        try:
            conn = pymysql.connect(
                host=settings.DB_HOST,
                port=settings.DB_PORT,
                user=settings.DB_USER,
                password=settings.DB_PASSWORD,
                database=settings.DB_NAME,
                connect_timeout=5
            )
            conn.ping()
            conn.close()
            return {
                "status": "healthy",
                "message": "MySQL connection successful",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"MySQL health check failed: {e}")
            return {
                "status": "unhealthy",
                "message": f"MySQL connection failed: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def check_redis(self) -> Dict[str, Any]:
        """Check Redis connection"""
        try:
            if not self.redis_client:
                raise Exception("Redis client not initialized")
            
            await self.redis_client.ping()
            return {
                "status": "healthy",
                "message": "Redis connection successful",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {
                "status": "unhealthy",
                "message": f"Redis connection failed: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def check_qdrant(self) -> Dict[str, Any]:
        """Check Qdrant connection"""
        try:
            if not self.qdrant_client:
                raise Exception("Qdrant client not initialized")
            
            # Try to get collections (will fail if Qdrant is down)
            collections = self.qdrant_client.get_collections()
            return {
                "status": "healthy",
                "message": "Qdrant connection successful",
                "collections_count": len(collections.collections),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return {
                "status": "unhealthy",
                "message": f"Qdrant connection failed: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def check_ollama(self) -> Dict[str, Any]:
        """Check Ollama connection (optional)"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{settings.OLLAMA_HOST}/api/tags")
                if response.status_code == 200:
                    return {
                        "status": "healthy",
                        "message": "Ollama connection successful",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                else:
                    raise Exception(f"Unexpected status code: {response.status_code}")
        except Exception as e:
            logger.warning(f"Ollama health check failed (optional service): {e}")
            return {
                "status": "unavailable",
                "message": f"Ollama not available: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def check_all(self) -> Dict[str, Any]:
        """Check all services"""
        results = await asyncio.gather(
            self.check_mysql(),
            self.check_redis(),
            self.check_qdrant(),
            self.check_ollama(),
            return_exceptions=True
        )
        
        mysql_status, redis_status, qdrant_status, ollama_status = results
        
        # Determine overall health
        critical_services = [mysql_status, redis_status, qdrant_status]
        all_healthy = all(
            isinstance(s, dict) and s.get("status") == "healthy" 
            for s in critical_services
        )
        
        return {
            "status": "healthy" if all_healthy else "degraded",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "services": {
                "mysql": mysql_status,
                "redis": redis_status,
                "qdrant": qdrant_status,
                "ollama": ollama_status
            }
        }
