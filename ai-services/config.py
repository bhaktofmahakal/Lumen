"""
Configuration settings for AI Research Copilot
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import os


class Settings(BaseSettings):
    """Application settings"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )
    
    # Application
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_URL: str = "http://localhost"
    
    # Database
    DB_HOST: str = "mysql"
    DB_PORT: int = 3306
    DB_NAME: str = "ai_research"
    DB_USER: str = "root"
    DB_PASSWORD: str = "rootpassword"
    
    # Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = "redispassword"
    
    # Qdrant
    QDRANT_HOST: str = "qdrant"
    QDRANT_PORT: int = 6333
    
    @property
    def QDRANT_URL(self) -> str:
        return f"http://{self.QDRANT_HOST}:{self.QDRANT_PORT}"
    
    # LLM API Keys
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    OLLAMA_HOST: str = "http://ollama:11434"
    
    # CORS
    CORS_ORIGINS: str = "http://localhost,http://localhost:3000,https://localhost"
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 52428800  # 50MB
    ALLOWED_FILE_TYPES: str = "pdf"
    UPLOAD_DIR: str = "/app/uploads"
    
    @property
    def allowed_file_types_list(self) -> List[str]:
        return [ft.strip() for ft in self.ALLOWED_FILE_TYPES.split(",")]
    
    # Embedding Model
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    
    # LLM Configuration
    DEFAULT_LLM_PROVIDER: str = "gemini"
    GEMINI_MODEL: str = "gemini-1.5-flash"
    GROQ_MODEL: str = "llama3-8b-8192"
    OLLAMA_MODEL: str = "llama3"
    
    # Memory Configuration
    MEMORY_SHORT_TERM_TTL: int = 3600  # 1 hour
    MEMORY_LONG_TERM_TTL: int = 2592000  # 30 days


settings = Settings()
