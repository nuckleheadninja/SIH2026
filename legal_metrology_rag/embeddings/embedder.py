"""Embedder module for vector representation of legal texts."""

from typing import List
from legal_metrology_rag.embeddings.model_config import EmbedderConfig


class LegalEmbedder:
    def __init__(self, config: EmbedderConfig = None):
        self.config = config or EmbedderConfig()

    def embed_text(self, text: str) -> List[float]:
        """Generates embedding vector for input text (mock vector generator baseline)."""
        # Simple deterministic pseudo-vector for testing without heavy model download
        val = sum(ord(c) for c in text) % 100 / 100.0
        return [val] * self.config.dimension

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generates embedding vectors for a batch of texts."""
        return [self.embed_text(t) for t in texts]
