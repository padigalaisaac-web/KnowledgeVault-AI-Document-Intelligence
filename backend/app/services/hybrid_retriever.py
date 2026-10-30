"""Hybrid information retriever using Reciprocal Rank Fusion (RRF) and optional reranking."""
import time
from typing import List, Dict, Any, Optional, Tuple
from app.config import settings
from app.services.embedding import embedding_service
from app.services.vector_store import vector_store
from app.services.bm25_retriever import bm25_retriever
from app.services.reranker import passage_reranker
import logging

logger = logging.getLogger("knowledgevault.hybrid_retriever")


class HybridRetriever:
    """Combines dense semantic search and BM25 lexical search using Reciprocal Rank Fusion."""

    def __init__(
        self,
        rrf_k: int = settings.RRF_K,
        default_top_k: int = settings.TOP_K,
        default_candidate_k: int = settings.CANDIDATE_K,
        similarity_threshold: float = settings.SIMILARITY_THRESHOLD,
    ):
        self.rrf_k = rrf_k
        self.default_top_k = default_top_k
        self.default_candidate_k = default_candidate_k
        self.similarity_threshold = similarity_threshold

    def retrieve(
        self,
        query: str,
        mode: str = "hybrid",
        top_k: Optional[int] = None,
        candidate_k: Optional[int] = None,
        collection_id: Optional[str] = None,
        document_id: Optional[str] = None,
        rerank: bool = False,
        similarity_threshold: Optional[float] = None
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Execute retrieval based on selected mode: 'dense', 'bm25', or 'hybrid'.
        Returns (ranked_chunks, metrics_dict).
        """
        start_time = time.perf_counter()
        top_k = top_k or self.default_top_k
        candidate_k = candidate_k or self.default_candidate_k
        threshold = similarity_threshold if similarity_threshold is not None else self.similarity_threshold

        dense_results: List[Dict[str, Any]] = []
        bm25_results: List[Dict[str, Any]] = []

        # 1. Dense retrieval branch
        if mode in ("dense", "hybrid", "hybrid_rerank"):
            query_emb = embedding_service.embed_query(query)
            dense_results = vector_store.search(
                query_embedding=query_emb,
                top_k=candidate_k,
                collection_id=collection_id,
                document_id=document_id
            )

        # 2. BM25 retrieval branch
        if mode in ("bm25", "hybrid", "hybrid_rerank"):
            bm25_results = bm25_retriever.search(
                query=query,
                top_k=candidate_k,
                collection_id=collection_id,
                document_id=document_id
            )

        # 3. Fusion or Selection
        if mode == "dense":
            merged = dense_results
        elif mode == "bm25":
            merged = bm25_results
        else:
            # Reciprocal Rank Fusion
            merged = self._reciprocal_rank_fusion(dense_results, bm25_results)

        # 4. Optional Reranking
        if rerank and merged:
            merged = passage_reranker.rerank(query, merged, top_k=top_k)
        else:
            merged = merged[:top_k]

        # 5. Threshold filtering
        filtered: List[Dict[str, Any]] = []
        for chunk in merged:
            score = chunk.get("score", 0.0)
            if score >= threshold:
                filtered.append(chunk)

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        metrics = {
            "mode": mode,
            "latency_ms": round(elapsed_ms, 2),
            "dense_candidate_count": len(dense_results),
            "bm25_candidate_count": len(bm25_results),
            "total_candidates": len(merged),
            "retained_count": len(filtered),
            "rerank_applied": rerank,
        }

        return filtered, metrics

    def _reciprocal_rank_fusion(
        self,
        dense_results: List[Dict[str, Any]],
        bm25_results: List[Dict[str, Any]],
        dense_weight: float = 0.5,
        bm25_weight: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Merge ranked lists using Reciprocal Rank Fusion (RRF):
        RRF_Score(d) = sum( weight / (k + rank(d)) )
        """
        rrf_scores: Dict[str, float] = {}
        chunk_map: Dict[str, Dict[str, Any]] = {}

        # Process dense ranks
        for rank, item in enumerate(dense_results, start=1):
            cid = item["chunk_id"]
            chunk_map[cid] = item
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (dense_weight / (self.rrf_k + rank))

        # Process BM25 ranks
        for rank, item in enumerate(bm25_results, start=1):
            cid = item["chunk_id"]
            if cid not in chunk_map:
                chunk_map[cid] = item
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (bm25_weight / (self.rrf_k + rank))

        # Normalize RRF scores to 0.0 - 1.0 range
        max_possible_rrf = (dense_weight / (self.rrf_k + 1)) + (bm25_weight / (self.rrf_k + 1))
        fused_items: List[Dict[str, Any]] = []

        for cid, score in rrf_scores.items():
            item = dict(chunk_map[cid])
            norm_score = round(min(1.0, score / max_possible_rrf), 4)
            item["score"] = norm_score
            item["rrf_raw"] = round(score, 6)
            fused_items.append(item)

        fused_items.sort(key=lambda x: x["score"], reverse=True)
        return fused_items


# Singleton retriever instance
hybrid_retriever = HybridRetriever()
