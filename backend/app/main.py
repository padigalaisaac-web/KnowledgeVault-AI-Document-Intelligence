"""Main FastAPI application entry point for KnowledgeVault AI."""
import os
import json
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.config import settings
from app.database import engine, Base, get_db
from app.models import collection, document, conversation, evaluation
from app.api import collections, documents, chat, evaluation as eval_api, settings as settings_api
from app.services.bm25_retriever import bm25_retriever
from app.services.vector_store import vector_store
from app.models.document import DocumentChunk
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("knowledgevault")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle handler."""
    logger.info("Initializing KnowledgeVault AI backend...")
    
    # Create tables if not present
    Base.metadata.create_all(bind=engine)
    logger.info("Database schemas verified.")

    # Hydrate BM25 index from database
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        chunks = db.query(DocumentChunk).all()
        if chunks:
            payloads = []
            for c in chunks:
                meta = json.loads(c.metadata_json) if c.metadata_json else {}
                payloads.append({
                    "chunk_id": c.id,
                    "document_id": c.document_id,
                    "collection_id": meta.get("collection_id"),
                    "page_number": c.page_number,
                    "content": c.content,
                    "metadata": meta
                })
            bm25_retriever.index_chunks(payloads)
            logger.info("Hydrated BM25 index with %d existing chunks.", len(payloads))
    except Exception as e:
        logger.warning("Could not hydrate BM25 index on startup: %s", e)
    finally:
        db.close()

    yield

    logger.info("KnowledgeVault AI shutting down cleanly.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Evidence-grounded Document Intelligence & Research Assistant with Hybrid RAG.",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(collections.router)
app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(eval_api.router)
app.include_router(settings_api.router)


@app.get("/health", tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    """Health check verifying database connection and vector store readiness."""
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception as e:
        logger.error("Health check DB probe failed: %s", e)

    vector_count = vector_store.count_vectors()

    return {
        "status": "healthy" if db_ok else "degraded",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "database_connected": db_ok,
        "vector_store_ready": True,
        "indexed_vector_count": vector_count,
        "llm_provider": settings.LLM_PROVIDER,
        "embedding_model": settings.EMBEDDING_MODEL
    }


# Mount static production frontend if built
dist_candidates = [
    settings.BASE_DIR / "frontend" / "dist",
    settings.BASE_DIR / "dist",
    Path("/app/frontend/dist"),
    Path("/app/dist")
]
for dist_dir in dist_candidates:
    if dist_dir.exists() and (dist_dir / "index.html").exists():
        from fastapi.staticfiles import StaticFiles
        app.mount("/", StaticFiles(directory=str(dist_dir), html=True), name="frontend")
        logger.info("Mounted production frontend from: %s", dist_dir)
        break

