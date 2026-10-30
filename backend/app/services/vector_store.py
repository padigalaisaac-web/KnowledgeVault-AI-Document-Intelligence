"""Vector Store supporting both Qdrant REST service and embedded persistent storage."""
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
import httpx
import logging
from app.config import settings

logger = logging.getLogger("knowledgevault.vector_store")


class VectorStore:
    """Vector database interface supporting Qdrant HTTP REST and embedded storage."""

    def __init__(
        self,
        qdrant_url: Optional[str] = settings.QDRANT_URL,
        collection_name: str = settings.QDRANT_COLLECTION,
        dimension: int = settings.VECTOR_DIMENSION,
        storage_dir: Path = settings.VECTOR_STORAGE_DIR
    ):
        self.qdrant_url = qdrant_url.rstrip("/") if qdrant_url else None
        self.collection_name = collection_name
        self.dimension = dimension
        self.storage_dir = storage_dir
        self.storage_file = storage_dir / f"{collection_name}.json"
        self._embedded_data: Dict[str, Dict[str, Any]] = {}

        if self.qdrant_url:
            self._init_qdrant_collection()
        else:
            self._load_embedded_storage()

    # ------------------ Embedded Storage Implementation ------------------

    def _load_embedded_storage(self):
        """Load persisted vectors from JSON file."""
        if self.storage_file.exists():
            try:
                with open(self.storage_file, "r", encoding="utf-8") as f:
                    self._embedded_data = json.load(f)
                logger.info("Loaded %d vectors from embedded store: %s", len(self._embedded_data), self.storage_file)
            except Exception as e:
                logger.warning("Failed to load embedded vector file (%s), initializing empty.", e)
                self._embedded_data = {}
        else:
            self._embedded_data = {}

    def _save_embedded_storage(self):
        """Persist embedded vectors atomically."""
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        temp_file = self.storage_file.with_suffix(".tmp")
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(self._embedded_data, f)
            temp_file.replace(self.storage_file)
        except Exception as e:
            logger.error("Failed to persist embedded vectors: %s", e)

    # ------------------ Qdrant HTTP Implementation ------------------

    def _init_qdrant_collection(self):
        """Ensure collection exists in Qdrant server."""
        try:
            url = f"{self.qdrant_url}/collections/{self.collection_name}"
            headers = {}
            if settings.QDRANT_API_KEY:
                headers["api-key"] = settings.QDRANT_API_KEY

            with httpx.Client(timeout=10.0) as client:
                res = client.get(url, headers=headers)
                if res.status_code == 404:
                    # Create collection
                    payload = {
                        "vectors": {
                            "size": self.dimension,
                            "distance": "Cosine"
                        }
                    }
                    create_res = client.put(url, json=payload, headers=headers)
                    create_res.raise_for_status()
                    logger.info("Created Qdrant collection: %s", self.collection_name)
                elif res.status_code == 200:
                    logger.info("Connected to existing Qdrant collection: %s", self.collection_name)
        except Exception as e:
            logger.warning("Qdrant server connection failed (%s). Falling back to embedded vector store.", e)
            self.qdrant_url = None
            self._load_embedded_storage()

    # ------------------ Public Vector Store API ------------------

    def upsert_chunks(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]]) -> None:
        """Insert or update chunks with their dense embeddings."""
        if not chunks or not embeddings:
            return

        if self.qdrant_url:
            try:
                points = []
                for chunk, emb in zip(chunks, embeddings):
                    points.append({
                        "id": chunk["chunk_id"],
                        "vector": emb,
                        "payload": chunk
                    })
                url = f"{self.qdrant_url}/collections/{self.collection_name}/points?wait=true"
                headers = {}
                if settings.QDRANT_API_KEY:
                    headers["api-key"] = settings.QDRANT_API_KEY

                with httpx.Client(timeout=30.0) as client:
                    res = client.put(url, json={"points": points}, headers=headers)
                    res.raise_for_status()
                return
            except Exception as e:
                logger.error("Failed to upsert points to Qdrant HTTP (%s). Saving to embedded store.", e)

        # Embedded store upsert
        for chunk, emb in zip(chunks, embeddings):
            self._embedded_data[chunk["chunk_id"]] = {
                "chunk_id": chunk["chunk_id"],
                "document_id": chunk.get("document_id"),
                "collection_id": chunk.get("metadata", {}).get("collection_id") or chunk.get("collection_id"),
                "vector": emb,
                "payload": chunk
            }
        self._save_embedded_storage()

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        collection_id: Optional[str] = None,
        document_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Dense cosine similarity search over vector store."""
        if self.qdrant_url:
            try:
                url = f"{self.qdrant_url}/collections/{self.collection_name}/points/search"
                headers = {}
                if settings.QDRANT_API_KEY:
                    headers["api-key"] = settings.QDRANT_API_KEY

                filter_conditions = []
                if collection_id:
                    filter_conditions.append({
                        "key": "collection_id",
                        "match": {"value": collection_id}
                    })
                if document_id:
                    filter_conditions.append({
                        "key": "document_id",
                        "match": {"value": document_id}
                    })

                search_payload: Dict[str, Any] = {
                    "vector": query_embedding,
                    "limit": top_k,
                    "with_payload": True,
                }
                if filter_conditions:
                    search_payload["filter"] = {"must": filter_conditions}

                with httpx.Client(timeout=10.0) as client:
                    res = client.post(url, json=search_payload, headers=headers)
                    res.raise_for_status()
                    data = res.json()
                    results = []
                    for item in data.get("result", []):
                        payload = item.get("payload", {})
                        payload["score"] = float(item.get("score", 0.0))
                        results.append(payload)
                    return results
            except Exception as e:
                logger.warning("Qdrant search failed (%s), searching embedded store.", e)

        # Embedded exact cosine search
        if not self._embedded_data:
            return []

        q_vec = np.array(query_embedding, dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)
        if q_norm > 1e-9:
            q_vec = q_vec / q_norm

        scored_items = []
        for cid, record in self._embedded_data.items():
            # Check collection filter
            if collection_id and record.get("collection_id") != collection_id:
                continue
            # Check document filter
            if document_id and record.get("document_id") != document_id:
                continue

            r_vec = np.array(record["vector"], dtype=np.float32)
            r_norm = np.linalg.norm(r_vec)
            if r_norm > 1e-9:
                r_vec = r_vec / r_norm

            cos_sim = float(np.dot(q_vec, r_vec))
            item = dict(record["payload"])
            item["score"] = cos_sim
            scored_items.append(item)

        scored_items.sort(key=lambda x: x["score"], reverse=True)
        return scored_items[:top_k]

    def delete_by_document(self, document_id: str) -> None:
        """Remove all points belonging to the given document."""
        if self.qdrant_url:
            try:
                url = f"{self.qdrant_url}/collections/{self.collection_name}/points/delete?wait=true"
                headers = {}
                if settings.QDRANT_API_KEY:
                    headers["api-key"] = settings.QDRANT_API_KEY

                payload = {
                    "filter": {
                        "must": [
                            {"key": "document_id", "match": {"value": document_id}}
                        ]
                    }
                }
                with httpx.Client(timeout=15.0) as client:
                    res = client.post(url, json=payload, headers=headers)
                    res.raise_for_status()
            except Exception as e:
                logger.warning("Failed to delete points from Qdrant HTTP (%s).", e)

        # Delete from embedded store
        to_delete = [cid for cid, rec in self._embedded_data.items() if rec.get("document_id") == document_id]
        for cid in to_delete:
            del self._embedded_data[cid]
        if to_delete:
            self._save_embedded_storage()

    def count_vectors(self) -> int:
        """Return total vector count."""
        return len(self._embedded_data)


# Singleton vector store instance
vector_store = VectorStore()
