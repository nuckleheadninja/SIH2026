"""Structure-aware legal chunker producing chunks with full statutory metadata dictionary."""

import uuid
from typing import List, Dict, Any


class LegalChunker:
    def chunk_structured_sections(self, parsed_sections: List[Dict[str, Any]], doc_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Chunks parsed structural legal sections while embedding full Step 4 metadata attributes."""
        chunks = []

        for idx, sec in enumerate(parsed_sections, start=1):
            chunk_id = f"chk_{doc_metadata.get('domain', 'lm')}_{idx:03d}"
            
            chunk = {
                "chunk_id": chunk_id,
                "document_id": doc_metadata.get("document_id", "doc_lm_2011"),
                "document_title": doc_metadata.get("document_title", "Legal Metrology (Packaged Commodities) Rules, 2011"),
                "authority": doc_metadata.get("authority", "Ministry of Consumer Affairs, Food and Public Distribution, Government of India"),
                "jurisdiction": doc_metadata.get("jurisdiction", "India (Federal)"),
                "domain": doc_metadata.get("domain", "legal_metrology"),
                "part": sec.get("part", "Part II"),
                "chapter": sec.get("chapter", "Chapter II"),
                "rule": sec.get("rule", "Rule 6"),
                "sub_rule": sec.get("sub_rule"),
                "clause": sec.get("clause"),
                "schedule": sec.get("schedule"),
                "table": sec.get("table"),
                "page_start": sec.get("page_start", 1),
                "page_end": sec.get("page_end", 1),
                "effective_from": doc_metadata.get("effective_from", "2011-03-01"),
                "effective_to": doc_metadata.get("effective_to"),
                "status": doc_metadata.get("status", "current"),
                "amended_by": doc_metadata.get("amended_by", []),
                "supersedes": doc_metadata.get("supersedes"),
                "superseded_by": doc_metadata.get("superseded_by"),
                "chunk_type": "rule_clause",
                "text": sec.get("text", "")
            }
            chunks.append(chunk)

        return chunks
