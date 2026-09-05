"""EmbedderConfig in rag_core."""

from dataclasses import dataclass


@dataclass
class EmbedderConfig:
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    dimension: int = 384
    batch_size: int = 32
