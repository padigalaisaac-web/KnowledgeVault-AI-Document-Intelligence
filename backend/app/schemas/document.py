"""Pydantic schemas for documents and chunks."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class ChunkResponse(BaseModel):
    id: str
    chunk_index: int
    page_number: Optional[int]
    content: str
    token_count: int
    metadata: Dict[str, Any] = Field(default_factory=dict)
    model_config = ConfigDict(from_attributes=True)


class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_size: int
    file_type: str
    file_hash: str
    page_count: int
    chunk_count: int
    status: str
    error_message: Optional[str] = None
    collection_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class DocumentDetailResponse(DocumentResponse):
    chunks: List[ChunkResponse] = []


class DocumentUpdate(BaseModel):
    filename: Optional[str] = Field(None, min_length=1, max_length=255)
    collection_id: Optional[str] = None


class DocumentUploadResponse(BaseModel):
    message: str
    document_id: str
    filename: str
    status: str
