# KnowledgeVault AI — Build Status & Progress Tracker

## Project Overview
**KnowledgeVault AI** is a production-minded AI-powered document intelligence and research assistant.
It provides hybrid retrieval-augmented generation (RAG) with dense semantic search (Qdrant), exact keyword retrieval (BM25), reciprocal rank fusion (RRF), cross-encoder reranking, evidence-grounded responses with verifiable page and chunk citations, interactive evaluation benchmarks, and complete document management.

---

## Stages & Milestones

- [x] **Stage 1: Workspace Inspection & Architecture Plan**
  - [x] Inspect environment (Windows ARM64 with x64/native Python, Node v22.23.4, npm 10.9.9)
  - [x] Record key technical decisions in `docs/architecture-decisions.md`
  - [x] Initialize project architecture blueprint

- [x] **Stage 2: Application Skeleton & Health Endpoints**
  - [x] FastAPI backend application structure with typed schemas and `/health`
  - [x] Frontend React + TypeScript + Vite + Tailwind CSS scaffolding
  - [x] Production static build integration and health probe verification

- [x] **Stage 3: Document Ingestion Pipeline**
  - [x] Document validation, SHA-256 deduplication hashing, and persistent file storage
  - [x] Page-by-page text extraction with PyMuPDF (fitz) and pypdf fallback (empty/scanned page detection)
  - [x] Sliding-window chunker preserving paragraph boundaries, document ID, chunk index, page number, and content hash
  - [x] 384-dimensional dense embedding generation (`all-MiniLM-L6-v2`) and Qdrant/embedded vector indexing
  - [x] State machine: `uploading` -> `queued` -> `processing` -> `indexed` (or `failed` with retry)

- [x] **Stage 4: Hybrid Retrieval Pipeline**
  - [x] Dense semantic vector search via Qdrant / embedded cosine store
  - [x] Sparse keyword retrieval via `rank_bm25` Okapi with collection/document filtering
  - [x] Reciprocal Rank Fusion (RRF $k=60$) score merger and threshold filter
  - [x] Optional Cross-Encoder passage reranking

- [x] **Stage 5: Grounded LLM Generation & Citation Engine**
  - [x] Pluggable provider adapter interface (OpenAI, Anthropic Claude, Google Gemini, Ollama, and offline MockProvider)
  - [x] Grounded prompt engineering with strict hallucination safeguards and citation format: `[cite:doc_id:chunk_id]`
  - [x] Server-side citation validator cross-referencing citations against retrieved chunks, rejecting hallucinated references
  - [x] Prompt-injection defense: strict untrusted document context boundary isolation (`<context>...</context>`)
  - [x] Honest insufficient-evidence fallback handling for absent or ambiguous questions

- [x] **Stage 6: Frontend Pages & User Experience**
  - [x] **Page A: Landing Page**: value proposition, architecture workflow illustration, honest security statement, CTAs
  - [x] **Page B: Research Workspace**: real backend metrics, recent documents, recent chats, collection summaries
  - [x] **Page C: Document Library**: drag-and-drop upload, real processing status pills, collections assignment, page-by-page chunk inspector drawer, delete/reprocess actions
  - [x] **Page D: AI Research Chat**: conversational thread sidebar, collection filter, retrieval method toggles, clickable citation badges `[1]`, `[2]` opening provenance popover with excerpt and page number, copy, retry, insufficient-evidence notification
  - [x] **Page E: Evaluation Dashboard**: real experimental metrics (Recall@5, MRR, Context Precision, Faithfulness, Latency), experiment comparison matrix, question prediction hit/miss table, one-click CSV and JSON export
  - [x] **Page F: System Settings**: retrieval hyperparameters (chunk size, overlap, top-k, threshold, reranking), LLM provider configuration, infrastructure health

- [x] **Stage 7: Evaluation Suite & Automated Testing**
  - [x] Curated 30-question benchmark dataset across factual, exact-term, paraphrase, comparison, and unanswerable questions
  - [x] Automated benchmark runner script (`scripts/seed_and_evaluate.py`)
  - [x] Verified empirical results: Dense (Recall@5: 50.0%, MRR: 0.4333) vs Hybrid RRF (Recall@5: 100.0%, MRR: 0.8111) vs Hybrid+Reranker (Recall@5: 100.0%, MRR: 0.8333)
  - [x] Full automated test suite (12 passed in 0.99s) covering extraction, chunking, embeddings, RRF, citation validation, prompt injection defense, and API handlers

- [x] **Stage 8: Docker, Deployment & Documentation**
  - [x] Multi-stage `Dockerfile.backend` and `Dockerfile.frontend`
  - [x] `docker-compose.yml` for PostgreSQL 16, Qdrant v1.12, backend, and frontend
  - [x] `.env.example` with complete configuration options
  - [x] Comprehensive documentation: `README.md`, `ARCHITECTURE.md`, `EVALUATION.md`, `DEPLOYMENT.md`, `docs/architecture-decisions.md`
