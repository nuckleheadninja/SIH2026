"""Legal Chunker to split documents respecting section/rule boundaries."""

from typing import List, Dict, Any


class LegalChunker:
    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_structured_sections(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Chunks parsed legal sections into vector-store-ready chunks."""
        chunks = []
        for idx, sec in enumerate(sections):
            chunks.append({
                "chunk_id": f"chk_{idx+1:03d}",
                "rule_number": sec.get("rule_number", "Unknown Rule"),
                "text": f"{sec.get('title', '')}: {sec.get('content', '')}",
                "metadata": {
                    "chapter": sec.get("chapter", ""),
                    "rule_number": sec.get("rule_number", "")
                }
            })
        return chunks
