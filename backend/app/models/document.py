"""Document and DocumentChunk database models."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Text, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String(255), nullable=False)
    stored_path = Column(String(1024), nullable=False)
    file_size = Column(Integer, nullable=False, default=0)
    file_type = Column(String(100), nullable=False)
    file_hash = Column(String(64), nullable=False, index=True)
    page_count = Column(Integer, nullable=False, default=1)
    chunk_count = Column(Integer, nullable=False, default=0)
    
    # State machine: uploading -> queued -> processing -> indexed | failed
    status = Column(String(50), nullable=False, default="uploading", index=True)
    error_message = Column(Text, nullable=True)

    collection_id = Column(String(36), ForeignKey("collections.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    collection = relationship("Collection", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan", order_by="DocumentChunk.chunk_index")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(String(64), primary_key=True)  # stable ID: e.g. {doc_id}_{index}
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    page_number = Column(Integer, nullable=True)
    content = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=False)
    token_count = Column(Integer, nullable=False, default=0)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    document = relationship("Document", back_populates="chunks")

    __table_args__ = (
        Index("idx_chunk_doc_index", "document_id", "chunk_index"),
    )
