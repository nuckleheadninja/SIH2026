from legal_metrology_rag.domains.fssai.rag import FSSAIRAG


def test_fssai_rag_query():
    rag = FSSAIRAG()
    query = {"check_id": "FSSAI_LIC_001", "field": "fssai_license", "query_terms": ["FSSAI", "license"]}
    ev = rag.query_compliance(query)

    assert ev["check_id"] == "FSSAI_LIC_001"
    assert "document" in ev
    assert "citation" in ev
