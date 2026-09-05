"""Metadata store for managing document attributes, amendments, and legal validity periods."""

from typing import Dict, Any, Optional


class MetadataStore:
    def __init__(self):
        self.store: Dict[str, Dict[str, Any]] = {}

    def insert(self, doc_id: str, metadata: Dict[str, Any]):
        self.store[doc_id] = metadata

    def get(self, doc_id: str) -> Optional[Dict[str, Any]]:
        return self.store.get(doc_id)
