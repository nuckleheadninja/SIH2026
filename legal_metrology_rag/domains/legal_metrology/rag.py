"""LegalMetrologyRAG domain implementation subclassing BaseComplianceRAG."""

from typing import Dict, Any, List, Optional
from legal_metrology_rag.rag_core.base_rag import BaseComplianceRAG
from legal_metrology_rag.rag_core.ingestion.pdf_loader import PDFLoader
from legal_metrology_rag.rag_core.ingestion.text_extractor import TextExtractor
from legal_metrology_rag.rag_core.ingestion.structure_parser import StructureParser
from legal_metrology_rag.rag_core.ingestion.metadata_extractor import MetadataExtractor
from legal_metrology_rag.rag_core.chunking.legal_chunker import LegalChunker
from legal_metrology_rag.rag_core.database.vector_store import VectorStore
from legal_metrology_rag.rag_core.database.metadata_store import MetadataStore
from legal_metrology_rag.rag_core.retrieval.hybrid_retriever import HybridRetriever
from legal_metrology_rag.rag_core.retrieval.reranker import LegalReranker
from legal_metrology_rag.rag_core.evidence.evidence_builder import EvidenceBuilder


class LegalMetrologyRAG(BaseComplianceRAG):
    """Legal Metrology RAG module for pre-packaged commodities in India."""

    def __init__(self, config_path: Optional[str] = None):
        super().__init__(domain_name="legal_metrology", config_path=config_path)

        self.pdf_loader = PDFLoader()
        self.text_extractor = TextExtractor()
        self.structure_parser = StructureParser()
        self.metadata_extractor = MetadataExtractor()
        self.chunker = LegalChunker()

        self.vector_store = VectorStore(collection_name="legal_metrology")
        self.metadata_store = MetadataStore()

        self.hybrid_retriever = HybridRetriever(vector_store=self.vector_store)
        self.reranker = LegalReranker(target_top_k=6)
        self.evidence_builder = EvidenceBuilder(default_doc_name="Legal Metrology (Packaged Commodities) Rules, 2011")

        self._seed_default_index()

    def _seed_default_index(self):
        doc_meta = self.metadata_extractor.extract_document_metadata("Legal_Metrology_Packaged_Commodities_Rules_2011.pdf")

        # Explicit pre-packaged statutory rule sections for accurate retrieval
        sections = [
            {
                "part": "Part II",
                "chapter": "Chapter II",
                "rule": "Rule 6",
                "sub_rule": "sub-rule (1)",
                "clause": "clause (f)",
                "schedule": None,
                "page_start": 12,
                "page_end": 12,
                "text": "Rule 6(1)(f) The maximum retail price at which the package may be sold to the ultimate consumer inclusive of all taxes."
            },
            {
                "part": "Part II",
                "chapter": "Chapter II",
                "rule": "Rule 6",
                "sub_rule": "sub-rule (1)",
                "clause": "clause (d)",
                "schedule": None,
                "page_start": 10,
                "page_end": 10,
                "text": "Rule 6(1)(d) Net quantity, in terms of standard unit of weight or measure or number, contained in the package."
            },
            {
                "part": "Part II",
                "chapter": "Chapter II",
                "rule": "Rule 6",
                "sub_rule": "sub-rule (1)",
                "clause": "clause (a)",
                "schedule": None,
                "page_start": 8,
                "page_end": 8,
                "text": "Rule 6(1)(a) The name and address of the manufacturer or where the manufacturer is not the packer, the name and address of the manufacturer and packer."
            },
            {
                "part": "Part II",
                "chapter": "Chapter II",
                "rule": "Rule 6",
                "sub_rule": "sub-rule (1)",
                "clause": "clause (g)",
                "schedule": null if "null" in locals() else None,
                "page_start": 13,
                "page_end": 13,
                "text": "Rule 6(1)(g) Name, address, telephone number, e-mail address of the person who can be contacted in case of consumer complaints."
            },
            {
                "part": "Part II",
                "chapter": "Chapter II",
                "rule": "Rule 7",
                "sub_rule": "sub-rule (1)",
                "clause": None,
                "schedule": "Schedule II",
                "page_start": 24,
                "page_end": 24,
                "text": "Rule 7 & Schedule II: Height of numerals and letters in declarations shall comply with prescribed mm size requirements per area of principal display panel."
            }
        ]

        chunks = self.chunker.chunk_structured_sections(sections, doc_meta)
        self.vector_store.add_documents(chunks)
        for c in chunks:
            self.metadata_store.insert(c["chunk_id"], c)

    def load_documents(self, raw_dir: str):
        pass

    def query_compliance(self, check_query: Dict[str, Any]) -> Dict[str, Any]:
        query_terms = check_query.get("query_terms") or [check_query.get("field", "mrp")]
        field = check_query.get("field", "")
        raw_query = f"{field} {' '.join(query_terms)}"

        candidates = self.hybrid_retriever.retrieve(query_terms=query_terms, raw_query_string=raw_query, top_k=20)
        active_candidates = self.metadata_store.filter_current_provisions(candidates)
        top_reranked = self.reranker.rerank(query_terms=query_terms, candidate_chunks=active_candidates)
        evidence_items = self.evidence_builder.build_evidence_list(check_query, top_reranked)

        return evidence_items[0] if evidence_items else {
            "check_id": check_query.get("check_id") or check_query.get("query_id") or "LM_UNK",
            "chunk_id": "chk_none",
            "document": "Legal Metrology (Packaged Commodities) Rules, 2011",
            "rule": "Rule 6",
            "sub_rule": None,
            "clause": None,
            "schedule": None,
            "page": None,
            "text": "No evidence retrieved",
            "retrieval_score": 0.0,
            "citation": {
                "document": "Legal Metrology (Packaged Commodities) Rules, 2011",
                "rule": "Rule 6",
                "sub_rule": None,
                "clause": None,
                "schedule": None,
                "page": None
            }
        }
