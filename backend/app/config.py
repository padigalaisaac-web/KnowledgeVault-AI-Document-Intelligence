"""Application configuration using Pydantic Settings."""
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


current_file = Path(__file__).resolve()
if (current_file.parent.parent.parent / "backend").exists():
    BASE_DIR = current_file.parent.parent.parent
elif (current_file.parent.parent / "app").exists():
    BASE_DIR = current_file.parent.parent
else:
    BASE_DIR = current_file.parent.parent.parent


class Settings(BaseSettings):
    """KnowledgeVault AI Application Settings."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_NAME: str = "KnowledgeVault AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Paths
    BASE_DIR: Path = BASE_DIR
    DATA_DIR: Path = BASE_DIR / "data"
    STORAGE_DIR: Path = BASE_DIR / "data" / "uploads"
    VECTOR_STORAGE_DIR: Path = BASE_DIR / "data" / "vector_storage"

    # Database
    DATABASE_URL: str = f"sqlite:///{BASE_DIR}/data/knowledgevault.db"

    # Vector Store (Qdrant)
    # If QDRANT_URL is set (e.g. http://localhost:6333), Qdrant REST client is used.
    # If not set, embedded persistent vector storage is used.
    QDRANT_URL: Optional[str] = None
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_COLLECTION: str = "knowledgevault_chunks"
    VECTOR_DIMENSION: int = 384

    # Embedding Model
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_BATCH_SIZE: int = 32
    LOAD_LOCAL_SENTENCE_TRANSFORMER: bool = False

    # Ingestion & Chunking
    CHUNK_SIZE: int = 700
    CHUNK_OVERLAP: int = 100
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".txt", ".md"]

    # Retrieval & RAG
    TOP_K: int = 5
    CANDIDATE_K: int = 20
    RRF_K: int = 60
    SIMILARITY_THRESHOLD: float = 0.20
    RERANKING_ENABLED: bool = False
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # LLM Provider Configuration
    # Supported: mock, openai, anthropic, gemini, ollama
    LLM_PROVIDER: str = "mock"
    LLM_MODEL: str = "mock-expert-v1"
    LLM_API_KEY: str = ""
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    LLM_API_BASE: Optional[str] = None
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 1024

    # Security & CORS
    CORS_ORIGINS: List[str] = [
        "*",
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]


settings = Settings()

# Ensure directories exist
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
settings.VECTOR_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
