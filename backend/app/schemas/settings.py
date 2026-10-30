"""Pydantic schemas for application settings."""
from typing import Optional, List
from pydantic import BaseModel, Field


class SettingsResponse(BaseModel):
    app_name: str
    app_version: str
    embedding_model: str
    chunk_size: int
    chunk_overlap: int
    top_k: int
    candidate_k: int
    rrf_k: int
    similarity_threshold: float
    reranking_enabled: bool
    llm_provider: str
    llm_model: str
    max_upload_size_mb: int
    database_type: str
    vector_store_type: str
    total_documents: int = 0
    total_chunks: int = 0
    total_collections: int = 0


class SettingsUpdateRequest(BaseModel):
    chunk_size: Optional[int] = Field(None, ge=100, le=4000)
    chunk_overlap: Optional[int] = Field(None, ge=0, le=1000)
    top_k: Optional[int] = Field(None, ge=1, le=50)
    similarity_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    reranking_enabled: Optional[bool] = None
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
