"""Central configuration using Pydantic Settings."""

from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    APP_NAME: str = "Agentic RAG Nexus"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    FRONTEND_PORT: int = 8501

    # LLM - Ollama Primary
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "phi3"
    DEFAULT_LLM_PROVIDER: str = "ollama"
    
    # Ollama Performance Settings
    OLLAMA_TIMEOUT: int = 300
    OLLAMA_NUM_PREDICT: int = 512
    OLLAMA_TEMPERATURE: float = 0.3
    
    # API Timeouts
    LLM_API_TIMEOUT: int = 120
    VECTOR_SEARCH_TIMEOUT: int = 10
    
    # Groq Fallback
    GROQ_API_KEY: Optional[str] = None
    DEFAULT_LLM_MODEL: str = "llama-3.1-8b-instant"
    
    # Fallback models
    FALLBACK_MODELS: List[str] = [
        "llama-3.1-8b-instant",
        "llama3-8b-8192",
        "mixtral-8x7b-32768"
    ]

    # Embeddings
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Vector DB
    CHROMA_PERSIST_DIR: str = "./vectorstore"
    CHROMA_COLLECTION_NAME: str = "documents"

    # Database
    DATABASE_URL: str = "sqlite:///./agentic_rag.db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # LangSmith
    LANGSMITH_TRACING: bool = False
    LANGSMITH_ENDPOINT: str = "https://api.smith.langchain.com"
    LANGSMITH_API_KEY: Optional[str] = None
    LANGSMITH_PROJECT: str = "agentic-rag-nexus"

    # Document Processing
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: str = "pdf,txt,docx,md"
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    # Agent Settings
    MAX_ITERATIONS: int = 3
    CRITIC_MIN_SCORE: float = 7.0
    HUMAN_APPROVAL_TIMEOUT: int = 300

    @property
    def allowed_extensions_list(self) -> List[str]:
        return [ext.strip().lower() for ext in self.ALLOWED_EXTENSIONS.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()