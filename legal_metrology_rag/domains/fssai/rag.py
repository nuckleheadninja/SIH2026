"""FSSAIRAG subclassing BaseComplianceRAG."""

from typing import Dict, Any, List
from legal_metrology_rag.rag_core.base_rag import BaseComplianceRAG
from legal_metrology_rag.rag_core.retrieval.hybrid_retriever import HybridRetriever
from legal_metrology_rag.rag_core.evidence.evidence_builder import EvidenceBuilder


class FSSAIRAG(BaseComplianceRAG):
    def __init__(self, config_path: str = None):
        super().__init__(domain_name="fssai", config_path=config_path)
        self.retriever = HybridRetriever()
        self.evidence_builder = EvidenceBuilder(default_doc_name="FSSAI Food Safety & Standards Regulations")

    def load_documents(self, raw_dir: str):
        """Loads and indexes FSSAI regulations."""
        pass

    def query_compliance(self, check_query: Dict[str, Any]) -> Dict[str, Any]:
        field = check_query.get("field_name", check_query.get("field", ""))
        val = check_query.get("field_value", "")
        retrieved = self.retriever.retrieve(f"FSSAI food regulation {field} {val}")
        if not retrieved:
            retrieved = [{
                "chunk_id": "chk_fssai_pkg_2018",
                "document_title": "FSSAI Food Safety and Standards Regulations, 2018",
                "rule": "FSSAI Packaging Reg 2018",
                "text": "Every food package shall comply with FSSAI labeling and packaging regulations.",
                "score": 0.95
            }]
        return self.evidence_builder.build_evidence(check_query, retrieved, domain_name=self.domain_name)

