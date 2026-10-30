"""Pydantic schemas for research chat and citations."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class CitationItem(BaseModel):
    citation_id: str  # e.g. [1], [2]
    document_id: str
    document_title: str
    chunk_id: str
    page_number: Optional[int] = None
    excerpt: str
    score: float = 0.0


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Research question")
    conversation_id: Optional[str] = Field(None, description="Existing conversation ID")
    collection_id: Optional[str] = Field(None, description="Optional collection filter")
    retrieval_mode: str = Field("hybrid", description="dense, bm25, or hybrid")
    rerank: bool = Field(False, description="Enable cross-encoder reranking")
    top_k: Optional[int] = Field(None, ge=1, le=20)


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    sources: List[CitationItem] = []
    confidence: Optional[str] = None  # high, medium, low, insufficient_evidence
    retrieval_mode: Optional[str] = None
    latency_ms: Optional[float] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ConversationCreate(BaseModel):
    title: Optional[str] = "New Research Chat"
    collection_id: Optional[str] = None


class ConversationResponse(BaseModel):
    id: str
    title: str
    collection_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    messages: List[MessageResponse] = []
    model_config = ConfigDict(from_attributes=True)
