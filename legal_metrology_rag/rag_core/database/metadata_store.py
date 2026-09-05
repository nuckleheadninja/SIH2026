"""MetadataStore for managing document attributes, amendments, versioning, and effective period filtering."""

from typing import Dict, Any, List, Optional
from datetime import datetime


class MetadataStore:
    def __init__(self):
        self.store: Dict[str, Dict[str, Any]] = {}

    def insert(self, chunk_id: str, metadata: Dict[str, Any]):
        """Stores chunk metadata indexed by chunk_id."""
        self.store[chunk_id] = metadata

    def get(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves chunk metadata by chunk_id."""
        return self.store.get(chunk_id)

    def filter_current_provisions(self, chunks: List[Dict[str, Any]], query_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Filters out superseded or obsolete legal provisions.
        
        Safety Rule 2: Never treat an old/superseded rule as current law.
        """
        active_chunks = []
        target_date = query_date or datetime.now().strftime("%Y-%m-%d")

        for c in chunks:
            status = c.get("status", "current").lower()
            if status == "superseded":
                continue

            eff_from = c.get("effective_from")
            eff_to = c.get("effective_to")

            if eff_from and target_date < eff_from:
                continue
            if eff_to and target_date > eff_to:
                continue

            active_chunks.append(c)

        return active_chunks
