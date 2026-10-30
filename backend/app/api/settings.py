"""API endpoints for application settings and system configuration."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings
from app.models.document import Document, DocumentChunk
from app.models.collection import Collection
from app.schemas.settings import SettingsResponse, SettingsUpdateRequest
from app.services.vector_store import vector_store

router = APIRouter(prefix="/api/settings", tags=["Settings"])


@router.get("", response_model=SettingsResponse)
def get_system_settings(db: Session = Depends(get_db)):
    """Retrieve current application configuration and storage counts."""
    doc_count = db.query(Document).count()
    chunk_count = db.query(DocumentChunk).count()
    coll_count = db.query(Collection).count()

    db_type = "PostgreSQL" if "postgresql" in settings.DATABASE_URL else "SQLite (WAL mode)"
    vs_type = f"Qdrant ({settings.QDRANT_URL})" if settings.QDRANT_URL else "Embedded Vector Store (Disk/Memory)"

    return SettingsResponse(
        app_name=settings.APP_NAME,
        app_version=settings.APP_VERSION,
        embedding_model=settings.EMBEDDING_MODEL,
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        top_k=settings.TOP_K,
        candidate_k=settings.CANDIDATE_K,
        rrf_k=settings.RRF_K,
        similarity_threshold=settings.SIMILARITY_THRESHOLD,
        reranking_enabled=settings.RERANKING_ENABLED,
        llm_provider=settings.LLM_PROVIDER,
        llm_model=settings.LLM_MODEL,
        max_upload_size_mb=settings.MAX_UPLOAD_SIZE_MB,
        database_type=db_type,
        vector_store_type=vs_type,
        total_documents=doc_count,
        total_chunks=chunk_count,
        total_collections=coll_count
    )


@router.put("", response_model=SettingsResponse)
def update_system_settings(payload: SettingsUpdateRequest, db: Session = Depends(get_db)):
    """Update runtime retrieval and model settings."""
    if payload.chunk_size is not None:
        settings.CHUNK_SIZE = payload.chunk_size
    if payload.chunk_overlap is not None:
        settings.CHUNK_OVERLAP = payload.chunk_overlap
    if payload.top_k is not None:
        settings.TOP_K = payload.top_k
    if payload.similarity_threshold is not None:
        settings.SIMILARITY_THRESHOLD = payload.similarity_threshold
    if payload.reranking_enabled is not None:
        settings.RERANKING_ENABLED = payload.reranking_enabled
    if payload.llm_provider is not None:
        settings.LLM_PROVIDER = payload.llm_provider
    if payload.llm_model is not None:
        settings.LLM_MODEL = payload.llm_model

    return get_system_settings(db)
