"""Citation module to generate structured legal citations."""

from typing import Dict, Any


class CitationGenerator:
    @staticmethod
    def create_citation(document_name: str, rule_number: str, page_number: int = 1) -> Dict[str, Any]:
        """Creates citation object adhering to evidence_output.schema.json."""
        return {
            "document_name": document_name,
            "page_number": page_number,
            "rule_number": rule_number
        }
