# KnowledgeVault AI — Architecture Decision Records (ADRs)

## ADR 001: Hybrid Information Retrieval (Dense + Sparse + RRF)
- **Status**: Accepted
- **Context**: Relying exclusively on dense semantic embeddings (e.g., `sentence-transformers/all-MiniLM-L6-v2`) frequently misses exact matches for technical identifiers, product codes, abbreviations, or specialized jargon. Conversely, keyword-only search (BM25) fails when users ask paraphrased or conceptual questions.
- **Decision**: Implement a hybrid retrieval pipeline combining:
  1. **Dense Vector Search**: Qdrant vector database using cosine similarity over embeddings.
  2. **Sparse Lexical Search**: BM25 algorithm (`rank_bm25`) indexing tokenized chunk contents.
  3. **Reciprocal Rank Fusion (RRF)**: Merges ranked lists using $RRF\_Score(d) = \sum \frac{1}{k + rank(d)}$ where $k=60$.
  4. **Optional Cross-Encoder Reranking**: Configurable flag to apply a cross-encoder model for fine-grained semantic scoring of the top candidate pool.
- **Consequences**: Significantly improved recall on both semantic and exact keyword queries. Zero vendor lock-in.

---

## ADR 002: Dual-Mode Persistence (SQLite/PostgreSQL & Embedded/Networked Qdrant)
- **Status**: Accepted
- **Context**: Developers need to run the application immediately without starting 4 Docker containers, but production environments require robust PostgreSQL and a standalone Qdrant cluster.
- **Decision**:
  - Relational Database: Use SQLAlchemy with declarative models and Alembic migrations. Default to SQLite (`sqlite:///./data/knowledgevault.db`) with foreign key enforcement for lightweight local development, while supporting PostgreSQL (`postgresql+psycopg2://...`) seamlessly via `DATABASE_URL`.
  - Vector Store: The `QdrantVectorStore` adapter supports both local filesystem persistence (`path="./data/qdrant_storage"`) and networked server mode (`url="http://localhost:6333"`), selectable via the `QDRANT_URL` environment variable.
- **Consequences**: Immediate out-of-the-box local developer experience with zero required external daemons, while remaining 100% production-ready for Docker Compose / Kubernetes.

---

## ADR 003: Deterministic & Verifiable Source Citations
- **Status**: Accepted
- **Context**: LLM hallucinations and invented citations destroy trust in research tools. Systems that only cite at document level fail to provide actionable provenance.
- **Decision**:
  - Every extracted chunk is tagged with its source document ID, sequential chunk ID, and exact PDF page number (derived from PyMuPDF page iteration).
  - The LLM prompt strictly requires outputting citations using machine-verifiable tags: `[cite:doc_id:chunk_id]`.
  - The backend citation validator scans the LLM output, verifies each referenced `chunk_id` against the retrieved candidate set, resolves document title and page number, and rejects or flags any hallucinated references.
  - The UI presents citations as interactive clickable badges that display an excerpt drawer/popover showing the exact grounding passage.
- **Consequences**: Verifiable document provenance with page numbers. Hallucinations are detected before answers reach the user.

---

## ADR 004: Anti-Hallucination & Prompt-Injection Safeguards
- **Status**: Accepted
- **Context**: Untrusted user documents might contain adversarial prompts ("Ignore previous instructions and do X"), or users might ask questions not answerable from their uploads.
- **Decision**:
  - System instructions are strictly demarcated from retrieved context using distinct XML/markdown containers (`<context>` ... `</context>`).
  - The LLM is explicitly instructed that context text is passive data, not instructions.
  - If retrieved passages have similarity below relevance thresholds or fail to contain relevant information, the system returns a standard honest insufficient-evidence notification instead of speculating.
- **Consequences**: Robust prompt-injection mitigation and honest attribution.

---

## ADR 005: Modular LLM Provider Adapter
- **Status**: Accepted
- **Context**: Users may use OpenAI, Anthropic Claude, Google Gemini, local Ollama, or run offline tests without API keys.
- **Decision**: Define a generic `LLMProvider` abstract base class with synchronous and asynchronous streaming methods. Implement:
  - `MockProvider`: Generates deterministic, grounded responses with verifiable citations from the supplied context. Used for automated tests, offline dev, and evaluation baselines.
  - `OpenAIProvider`: OpenAI API (GPT-4o, GPT-3.5-turbo, etc.).
  - `AnthropicProvider`: Anthropic Claude API (Claude 3.5 Sonnet, etc.).
  - `GeminiProvider`: Google Gemini API.
  - `OllamaProvider`: Local open-weights models.
- **Consequences**: Hot-swappable models without modifying the RAG retrieval core.

---

## ADR 006: Background Task Processing for Ingestion
- **Status**: Accepted
- **Context**: Ingesting large PDFs (extraction, chunking, embedding) can take several seconds to minutes and must never freeze the HTTP API.
- **Decision**: Use FastAPI `BackgroundTasks` / async queue with explicit database state machine:
  `UPLOADING` -> `QUEUED` -> `PROCESSING` -> `INDEXED` (or `FAILED` with retry capability).
- **Consequences**: Instantaneous API response with real-time progress polling or WebSocket updates.
