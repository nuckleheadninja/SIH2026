import json
from pathlib import Path
from legal_metrology_rag.domains.legal_metrology.catalogue.validator import RuleValidator
from legal_metrology_rag.domains.legal_metrology.catalogue.rule_builder import RuleBuilder
from legal_metrology_rag.domains.legal_metrology.query.query_builder import QueryBuilder
from legal_metrology_rag.domains.legal_metrology.query.check_mapper import CheckMapper
from legal_metrology_rag.domains.legal_metrology.rag import LegalMetrologyRAG
from legal_metrology_rag.rag_core.ingestion.pdf_loader import PDFLoader
from legal_metrology_rag.rag_core.ingestion.text_extractor import TextExtractor
from legal_metrology_rag.rag_core.ingestion.structure_parser import StructureParser
from legal_metrology_rag.rag_core.chunking.legal_chunker import LegalChunker
from legal_metrology_rag.rag_core.database.vector_store import VectorStore
from legal_metrology_rag.rag_core.database.metadata_store import MetadataStore
from legal_metrology_rag.rag_core.retrieval.hybrid_retriever import HybridRetriever
from legal_metrology_rag.rag_core.retrieval.reranker import LegalReranker
from legal_metrology_rag.evaluation.retrieval_eval import RetrievalEvaluator
from legal_metrology_rag.evaluation.citation_eval import CitationEvaluator


def test_compliance_rule_catalogue_validation():
    cat_path = Path(__file__).parent.parent / "domains" / "legal_metrology" / "catalogue" / "compliance_rules.json"
    with open(cat_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    validator = RuleValidator()
    assert validator.validate_catalogue(data["checks"]) is True


def test_ingestion_and_page_preservation():
    loader = PDFLoader()
    doc_info = loader.load_pdf("sample.pdf")
    extractor = TextExtractor()
    pages = extractor.extract_pages(doc_info)
    assert len(pages) > 0
    assert "page_number" in pages[0]


def test_structure_parser_and_chunker():
    parser = StructureParser()
    page = {"page_number": 12, "text": "Rule 6. Declarations to be made on every package..."}
    sections = parser.parse_page_structure(page)

    chunker = LegalChunker()
    doc_meta = {"document_id": "doc_test", "domain": "legal_metrology"}
    chunks = chunker.chunk_structured_sections(sections, doc_meta)

    assert len(chunks) > 0
    c = chunks[0]
    assert "chunk_id" in c
    assert "rule" in c
    assert "effective_from" in c
    assert "status" in c


def test_metadata_store_superseded_filtering():
    store = MetadataStore()
    current_chunk = {"chunk_id": "c1", "status": "current", "effective_from": "2011-01-01"}
    superseded_chunk = {"chunk_id": "c2", "status": "superseded", "effective_from": "1990-01-01"}

    filtered = store.filter_current_provisions([current_chunk, superseded_chunk])
    assert len(filtered) == 1
    assert filtered[0]["chunk_id"] == "c1"


def test_abstract_vector_store_operations():
    vs = VectorStore(collection_name="test_col")
    doc = {"chunk_id": "c100", "rule": "Rule 6", "text": "MRP declaration requirement"}
    vs.add_documents([doc])
    
    results = vs.search("MRP", top_k=1)
    assert len(results) == 1
    assert results[0]["chunk_id"] == "c100"

    deleted = vs.delete("c100")
    assert deleted is True


def test_hybrid_retrieval_and_reranking():
    vs = VectorStore(collection_name="test_col")
    vs.add_documents([
        {"chunk_id": "c1", "rule": "Rule 6", "text": "MRP maximum retail price inclusive of all taxes"},
        {"chunk_id": "c2", "rule": "Rule 7", "text": "Height of numerals Schedule II font size"}
    ])

    retriever = HybridRetriever(vector_store=vs)
    candidates = retriever.retrieve(query_terms=["MRP", "maximum retail price"], top_k=20)
    assert len(candidates) > 0

    reranker = LegalReranker(target_top_k=5)
    reranked = reranker.rerank(query_terms=["MRP"], candidate_chunks=candidates)
    assert len(reranked) <= 5
    assert "retrieval_score" in reranked[0]


test_legal_metrology_rag_end_to_end_query = None  # Placeholder declaration


def test_legal_metrology_rag_full_pipeline():
    rag = LegalMetrologyRAG()
    query = {
        "check_id": "LM_MRP_001",
        "domain": "legal_metrology",
        "commodity_type": "pre_packaged_commodity",
        "field": "mrp",
        "query_terms": ["MRP", "maximum retail price", "inclusive of all taxes"]
    }

    evidence = rag.query_compliance(query)
    assert evidence["check_id"] == "LM_MRP_001"
    assert "citation" in evidence
    assert evidence["citation"]["document"] is not None
    assert evidence["citation"]["rule"] is not None


def test_evaluation_suite():
    rag = LegalMetrologyRAG()
    evaluator = RetrievalEvaluator()
    eval_file = Path(__file__).parent.parent / "evaluation" / "legal_metrology_test_questions.json"
    res = evaluator.evaluate(rag, str(eval_file))

    assert res["total_test_cases"] > 0
    assert res["hit_rate"] >= 0.8

    cit_eval = CitationEvaluator()
    sample_evidence = rag.query_compliance({"check_id": "LM_MRP_001", "field": "mrp", "query_terms": ["MRP"]})
    cit_res = cit_eval.evaluate_citations([sample_evidence])
    assert cit_res["accuracy"] == 1.0
