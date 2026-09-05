"""VectorRetriever in rag_core supporting vector similarity search with status filtering."""

from typing import List, Dict, Any, Optional
from legal_metrology_rag.rag_core.embeddings.embedder import LegalEmbedder


class VectorRetriever:
    def __init__(self, vector_store=None, embedder=None):
        self.vector_store = vector_store
        self.embedder = embedder or (vector_store.embedder if vector_store else LegalEmbedder())

    def retrieve(self, query: str, top_k: int = 20, status_filter: Optional[str] = "current") -> List[Dict[str, Any]]:
        if not self.vector_store:
            return []
        
        results = self.vector_store.search(query=query, top_k=top_k, status_filter=status_filter)
        for doc in results:
            doc["vector_score"] = float(doc.get("score", 0.0))
        return results

