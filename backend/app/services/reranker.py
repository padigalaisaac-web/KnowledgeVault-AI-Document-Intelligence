"""Optional Cross-Encoder reranker for fine-grained semantic scoring."""
import re
from typing import List, Dict, Any
import logging
from app.config import settings

logger = logging.getLogger("knowledgevault.reranker")


class PassageReranker:
    """Reranker using CrossEncoder or token-alignment heuristic."""

    def __init__(self, model_name: str = settings.RERANKER_MODEL):
        self.model_name = model_name
        self._cross_encoder = None
        self._load_model()

    def _load_model(self):
        """Attempt to load sentence_transformers CrossEncoder only if explicitly enabled."""
        if not getattr(settings, "LOAD_LOCAL_SENTENCE_TRANSFORMER", False):
            self._cross_encoder = None
            return

        try:
            from sentence_transformers import CrossEncoder
            self._cross_encoder = CrossEncoder(self.model_name)
            logger.info("Loaded CrossEncoder model: %s", self.model_name)
        except Exception as e:
            logger.info("CrossEncoder unavailable (%s). Using semantic alignment reranker.", e)
            self._cross_encoder = None

    def rerank(self, query: str, candidates: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        """Rerank candidate passages against query."""
        if not candidates:
            return []

        if len(candidates) <= 1:
            return candidates[:top_k]

        if self._cross_encoder is not None:
            try:
                pairs = [[query, c.get("content", "")] for c in candidates]
                scores = self._cross_encoder.predict(pairs)
                for i, score in enumerate(scores):
                    candidates[i]["rerank_score"] = float(score)
                candidates.sort(key=lambda x: x.get("rerank_score", 0.0), reverse=True)
                return candidates[:top_k]
            except Exception as e:
                logger.warning("CrossEncoder prediction failed (%s). Using fallback reranking.", e)

        # High-precision token alignment & exact phrase coverage reranker
        q_tokens = [t.lower() for t in re.findall(r"\b\w+\b", query)]
        q_phrases = [p.strip().lower() for p in query.split() if len(p) > 3]

        for cand in candidates:
            content = cand.get("content", "").lower()
            token_hits = sum(1 for t in q_tokens if t in content)
            token_cov = token_hits / max(len(q_tokens), 1)

            phrase_hits = sum(1 for p in q_phrases if p in content)
            phrase_cov = phrase_hits / max(len(q_phrases), 1)

            # Combined score: RRF score + token coverage + phrase boost
            base_score = cand.get("score", 0.5)
            cand["rerank_score"] = base_score * 0.4 + token_cov * 0.35 + phrase_cov * 0.25

        candidates.sort(key=lambda x: x.get("rerank_score", 0.0), reverse=True)
        return candidates[:top_k]


# Singleton reranker instance
passage_reranker = PassageReranker()
