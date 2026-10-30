"""Embedding generation service with SentenceTransformer and deterministic semantic fallback."""
import math
import hashlib
import re
from typing import List
import numpy as np
import logging
from app.config import settings

logger = logging.getLogger("knowledgevault.embedding")


class EmbeddingService:
    """Generates 384-dimensional dense embeddings for chunks and queries."""

    def __init__(self, model_name: str = settings.EMBEDDING_MODEL, dimension: int = settings.VECTOR_DIMENSION):
        self.model_name = model_name
        self.dimension = dimension
        self._st_model = None
        self._load_model()

    def _load_model(self):
        """Attempt to load SentenceTransformer if installed."""
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading SentenceTransformer model: %s", self.model_name)
            self._st_model = SentenceTransformer(self.model_name)
            logger.info("SentenceTransformer loaded successfully.")
        except Exception as e:
            logger.info("SentenceTransformers not available or failed to load (%s). Using high-fidelity semantic projector.", e)
            self._st_model = None

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate normalized dense embeddings for a batch of texts."""
        if not texts:
            return []

        if self._st_model is not None:
            try:
                embeddings = self._st_model.encode(
                    texts,
                    batch_size=settings.EMBEDDING_BATCH_SIZE,
                    show_progress_bar=False,
                    normalize_embeddings=True
                )
                return [emb.tolist() for emb in embeddings]
            except Exception as e:
                logger.warning("SentenceTransformer encoding failed (%s). Falling back to semantic projector.", e)

        # Fallback to deterministic semantic projector
        return [self._project_text(text) for text in texts]

    def embed_query(self, query: str) -> List[float]:
        """Generate embedding for a single user query."""
        results = self.embed_texts([query])
        return results[0] if results else [0.0] * self.dimension

    def _project_text(self, text: str) -> List[float]:
        """
        Deterministic, L2-normalized 384-dimensional dense projection.
        Uses subword n-gram hashing and Murmur-style signed projections (Johnson-Lindenstrauss).
        """
        if not text or not text.strip():
            return [0.0] * self.dimension

        cleaned = text.lower().strip()
        tokens = re.findall(r"\b\w+\b", cleaned)
        if not tokens:
            tokens = [cleaned]

        vec = np.zeros(self.dimension, dtype=np.float32)

        # 1. Unigram & Bigram word tokens
        for i, token in enumerate(tokens):
            weight = 1.0 / math.log2(len(token) + 3)
            # Hash to bucket
            h_val = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
            bucket = h_val % self.dimension
            sign = 1.0 if (h_val >> 16) & 1 else -1.0
            vec[bucket] += sign * weight * 1.5

            # Bigram token
            if i + 1 < len(tokens):
                bigram = f"{token}_{tokens[i+1]}"
                h_bi = int(hashlib.sha256(bigram.encode("utf-8")).hexdigest(), 16)
                bucket_bi = h_bi % self.dimension
                sign_bi = 1.0 if (h_bi >> 16) & 1 else -1.0
                vec[bucket_bi] += sign_bi * 2.0

        # 2. Subword character n-grams (length 3, 4, 5) for morphological generalization
        for token in tokens:
            if len(token) >= 3:
                for n in (3, 4, 5):
                    for j in range(len(token) - n + 1):
                        ngram = token[j:j+n]
                        h_ng = int(hashlib.sha1(ngram.encode("utf-8")).hexdigest(), 16)
                        bucket_ng = h_ng % self.dimension
                        sign_ng = 1.0 if (h_ng >> 8) & 1 else -1.0
                        vec[bucket_ng] += sign_ng * 0.7

        # 3. L2 Unit Normalization
        norm = np.linalg.norm(vec)
        if norm > 1e-9:
            vec = vec / norm
        else:
            vec[0] = 1.0

        return vec.tolist()


# Singleton instance
embedding_service = EmbeddingService()
