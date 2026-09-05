from legal_metrology_rag.domains.legal_metrology.rag import LegalMetrologyRAG


def test_legal_metrology_rag_query():
    rag = LegalMetrologyRAG()
    query = {"check_id": "LM_MRP_001", "field": "mrp", "query_terms": ["MRP", "maximum retail price"]}
    ev = rag.query_compliance(query)

    assert ev["check_id"] == "LM_MRP_001"
    assert "document" in ev
    assert "rule" in ev
    assert "citation" in ev
