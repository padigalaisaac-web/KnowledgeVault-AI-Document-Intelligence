# KnowledgeVault AI — Architecture Specification

## 1. System Overview

KnowledgeVault AI is an enterprise-grade document intelligence and research assistant engineered around evidence-grounded Retrieval-Augmented Generation (RAG). It combines dense semantic retrieval, sparse lexical search, Reciprocal Rank Fusion (RRF), optional Cross-Encoder reranking, and server-side citation validation with verifiable document and page provenance.

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
     |                      v                    v                    |
     |               +---------------+   +-------------------+        |
     |               | Ingestion     |   | RAG Orchestration |        |
     |               | Engine        |   | Engine            |        |
     |               +-------+-------+   +---------+---------+        |
     |                       |                     |                  |
     |                       |                     v                  |
     |                       |           +-------------------+        |
     |                       |           | Hybrid Retriever  |        |
     |                       |           | (RRF + Reranker)  |        |
     |                       |           +----+---------+----+        |
     |                       v                |         |             v
     |          +------------+------------+   |         |     +-------+-------+
     |          | PyMuPDF / Chunker /     |   |         |     | Benchmark     |
     |          | SentenceTransformers    |   |         |     | Runner Engine |
     |          +------+---------------+--+   |         |     +-------+-------+
     |                 |               |      |         |             |
     v                 v               v      v         v             v
+----+-----------------+----+     +----+------+----+----+-------------+-------------------+
|     RELATIONAL STORE      |     |  DENSE VECTOR  |      SPARSE BM25 INVERTED INDEX      |
| PostgreSQL / SQLite (WAL) |     | Qdrant Server  | rank_bm25 Okapi Lexical Index        |
| Documents, Chunks, Chats, |     | / Embedded Disk| Tokenized Corpus with                |
| Evaluation Runs & Results |     | 384-dim Cosine | Collection & Document Filtering      |
+---------------------------+     +----------------+--------------------------------------+
```

---

## 2. Ingestion Pipeline

1. **Validation & Hashing**: Incoming files (`.pdf`, `.txt`, `.md`) are validated against a 50MB ceiling. A SHA-256 content hash is computed immediately to prevent redundant duplicate ingestions.
2. **Persistent Storage**: Files are saved to `data/uploads/{document_id}_{filename}` with safe filenames.
3. **High-Fidelity Text Extraction**:
   - For PDFs, `PyMuPDF` iterates through each page, tracking 1-based page numbers. It detects pages with low character counts (<30 chars) and flags potential scanned/image pages.
   - For Markdown/Plaintext, contents are normalized while preserving headings and paragraph breaks.
4. **Sliding-Window Chunking**:
   - `DocumentChunker` splits text into ~700-token chunks with 100-token overlap (~4 chars/token).
   - Paragraph and sentence boundaries are preserved to prevent truncating semantic clauses.
   - Each chunk preserves `document_id`, `chunk_id` (`{doc_id}_c{index}`), `page_number`, `chunk_index`, `token_count`, and a content hash.
5. **Dual Indexing**:
   - Dense embeddings (384 dimensions) are generated using `sentence-transformers/all-MiniLM-L6-v2` (or the L2-normalized deterministic semantic projector).
   - Embeddings and metadata payloads are upserted to Qdrant (or embedded disk store).
   - Tokenized chunk representations are added to the in-memory `BM25Okapi` index.
6. **State Transition**: Relational database status moves from `QUEUED` -> `PROCESSING` -> `INDEXED` (or `FAILED` with explicit error logs).

---

## 3. Hybrid Information Retrieval (Dense + Sparse + RRF)

Query processing follows a dual-channel retrieval architecture:

$$\text{RRF\_Score}(d) = \frac{w_{\text{dense}}}{k + \text{rank}_{\text{dense}}(d)} + \frac{w_{\text{bm25}}}{k + \text{rank}_{\text{bm25}}(d)}$$

- $k = 60$ (smoothing constant preventing high-ranking outliers from dominating).
- $w_{\text{dense}} = 0.5$, $w_{\text{bm25}} = 0.5$.
- Candidate pool: top 20 candidates retrieved from each channel ($K_{\text{candidate}} = 20$).
- Normalized to $[0, 1]$ range.
- Filtered by configurable `similarity_threshold` (default 0.20).
- **Optional Cross-Encoder Reranking**: When `rerank=True`, candidate passages are scored using cross-attention relevance before slicing the final top-k passages ($K=5$).

---

## 4. Prompt Engineering & Citation Engine

### Prompt-Injection Defense
Document excerpts are untrusted user inputs. The system fences retrieved content within strict XML boundary tags:

```xml
<context>
[DOCUMENT_ID: doc_1] [CHUNK_ID: doc_1_c0] [PAGE: 2]
Random Forest utilizes bootstrap aggregating (bagging)...
---
[DOCUMENT_ID: doc_1] [CHUNK_ID: doc_1_c1] [PAGE: 3]
Gradient boosting fits pseudo-residuals sequentially...
</context>

User Question: {user_query}

Answer (remember to append [cite:DOCUMENT_ID:CHUNK_ID] to every claim):
```

### Citation Validation
The server intercepts the raw LLM output and executes deterministic checks:
1. Regex matches `[cite:DOCUMENT_ID:CHUNK_ID]`.
2. Verifies that `CHUNK_ID` exists in the retrieved evidence pool.
3. If an LLM hallucinates an unretrieved chunk ID, the tag is stripped.
4. Valid tags are substituted with numbered footnotes: `[1]`, `[2]`.
5. Provenance payloads (document title, page number, verified excerpt) are attached to the API response.
6. If the LLM indicates insufficient information, or if zero valid citations support the answer, confidence is marked `insufficient_evidence`.

---

## 5. Database Schema & Entities

- `collections`: Unique name, description, timestamps.
- `documents`: Filename, stored path, file size, MIME type, SHA-256 hash, page count, chunk count, status (`uploading`, `queued`, `processing`, `indexed`, `failed`), error message, collection foreign key.
- `document_chunks`: Stable chunk ID, document foreign key, chunk index, page number, content, content hash, token count, metadata JSON.
- `conversations`: Conversation ID, title, collection filter, timestamps.
- `messages`: Role (`user`, `assistant`), content, serialized citations JSON, confidence, retrieval mode, latency ms.
- `evaluation_runs`: Experiment run ID, name, retrieval mode, total questions, Recall@5, MRR, Context Precision, Faithfulness, Citation Support Rate, Avg Latency ms, Error Rate, serialized results JSON.
