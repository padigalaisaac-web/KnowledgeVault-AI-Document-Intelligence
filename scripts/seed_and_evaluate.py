"""Seed sample documents and run reproducible evaluation experiments."""
import os
import sys
import uuid
import hashlib
from pathlib import Path

# Add backend to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "backend"))

from app.database import Base, engine, SessionLocal
from app.models.collection import Collection
from app.models.document import Document
from app.services.ingestion import IngestionService
from app.services.evaluation_service import EvaluationService
from app.config import settings


def main():
    print("=== KnowledgeVault AI: Seeding Sample Documents & Benchmarking ===")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Create default collection
        coll = db.query(Collection).filter(Collection.name == "Machine Learning Papers").first()
        if not coll:
            coll = Collection(
                id=str(uuid.uuid4()),
                name="Machine Learning Papers",
                description="Core research guides on supervised, deep learning, and evaluation metrics."
            )
            db.add(coll)
            db.commit()
            db.refresh(coll)
            print(f"[+] Created collection: {coll.name} (id: {coll.id})")
        else:
            print(f"[*] Found collection: {coll.name}")

        # 2. Ingest Machine_Learning_Algorithms_Guide.md
        guide_path = BASE_DIR / "data" / "sample_documents" / "Machine_Learning_Algorithms_Guide.md"
        if not guide_path.exists():
            print(f"[!] Sample file not found: {guide_path}")
            return

        with open(guide_path, "r", encoding="utf-8") as f:
            content = f.read()

        file_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        existing_doc = db.query(Document).filter(Document.file_hash == file_hash).first()

        if existing_doc:
            doc_id = existing_doc.id
            print(f"[*] Document already exists: {existing_doc.filename} (id: {doc_id})")
            if existing_doc.status != "indexed":
                IngestionService.process_document(doc_id, db)
        else:
            doc_id = str(uuid.uuid4())
            target_file = settings.STORAGE_DIR / f"{doc_id}_Machine_Learning_Algorithms_Guide.md"
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(content)

            doc = Document(
                id=doc_id,
                filename="Machine_Learning_Algorithms_Guide.md",
                stored_path=str(target_file),
                file_size=len(content.encode("utf-8")),
                file_type="text/markdown",
                file_hash=file_hash,
                page_count=1,
                chunk_count=0,
                status="queued",
                collection_id=coll.id
            )
            db.add(doc)
            db.commit()
            print(f"[+] Saved document record: {doc.filename}")
            IngestionService.process_document(doc_id, db)
            print(f"[+] Indexed document: {doc.chunk_count} chunks generated.")

        # 3. Run Experiment A: Dense Retrieval
        print("\n--- Running Experiment A: Dense Retrieval ---")
        run_dense = EvaluationService.run_benchmark(
            db=db,
            name="Experiment A: Dense Retrieval Baseline",
            retrieval_mode="dense",
            top_k=5,
            rerank=False
        )
        print(f"Dense -> Recall@5: {run_dense.recall_at_k:.4f} | MRR: {run_dense.mrr:.4f} | Faithfulness: {run_dense.faithfulness:.4f} | Latency: {run_dense.avg_latency_ms:.2f}ms")

        # 4. Run Experiment B: Hybrid Retrieval (Dense + BM25 + RRF)
        print("\n--- Running Experiment B: Hybrid Retrieval (Dense + BM25 + RRF) ---")
        run_hybrid = EvaluationService.run_benchmark(
            db=db,
            name="Experiment B: Hybrid Retrieval (RRF)",
            retrieval_mode="hybrid",
            top_k=5,
            rerank=False
        )
        print(f"Hybrid -> Recall@5: {run_hybrid.recall_at_k:.4f} | MRR: {run_hybrid.mrr:.4f} | Faithfulness: {run_hybrid.faithfulness:.4f} | Latency: {run_hybrid.avg_latency_ms:.2f}ms")

        # 5. Run Experiment C: Hybrid Retrieval + Reranking
        print("\n--- Running Experiment C: Hybrid Retrieval + Reranking ---")
        run_rerank = EvaluationService.run_benchmark(
            db=db,
            name="Experiment C: Hybrid + Cross-Encoder Rerank",
            retrieval_mode="hybrid_rerank",
            top_k=5,
            rerank=True
        )
        print(f"Hybrid+Rerank -> Recall@5: {run_rerank.recall_at_k:.4f} | MRR: {run_rerank.mrr:.4f} | Faithfulness: {run_rerank.faithfulness:.4f} | Latency: {run_rerank.avg_latency_ms:.2f}ms")

        print("\n================== BENCHMARK COMPARISON TABLE ==================")
        print(f"{'Experiment':<35} | {'Recall@5':<10} | {'MRR':<8} | {'Precision':<10} | {'Faithfulness':<12} | {'Latency':<8}")
        print("-" * 95)
        for r in [run_dense, run_hybrid, run_rerank]:
            print(f"{r.name:<35} | {r.recall_at_k:<10.4f} | {r.mrr:<8.4f} | {r.context_precision:<10.4f} | {r.faithfulness:<12.4f} | {r.avg_latency_ms:<8.2f}ms")
        print("================================================================")

    finally:
        db.close()


if __name__ == "__main__":
    main()
