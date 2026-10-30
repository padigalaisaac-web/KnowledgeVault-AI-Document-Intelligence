"""Document Ingestion pipeline orchestrating validation, extraction, chunking, embedding, and indexing."""
import os
import shutil
import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.config import settings
from app.models.document import Document, DocumentChunk
from app.services.text_extractor import TextExtractor
from app.services.chunker import DocumentChunker
from app.services.embedding import embedding_service
from app.services.vector_store import vector_store
from app.services.bm25_retriever import bm25_retriever
import json
import logging

logger = logging.getLogger("knowledgevault.ingestion")


class IngestionService:
    """End-to-end document processing and vector indexing."""

    @classmethod
    def process_document(cls, document_id: str, db: Session) -> Document:
        """Run extraction, chunking, embedding, and indexing for a pending document."""
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise ValueError(f"Document not found: {document_id}")

        try:
            doc.status = "processing"
            db.commit()

            # 1. Page-by-page text extraction
            pages, meta = TextExtractor.extract(doc.stored_path, doc.file_type)
            doc.page_count = meta.get("page_count", len(pages)) or 1

            # 2. Chunking
            chunker = DocumentChunker(
                target_chunk_tokens=settings.CHUNK_SIZE,
                overlap_tokens=settings.CHUNK_OVERLAP
            )
            chunks = chunker.chunk_pages(
                document_id=doc.id,
                document_title=doc.filename,
                pages=pages,
                collection_id=doc.collection_id
            )

            if not chunks:
                doc.status = "failed"
                doc.error_message = "No extractable text was found in the document (it may be an image-only scan or empty)."
                db.commit()
                return doc

            # 3. Clean up any previous chunks from DB and vector stores (in case of reprocess)
            db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).delete()
            vector_store.delete_by_document(doc.id)
            bm25_retriever.delete_by_document(doc.id)

            # 4. Generate Embeddings in batches
            chunk_texts = [c.content for c in chunks]
            embeddings = embedding_service.embed_texts(chunk_texts)

            # 5. Upsert to Vector Store
            chunk_payloads = [c.to_dict() for c in chunks]
            vector_store.upsert_chunks(chunk_payloads, embeddings)

            # 6. Index into BM25
            bm25_retriever.index_chunks(chunk_payloads)

            # 7. Persist chunks in Relational DB
            for c in chunks:
                db_chunk = DocumentChunk(
                    id=c.chunk_id,
                    document_id=doc.id,
                    chunk_index=c.chunk_index,
                    page_number=c.page_number,
                    content=c.content,
                    content_hash=c.content_hash,
                    token_count=c.token_count,
                    metadata_json=json.dumps(c.metadata)
                )
                db.add(db_chunk)

            doc.chunk_count = len(chunks)
            doc.status = "indexed"
            doc.error_message = None
            db.commit()
            db.refresh(doc)
            logger.info("Successfully indexed document: %s (%d chunks, %d pages)", doc.filename, doc.chunk_count, doc.page_count)
            return doc

        except Exception as e:
            logger.error("Failed to process document %s: %s", doc.id, str(e), exc_info=True)
            doc.status = "failed"
            doc.error_message = str(e)
            db.commit()
            return doc

    @classmethod
    def reprocess(cls, document_id: str, db: Session) -> Document:
        """Retry ingestion for a failed or updated document."""
        return cls.process_document(document_id, db)

    @classmethod
    def delete_document(cls, document_id: str, db: Session) -> bool:
        """Completely remove a document, its file, vector embeddings, BM25 indices, and DB records."""
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            return False

        # 1. Remove vector store entries
        vector_store.delete_by_document(document_id)

        # 2. Remove BM25 entries
        bm25_retriever.delete_by_document(document_id)

        # 3. Remove physical file
        try:
            if doc.stored_path and os.path.exists(doc.stored_path):
                os.remove(doc.stored_path)
        except Exception as e:
            logger.warning("Could not delete file %s: %s", doc.stored_path, e)

        # 4. Remove database records (cascades to chunks)
        db.delete(doc)
        db.commit()
        return True
