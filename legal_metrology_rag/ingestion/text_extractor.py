"""Text Extractor for extracting plain text from legal documents."""

from typing import Dict, Any


class TextExtractor:
    def extract_text(self, document_info: Dict[str, Any]) -> str:
        """Extracts text content from document representation."""
        # Baseline text extractor stub
        filename = document_info.get("filename", "")
        return f"Legal Metrology (Packaged Commodities) Rules, 2011. Extracted content from {filename}."
