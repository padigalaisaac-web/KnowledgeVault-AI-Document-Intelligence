# KnowledgeVault AI — AI-Powered Document Intelligence and Research Assistant

KnowledgeVault AI is an enterprise-grade research assistant and document intelligence application built around evidence-grounded Retrieval-Augmented Generation (RAG). It enables researchers, engineers, and analysts to upload complex document libraries (PDFs, Markdown, Plaintext), organize them into domain collections, ask nuanced cross-document questions, and receive factual, evidence-backed answers with verifiable page and chunk citations.

Zero silent hallucinations. Zero invented citations.

---

## Key Features

- **Hybrid Information Retrieval**: Dense semantic vector retrieval (Qdrant / `sentence-transformers`) paired with sparse lexical search (`rank_bm25` Okapi) fused via **Reciprocal Rank Fusion (RRF $k=60$)**, achieving **100% Recall@5** on benchmark evaluations.
- **Verifiable Page & Chunk Citations**: Every factual claim is mapped to internal chunk and document IDs. Citations reference the exact source PDF page and excerpt, viewable in an interactive provenance drawer.
- **Anti-Hallucination & Honest Fallback**: If retrieved evidence lacks sufficient support or answers are absent, KnowledgeVault AI explicitly states insufficient information rather than speculating.
- **Prompt-Injection Defense**: Document contents are treated as untrusted passive data isolated inside strict XML context boundaries, preventing adversarial instructions in documents from overriding system instructions.
- **Modular LLM Provider Adapter**: Seamlessly hot-swap between offline zero-cost `MockProvider` (for deterministic testing), `OpenAI`, `Anthropic Claude`, `Google Gemini`, and local `Ollama` without rewriting retrieval pipelines.
- **Interactive Evaluation Dashboard**: Built-in benchmark suite measuring Recall@K, Mean Reciprocal Rank (MRR), Context Precision, Faithfulness, and Latency against curated ground truth questions, with one-click JSON/CSV exports.
- **Dual Persistence Architecture**: Runs out-of-the-box locally with SQLite (WAL mode) and embedded persistent vector storage, or in multi-container production with PostgreSQL 16 and dedicated Qdrant clusters.

---

## Architecture Overview

```
+-----------------------------------------------------------------------------------------+
|                                    USER INTERFACE                                       |
|  React 18 + Vite 6 + TypeScript + Tailwind CSS (Responsive Desktop / Tablet / Mobile)   |
|  Workspace Dashboard | Document Library | Research Chat | Benchmarks | Settings        |
+--------------------------------------------+--------------------------------------------+
                                             | HTTP / JSON REST
                                             v
+-----------------------------------------------------------------------------------------+
|                               FASTAPI APPLICATION GATEWAY                               |
|  CORS Middleware | Pydantic Request/Response Validation | Dependency Injection Session  |
+----+----------------------+--------------------+--------------------+-------------------+
     |                      |                    |                    |
     v                      v                    v                    v
+----+---------+     +------+--------+    +------+--------+    +------+--------+
|  COLLECTIONS |     |   DOCUMENTS   |    | RESEARCH CHAT |    |  EVALUATION   |
|  API ROUTER  |     |   API ROUTER  |    |  API ROUTER   |    |  API ROUTER   |
+----+---------+     +------+--------+    +------+--------+    +------+--------+
     |                      |                    |                    |
     v                      v                    v                    v
+----+-----------------+----+     +----+------+----+----+-------------+-------------------+
|     RELATIONAL STORE      |     |  DENSE VECTOR  |      SPARSE BM25 INVERTED INDEX      |
| PostgreSQL / SQLite (WAL) |     | Qdrant Server  | rank_bm25 Okapi Lexical Index        |
| Documents, Chunks, Chats, |     | / Embedded Disk| Tokenized Corpus with                |
| Evaluation Runs & Results |     | 384-dim Cosine | Collection & Document Filtering      |
+---------------------------+     +----------------+--------------------------------------+
```

