"""LegalEmbedder in rag_core using sentence-transformers/all-MiniLM-L6-v2 to generate dense embeddings for legal text."""

from typing import List, Union, Optional
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False


class LegalEmbedder:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", config=None):
        self.model_name = model_name
        self.config = config
        self._model = None

    @property
    def model(self):
        if self._model is None:
            if HAS_SENTENCE_TRANSFORMERS:
                self._model = SentenceTransformer(self.model_name)
            else:
                raise RuntimeError("sentence-transformers package is required for LegalEmbedder.")
        return self._model

    def embed_text(self, text: Union[str, List[float]]) -> List[float]:
        if isinstance(text, list):
            return [float(x) for x in text]
        if not isinstance(text, str):
            text = str(text)

        vec = self.model.encode(text, convert_to_numpy=True)
        return vec.tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        vecs = self.model.encode(texts, convert_to_numpy=True)
        return vecs.tolist()

