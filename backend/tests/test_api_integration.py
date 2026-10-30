"""Integration tests for API handlers: collections, documents, RAG chat, evaluation, and settings."""
import os
import uuid
import hashlib
from app.database import Base, engine, SessionLocal
from app.models.document import Document
from app.schemas.collection import CollectionCreate
from app.schemas.chat import ChatRequest
from app.schemas.evaluation import EvaluationRunRequest
from app.schemas.settings import SettingsUpdateRequest
from app.main import health_check
from app.api.collections import create_collection, list_collections, get_collection, delete_collection
from app.api.documents import list_documents, get_document, delete_document
from app.api.chat import chat_query, list_conversations
from app.api.evaluation import trigger_evaluation, list_evaluation_runs, export_evaluation_run
from app.api.settings import get_system_settings, update_system_settings
from app.services.ingestion import IngestionService
from app.config import settings


def setup_module():
    Base.metadata.create_all(bind=engine)


def test_health_check_handler():
    db = SessionLocal()
    try:
        res = health_check(db=db)
        assert res["status"] in ("healthy", "degraded")
        assert res["database_connected"] is True
        assert "version" in res
        assert "embedding_model" in res
    finally:
        db.close()


def test_collection_handlers():
    db = SessionLocal()
    try:
        # Create
        coll_in = CollectionCreate(name=f"Deep Learning {uuid.uuid4().hex[:6]}", description="Neural networks research")
        res_create = create_collection(payload=coll_in, db=db)
        assert res_create.id is not None
        assert res_create.name == coll_in.name

        # List
        all_colls = list_collections(db=db)
        assert any(c.id == res_create.id for c in all_colls)

        # Get
        single = get_collection(collection_id=res_create.id, db=db)
        assert single.id == res_create.id

        # Delete
        delete_collection(collection_id=res_create.id, db=db)
    finally:
        db.close()


def test_document_ingestion_and_rag_chat():
    db = SessionLocal()
    try:
        # 1. Create a real sample document file
        filename = f"test_ensemble_{uuid.uuid4().hex[:6]}.md"
        file_path = settings.STORAGE_DIR / filename
        content = (
            "# Ensemble Machine Learning Guide\n\n"
            "Random Forest is an ensemble method utilizing bagging and feature subsampling.\n\n"
            "It builds uncorrelated decision trees and outputs class predictions via majority voting.\n\n"
            "The Out-of-Bag (OOB) error estimates generalization performance without separate validation sets.\n"
        )
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        file_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        doc_id = str(uuid.uuid4())

        doc = Document(
            id=doc_id,
            filename=filename,
            stored_path=str(file_path),
            file_size=len(content.encode("utf-8")),
            file_type="text/markdown",
            file_hash=file_hash,
            page_count=1,
            chunk_count=0,
            status="queued"
        )
        db.add(doc)
        db.commit()

        # 2. Ingest document
        indexed_doc = IngestionService.process_document(doc_id, db)
        assert indexed_doc.status == "indexed"
        assert indexed_doc.chunk_count > 0

        # 3. List and get document details
        docs = list_documents(db=db)
        assert any(d.id == doc_id for d in docs)

        detail = get_document(document_id=doc_id, db=db)
        assert detail.id == doc_id
        assert len(detail.chunks) > 0
        assert detail.chunks[0].chunk_index == 0

        # 4. Ask RAG chat question
        chat_req = ChatRequest(
            message="How does Random Forest use Out-of-Bag (OOB) error?",
            retrieval_mode="hybrid",
            rerank=False,
            top_k=5
        )
        chat_res = chat_query(payload=chat_req, db=db)
        assert chat_res.role == "assistant"
        assert len(chat_res.content) > 0
        assert len(chat_res.sources) > 0
        assert any(s.document_id == doc_id for s in chat_res.sources)
        assert chat_res.confidence in ("high", "medium")

        # 5. Ask unanswerable question
        unans_req = ChatRequest(
            message="What is the speed of sound in liquid helium at absolute zero?",
            retrieval_mode="hybrid"
        )
        unans_res = chat_query(payload=unans_req, db=db)
        assert ("do not contain sufficient information" in unans_res.content.lower() or
                "insufficient evidence" in unans_res.content.lower() or
                unans_res.confidence == "insufficient_evidence")

        # 6. Verify conversation persistence
        convs = list_conversations(db=db)
        assert len(convs) > 0

        # 7. Delete document and verify cleanup
        delete_document(document_id=doc_id, db=db)
        assert not os.path.exists(file_path)

    finally:
        db.close()


def test_settings_handlers():
    db = SessionLocal()
    try:
        curr = get_system_settings(db=db)
        assert curr.app_name == "KnowledgeVault AI"

        update_req = SettingsUpdateRequest(top_k=8, similarity_threshold=0.21)
        updated = update_system_settings(payload=update_req, db=db)
        assert updated.top_k == 8
        assert updated.similarity_threshold == 0.21
    finally:
        db.close()


def test_evaluation_benchmark_handler():
    db = SessionLocal()
    try:
        # Run small benchmark experiment
        eval_req = EvaluationRunRequest(name="Automated Test Run", retrieval_mode="hybrid", top_k=3)
        run_res = trigger_evaluation(payload=eval_req, db=db)
        assert run_res.id is not None
        assert run_res.status == "completed"
        assert run_res.total_questions > 0
        assert run_res.mrr >= 0.0
        assert run_res.recall_at_k >= 0.0

        # Export benchmark run (JSON & CSV)
        json_export = export_evaluation_run(run_id=run_res.id, format="json", db=db)
        assert json_export.media_type == "application/json"

        csv_export = export_evaluation_run(run_id=run_res.id, format="csv", db=db)
        assert csv_export.media_type == "text/csv"
    finally:
        db.close()
