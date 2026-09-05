from compliance_engine.engine import ComplianceEngine
from shared.constants import ComplianceStatus


def test_compliance_engine_field_evaluation():
    engine = ComplianceEngine()
    extracted_field = {
        "field_name": "mrp",
        "raw_text": "MRP Rs. 120.00",
        "normalized_value": "Rs. 120.00",
        "confidence": 0.95
    }
    rag_evidence = {
        "query_id": "q1",
        "relevant_rule": "Rule 6(1)(f)",
        "evidence_text": "MRP must be declared inclusive of all taxes."
    }

    res = engine.evaluate_field_compliance(extracted_field, rag_evidence)
    assert res["status"] == ComplianceStatus.PASS.value
    assert "mrp" in res["reason"]


def test_compliance_engine_package_evaluation():
    engine = ComplianceEngine()
    fields = [
        {"field_name": "mrp", "raw_text": "MRP 100", "confidence": 0.9},
        {"field_name": "net_quantity", "raw_text": "", "confidence": 0.1}
    ]
    evidences = [
        {"query_id": "q1", "relevant_rule": "Rule 6"}
    ]

    res = engine.evaluate_package_compliance(fields, evidences)
    assert res["overall_status"] == ComplianceStatus.FAIL.value
    assert len(res["field_evaluations"]) == 2
