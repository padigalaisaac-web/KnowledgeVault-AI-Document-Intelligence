"""BM25 sparse lexical retriever using rank_bm25."""
import re
from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi
import logging

logger = logging.getLogger("knowledgevault.bm25")


def tokenize_text(text: str) -> List[str]:
    """Tokenize text into lowercase alphanumeric words."""
    if not text:
        return []
    return re.findall(r"\b[a-zA-Z0-9_\-\.]+\b", text.lower())


class BM25Retriever:
    """In-memory BM25 lexical search over indexed document chunks."""

    def __init__(self):
        self.chunks: List[Dict[str, Any]] = []
        self.tokenized_corpus: List[List[str]] = []
        self.bm25_index: Optional[BM25Okapi] = None

    def index_chunks(self, new_chunks: List[Dict[str, Any]]) -> None:
        """Add or update chunks in the BM25 index."""
        # Remove any existing chunks with the same chunk_id
        new_ids = {c["chunk_id"] for c in new_chunks}
        self.chunks = [c for c in self.chunks if c["chunk_id"] not in new_ids]
        self.chunks.extend(new_chunks)
        self._rebuild_index()

    def delete_by_document(self, document_id: str) -> None:
        """Remove all chunks belonging to a document from the BM25 index."""
        self.chunks = [c for c in self.chunks if c.get("document_id") != document_id]
        self._rebuild_index()

    def _rebuild_index(self) -> None:
        """Recompute BM25Okapi index structures."""
        if not self.chunks:
            self.tokenized_corpus = []
            self.bm25_index = None
            return

        self.tokenized_corpus = [tokenize_text(c.get("content", "")) for c in self.chunks]
        self.bm25_index = BM25Okapi(self.tokenized_corpus)
        logger.info("Rebuilt BM25 index with %d chunks.", len(self.chunks))

    def search(
        self,
        query: str,
        top_k: int = 5,
        collection_id: Optional[str] = None,
        document_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search the BM25 index for the most relevant chunks."""
        if not self.bm25_index or not self.chunks or not query.strip():
            return []

        query_tokens = tokenize_text(query)
        if not query_tokens:
            return []

        scores = self.bm25_index.get_scores(query_tokens)

        # Pair chunks with scores and apply collection/document filters
        scored_candidates = []
        for i, chunk in enumerate(self.chunks):
            # Check collection filter
            chunk_coll = chunk.get("metadata", {}).get("collection_id") or chunk.get("collection_id")
            if collection_id and chunk_coll != collection_id:
                continue
            # Check document filter
            if document_id and chunk.get("document_id") != document_id:
                continue

            score = float(scores[i])
            if score > 0.0:
                item = dict(chunk)
                item["score"] = score
                scored_candidates.append(item)

        scored_candidates.sort(key=lambda x: x["score"], reverse=True)
        return scored_candidates[:top_k]


# Singleton instance
bm25_retriever = BM25Retriever()
