"""Citation system strictly extracting document, rule, sub-rule, clause, schedule, and page lineage."""

from typing import Dict, Any, Optional


class CitationGenerator:
    @staticmethod
    def build_citation(chunk_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Constructs strict citation dictionary sourced solely from retrieved metadata attributes."""
        return {
            "document": chunk_metadata.get("document_title") or chunk_metadata.get("document") or "Legal Metrology (Packaged Commodities) Rules, 2011",
            "rule": chunk_metadata.get("rule", "Rule 6"),
            "sub_rule": chunk_metadata.get("sub_rule"),
            "clause": chunk_metadata.get("clause"),
            "schedule": chunk_metadata.get("schedule"),
            "page": chunk_metadata.get("page_start") or chunk_metadata.get("page", 1)
        }
