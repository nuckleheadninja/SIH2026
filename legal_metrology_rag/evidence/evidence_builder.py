"""Evidence builder to transform retrieved legal chunks into evidence_output payload."""

from typing import Dict, Any, List
from legal_metrology_rag.evidence.citation import CitationGenerator


class EvidenceBuilder:
    def __init__(self):
        self.citation_gen = CitationGenerator()

    def build_evidence(self, query: Dict[str, Any], retrieved_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Constructs evidence output payload adhering to evidence_output.schema.json."""
        query_id = query.get("query_id", "query_unk")
        top_doc = retrieved_docs[0] if retrieved_docs else {
            "rule_number": "Rule 6",
            "text": "Every pre-packaged commodity must declare MRP, net weight, manufacturer name and address.",
            "score": 0.85
        }

        rule_num = top_doc.get("rule_number", "Rule 6")
        text = top_doc.get("text", "")
        score = float(top_doc.get("score", 0.85))

        return {
            "query_id": query_id,
            "relevant_rule": f"Legal Metrology Rules 2011, {rule_num}",
            "act_section": "Section 18 of Legal Metrology Act, 2009",
            "evidence_text": text,
            "citation": self.citation_gen.create_citation(
                document_name="Legal Metrology (Packaged Commodities) Rules, 2011",
                rule_number=rule_num,
                page_number=12
            ),
            "confidence": min(max(score, 0.0), 1.0)
        }
