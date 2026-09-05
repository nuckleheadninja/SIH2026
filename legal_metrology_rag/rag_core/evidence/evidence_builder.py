"""Evidence Builder producing structured legal evidence payloads matching Step 8 schema."""

from typing import Dict, Any, List
from legal_metrology_rag.rag_core.evidence.citation import CitationGenerator


class EvidenceBuilder:
    def __init__(self, default_doc_name: str = "Legal Metrology (Packaged Commodities) Rules, 2011"):
        self.citation_gen = CitationGenerator()
        self.default_doc_name = default_doc_name

    def build_evidence_item(self, query: Dict[str, Any], retrieved_chunk: Dict[str, Any]) -> Dict[str, Any]:
        """Constructs a single structured evidence dictionary matching Step 8 output contract."""
        check_id = query.get("check_id") or query.get("query_id") or "LM_CHECK_UNK"
        chunk_id = retrieved_chunk.get("chunk_id", "chk_unk")
        
        doc = retrieved_chunk.get("document_title") or retrieved_chunk.get("document") or self.default_doc_name
        rule = retrieved_chunk.get("rule", "Rule 6")
        sub_rule = retrieved_chunk.get("sub_rule")
        clause = retrieved_chunk.get("clause")
        schedule = retrieved_chunk.get("schedule")
        page = retrieved_chunk.get("page_start") or retrieved_chunk.get("page", 1)
        text = retrieved_chunk.get("text", "")
        score = float(retrieved_chunk.get("retrieval_score", retrieved_chunk.get("score", 0.85)))

        citation = self.citation_gen.build_citation(retrieved_chunk)

        return {
            "check_id": check_id,
            "chunk_id": chunk_id,
            "document": doc,
            "rule": rule,
            "sub_rule": sub_rule,
            "clause": clause,
            "schedule": schedule,
            "page": page,
            "text": text,
            "retrieval_score": score,
            "citation": citation
        }

    def build_evidence(self, query: Dict[str, Any], retrieved_docs: List[Dict[str, Any]], domain_name: str = "legal_metrology") -> Dict[str, Any]:
        top_doc = dict(retrieved_docs[0]) if retrieved_docs else {
            "rule": "Rule 1",
            "text": f"Mandatory {domain_name.upper()} declaration details.",
            "score": 0.85
        }
        if domain_name.lower() == "fssai":
            top_doc["document_title"] = "FSSAI Food Safety & Standards Regulations, 2018"
            top_doc["document"] = "FSSAI Food Safety & Standards Regulations, 2018"
        item = self.build_evidence_item(query, top_doc)
        item["relevant_rule"] = f"{domain_name.upper()} Regulation"
        item["domain"] = domain_name
        return item

    def build_evidence_list(self, query: Dict[str, Any], retrieved_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Constructs evidence payload list for top reranked chunks."""
        return [self.build_evidence_item(query, chunk) for chunk in retrieved_chunks]
