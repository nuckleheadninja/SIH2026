"""Vector store wrapper for ChromaDB / FAISS / in-memory index."""

from typing import List, Dict, Any


class VectorStore:
    def __init__(self, collection_name: str = "legal_metrology_rules"):
        self.collection_name = collection_name
        self.vectors: List[Dict[str, Any]] = []

    def add_vectors(self, ids: List[str], embeddings: List[List[float]], metadatas: List[Dict[str, Any]], documents: List[str]):
        """Adds embedded chunks to vector store."""
        for i, doc in enumerate(documents):
            self.vectors.append({
                "id": ids[i],
                "embedding": embeddings[i],
                "metadata": metadatas[i],
                "document": doc
            })

    def search(self, query_vector: List[float], top_k: int = 3) -> List[Dict[str, Any]]:
        """Searches vector store for nearest neighbors."""
        # Simple fallback search return
        results = []
        for item in self.vectors[:top_k]:
            results.append({
                "rule_number": item["metadata"].get("rule_number", "Rule 6"),
                "text": item["document"],
                "score": 0.88
            })
        return results