Detailed architectural blueprints, data flow specifications, and ADRs are documented in [ARCHITECTURE.md](file:///c:/Users/padig/OneDrive/Desktop/KNOWLEDGEVAULT%20AI/ARCHITECTURE.md) and [docs/architecture-decisions.md](file:///c:/Users/padig/OneDrive/Desktop/KNOWLEDGEVAULT%20AI/docs/architecture-decisions.md).

---

## Empirical Benchmark Results

Evaluation was executed across our version-controlled 30-question benchmark dataset (`data/benchmark_dataset.json`):

| Experiment | Retrieval Mode | Recall@5 | MRR | Context Precision | Faithfulness | Citation Support | Avg Latency |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Experiment A** | **Dense Vector Baseline** | 50.00% | 0.4333 | 45.50% | 67.85% | 76.67% | **0.40 ms** |
| **Experiment B** | **Hybrid Retrieval (RRF)** | **100.00%** | 0.8111 | 85.17% | **91.86%** | **100.00%** | 0.65 ms |
| **Experiment C** | **Hybrid + Cross-Encoder Rerank** | **100.00%** | **0.8333** | **87.50%** | **91.86%** | **100.00%** | 0.73 ms |

> Hybrid retrieval doubled Recall@5 from 50% to 100%, and Reciprocal Rank Fusion boosted MRR by **+87.2%** over dense search alone. Read the full evaluation report in [EVALUATION.md](file:///c:/Users/padig/OneDrive/Desktop/KNOWLEDGEVAULT%20AI/EVALUATION.md).

---

## Quickstart Guide

### 1. Zero-Dependency Local Setup
```bash
# 1. Clone repository and copy sample environment
cp .env.example .env

# 2. Setup Python environment and install dependencies
python -m venv backend/.venv
# Windows: backend\.venv\Scripts\activate | Linux: source backend/.venv/bin/activate
pip install -r backend/requirements.txt

# 3. Build Frontend SPA
cd frontend
npm install
npm run build
cd ..

# 4. Seed sample research documents & run benchmark
python scripts/seed_and_evaluate.py

# 5. Start unified server
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```
Open [http://127.0.0.1:8000](http://127.0.0.1:8000) to access the complete application.

### 2. Multi-Container Docker Deployment
```bash
docker-compose up -d --build
```
- Web Application: [http://localhost:80](http://localhost:80)
- Backend API & Swagger: [http://localhost:8000/docs](http://localhost:8000/docs)
- Qdrant Vector Console: [http://localhost:6333/dashboard](http://localhost:6333/dashboard)

Complete deployment guides and cloud production configs are detailed in [DEPLOYMENT.md](file:///c:/Users/padig/OneDrive/Desktop/KNOWLEDGEVAULT%20AI/DEPLOYMENT.md).

---

## Automated Test Suite

Run unit and integration tests covering extraction, chunking, embeddings, hybrid retrieval, citation validation, prompt injection defense, and API endpoints:

```bash
pytest backend/tests/ -v
```

```
backend/tests/test_api_integration.py::test_health_check_handler PASSED  [  8%]
backend/tests/test_api_integration.py::test_collection_handlers PASSED   [ 16%]
backend/tests/test_api_integration.py::test_document_ingestion_and_rag_chat PASSED [ 25%]
backend/tests/test_api_integration.py::test_settings_handlers PASSED     [ 33%]
backend/tests/test_api_integration.py::test_evaluation_benchmark_handler PASSED [ 41%]
backend/tests/test_unit_pipeline.py::test_normalize_whitespace PASSED    [ 50%]
backend/tests/test_unit_pipeline.py::test_chunker_metadata_preservation PASSED [ 58%]
backend/tests/test_unit_pipeline.py::test_embedding_dimensions_and_norm PASSED [ 66%]
backend/tests/test_unit_pipeline.py::test_citation_validation_and_rejection PASSED [ 75%]
backend/tests/test_unit_pipeline.py::test_insufficient_evidence_detection PASSED [ 83%]
backend/tests/test_unit_pipeline.py::test_mock_provider_grounding_and_unanswerable PASSED [ 91%]
backend/tests/test_unit_pipeline.py::test_prompt_injection_defense PASSED [100%]
============================= 12 passed in 0.99s ==============================
```

---

## Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | React 18, TypeScript, Vite 6, Tailwind CSS, Lucide Icons |
| **Backend Framework** | Python 3.11, FastAPI, Pydantic v2, Uvicorn |
| **Document Processing** | PyMuPDF (fitz), pypdf fallback, Custom Sentence/Paragraph Sliding Chunker |
| **Vector & Lexical Search** | Qdrant (HTTP & Embedded), `rank-bm25` (Okapi), Reciprocal Rank Fusion (RRF) |
| **Embeddings & Reranking** | `sentence-transformers/all-MiniLM-L6-v2`, `ms-marco-MiniLM-L-6-v2` |
| **Database & ORM** | SQLAlchemy 2.0, SQLite (WAL mode) / PostgreSQL 16 |
| **DevOps & Containers** | Docker, Multi-Stage Dockerfiles, Docker Compose |

---

## Limitations & Future Extensions

- **Scanned Image PDFs (OCR)**: Scanned PDFs with no embedded text are flagged with informative warnings during extraction. Future extensions can integrate Tesseract OCR or docTR as an asynchronous background worker.
- **Hierarchical Chunking**: Future iterations can implement parent-document retrieval where small chunks are matched and broader parent sections are expanded into context.
- **Multi-Modal Retrieval**: Support for image, diagram, and table extraction within PDFs using multimodal vision models.

---

## License

This project is released under the **MIT License**.
