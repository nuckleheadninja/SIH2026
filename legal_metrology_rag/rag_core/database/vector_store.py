"""VectorStore abstraction supporting add_documents(), search(), and delete() operations with metadata filtering."""

from typing import List, Dict, Any, Optional, Union
import numpy as np
from legal_metrology_rag.rag_core.embeddings.embedder import LegalEmbedder


class VectorStore:
    def __init__(self, collection_name: str = "legal_metrology", embedder: Optional[LegalEmbedder] = None):
        self.collection_name = collection_name
        self.embedder = embedder or LegalEmbedder()
        self.documents: Dict[str, Dict[str, Any]] = {}

    def add_documents(self, documents: List[Dict[str, Any]]):
        """Add documents with their embeddings and metadata to the vector store."""
        texts_to_embed = []
        docs_to_embed = []

        for doc in documents:
            doc_id = doc.get("chunk_id") or doc.get("id") or str(len(self.documents) + 1)
            if "embedding" in doc and doc["embedding"] is not None:
                emb = np.array(doc["embedding"], dtype=np.float32)
                norm = np.linalg.norm(emb)
                if norm > 0:
                    emb = emb / norm
                self.documents[doc_id] = {
                    **doc,
                    "chunk_id": doc_id,
                    "embedding": emb.tolist()
                }
            else:
                texts_to_embed.append(doc.get("text", ""))
                docs_to_embed.append((doc_id, doc))

        if texts_to_embed:
            embeddings = self.embedder.embed_batch(texts_to_embed)
            for (doc_id, doc), emb_list in zip(docs_to_embed, embeddings):
                emb = np.array(emb_list, dtype=np.float32)
                norm = np.linalg.norm(emb)
                if norm > 0:
                    emb = emb / norm
                self.documents[doc_id] = {
                    **doc,
                    "chunk_id": doc_id,
                    "embedding": emb.tolist()
                }

    def search(
        self,
        query: Union[str, List[float]],
        top_k: int = 5,
        status_filter: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for top_k documents most similar to the query.
        Supports status_filter (e.g. "current") and generic metadata filters.
        """
        if not self.documents:
            return []

        if isinstance(query, str):
            q_vec = np.array(self.embedder.embed_text(query), dtype=np.float32)
        else:
            q_vec = np.array(query, dtype=np.float32)

        q_norm = np.linalg.norm(q_vec)
        if q_norm > 0:
            q_vec = q_vec / q_norm

        results = []
        for doc_id, doc in self.documents.items():
            # Apply status filter if provided (defaulting missing status to "current")
            doc_status = doc.get("status", "current")
            if status_filter is not None and doc_status != status_filter:
                continue

            # Apply arbitrary metadata filters if provided
            if filters:
                match = True
                for k, v in filters.items():
                    if doc.get(k) != v:
                        match = False
                        break
                if not match:
                    continue

            d_vec = np.array(doc.get("embedding", []), dtype=np.float32)
            if len(d_vec) == len(q_vec):
                score = float(np.dot(q_vec, d_vec))
            else:
                score = 0.0

            doc_copy = {k: v for k, v in doc.items() if k != "embedding"}
            doc_copy["score"] = float(score)
            results.append(doc_copy)

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def delete(self, doc_id: str) -> bool:
        """Delete a document by chunk_id from the vector store."""
        if doc_id in self.documents:
            del self.documents[doc_id]
            return True
        return False

