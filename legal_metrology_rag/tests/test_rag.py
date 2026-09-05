import json
from pathlib import Path
from legal_metrology_rag.catalogue.validator import RuleValidator
from legal_metrology_rag.retrieval.hybrid_retriever import HybridRetriever
from legal_metrology_rag.query.query_builder import QueryBuilder
from legal_metrology_rag.evidence.evidence_builder import EvidenceBuilder


def test_compliance_rules_catalogue():
    cat_path = Path(__file__).parent.parent / "catalogue" / "compliance_rules.json"
    with open(cat_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    validator = RuleValidator()
    assert validator.validate_catalogue(data["rules"]) is True


def test_query_builder():
    qb = QueryBuilder()
    q = qb.build_query("mrp", "Rs 120", declared_font_height_mm=3.0)
    assert q["field_name"] == "mrp"
    assert q["declared_font_height_mm"] == 3.0


def test_hybrid_retriever_and_evidence():
    retriever = HybridRetriever()
    docs = retriever.retrieve("mrp price declaration")
    assert len(docs) > 0

    builder = EvidenceBuilder()
    query = {"query_id": "q_test", "field_name": "mrp"}
    evidence = builder.build_evidence(query, docs)
    assert evidence["query_id"] == "q_test"
    assert "citation" in evidence
    assert "rule_number" in evidence["citation"]
