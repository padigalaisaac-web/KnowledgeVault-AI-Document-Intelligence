"""API endpoints for document management and file ingestion."""
import os
import uuid
import hashlib
from typing import List, Optional
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings
from app.models.document import Document, DocumentChunk
from app.schemas.document import DocumentResponse, DocumentDetailResponse, ChunkResponse, DocumentUploadResponse
from app.services.ingestion import IngestionService
import json

router = APIRouter(prefix="/api/documents", tags=["Documents"])


def run_ingestion_background(document_id: str):
    """Background task runner for document indexing."""
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        IngestionService.process_document(document_id, db)
    finally:
        db.close()


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    collection_id: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Upload a document (PDF, TXT, MD), validate, save, and enqueue for background indexing.
    """
    # 1. Validate extension
    filename = file.filename or "uploaded_document"
    ext = Path(filename).suffix.lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )

    # 2. Read contents and check size
    content = await file.read()
    file_size = len(content)
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if file_size > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB."
        )

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty (0 bytes)."
        )

    # 3. Compute file hash for deduplication
    file_hash = hashlib.sha256(content).hexdigest()
    existing_doc = db.query(Document).filter(Document.file_hash == file_hash).first()
    if existing_doc:
        # If already indexed, notify duplicate or update collection
        if collection_id and existing_doc.collection_id != collection_id:
            existing_doc.collection_id = collection_id
            db.commit()
        return DocumentUploadResponse(
            message="Document already exists and is indexed.",
            document_id=existing_doc.id,
            filename=existing_doc.filename,
            status=existing_doc.status
        )

    # 4. Generate stable ID and persist file
    doc_id = str(uuid.uuid4())
    safe_name = f"{doc_id}_{filename.replace(' ', '_')}"
    target_path = settings.STORAGE_DIR / safe_name

    with open(target_path, "wb") as f:
        f.write(content)

    # 5. Determine MIME type
    mime_type = "application/pdf" if ext == ".pdf" else ("text/markdown" if ext == ".md" else "text/plain")

    # 6. Create initial document record
    doc = Document(
        id=doc_id,
        filename=filename,
        stored_path=str(target_path),
        file_size=file_size,
        file_type=mime_type,
        file_hash=file_hash,
        page_count=1,
        chunk_count=0,
        status="queued",
        collection_id=collection_id
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # 7. Kick off background processing
    background_tasks.add_task(run_ingestion_background, doc_id)

    return DocumentUploadResponse(
        message="Document uploaded successfully. Processing queued.",
        document_id=doc.id,
        filename=doc.filename,
        status=doc.status
    )


@router.get("", response_model=List[DocumentResponse])
def list_documents(
    collection_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List documents with optional collection and status filters."""
    query = db.query(Document)
    if collection_id:
        query = query.filter(Document.collection_id == collection_id)
    if status_filter:
        query = query.filter(Document.status == status_filter)

    return query.order_by(Document.created_at.desc()).all()


@router.get("/{document_id}", response_model=DocumentDetailResponse)
def get_document(document_id: str, db: Session = Depends(get_db)):
    """Retrieve detailed document metadata and its extracted chunks."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).order_by(DocumentChunk.chunk_index).all()
    chunk_responses = []
    for c in chunks:
        meta = json.loads(c.metadata_json) if c.metadata_json else {}
        chunk_responses.append(ChunkResponse(
            id=c.id,
            chunk_index=c.chunk_index,
            page_number=c.page_number,
            content=c.content,
            token_count=c.token_count,
            metadata=meta
        ))

    return DocumentDetailResponse(
        id=doc.id,
        filename=doc.filename,
        file_size=doc.file_size,
        file_type=doc.file_type,
        file_hash=doc.file_hash,
        page_count=doc.page_count,
        chunk_count=doc.chunk_count,
        status=doc.status,
        error_message=doc.error_message,
        collection_id=doc.collection_id,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        chunks=chunk_responses
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: str, db: Session = Depends(get_db)):
    """Delete document, physical file, and vector index embeddings."""
    success = IngestionService.delete_document(document_id, db)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return None


@router.post("/{document_id}/reprocess", response_model=DocumentResponse)
def reprocess_document(
    document_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Retry indexing for a failed or updated document."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    doc.status = "queued"
    doc.error_message = None
    db.commit()

    background_tasks.add_task(run_ingestion_background, document_id)
    return doc
