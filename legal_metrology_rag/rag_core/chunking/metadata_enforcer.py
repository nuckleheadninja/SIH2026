"""MetadataEnforcer module ensuring every chunk complies with Task 4 metadata schema."""

from typing import Dict, Any, List


class MetadataEnforcer:
    REQUIRED_SCHEMA_KEYS = [
        "chunk_id",
        "document_id",
        "document_title",
        "authority",
        "jurisdiction",
        "domain",
        "chapter",
        "rule",
        "sub_rule",
        "clause",
        "schedule",
        "table",
        "page_start",
        "page_end",
        "effective_from",
        "effective_to",
        "status",
        "amended_by",
        "supersedes",
        "superseded_by",
        "chunk_type",
        "text"
    ]

    def enforce_schema(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
        """Validates and completes chunk metadata attributes."""
        sanitized = {}
        for key in self.REQUIRED_SCHEMA_KEYS:
            val = chunk.get(key)
            if key in ("amended_by", "supersedes", "superseded_by") and val is None:
                val = []
            sanitized[key] = val
        return sanitized

    def enforce_schema_batch(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [self.enforce_schema(c) for c in chunks]
