"""End-to-end pipeline integration test: OCR -> Dispatcher -> RAG(s) -> Engine."""

import json
from pathlib import Path
from ocr_module.field_extraction.field_mapper import FieldMapper
from legal_metrology_rag.dispatcher.domain_router import DomainRouter
from legal_metrology_rag.domains.legal_metrology.query.check_mapper import CheckMapper
from compliance_engine.engine import ComplianceEngine
from shared.constants import ComplianceStatus


def test_end_to_end_multi_domain_pipeline():
    # 1. Load mock OCR output from shared sample
    sample_ocr_path = Path(__file__).parent.parent / "shared" / "sample_data" / "sample_ocr_output.json"
    with open(sample_ocr_path, "r", encoding="utf-8") as f:
        ocr_data = json.load(f)

    # 2. Extract Fields & Classify Commodity via ocr_module
    field_mapper = FieldMapper()
    extracted_output = field_mapper.extract_fields(ocr_data)
    assert "commodity_type" in extracted_output
    commodity_type = extracted_output["commodity_type"]

    # 3. Map Extracted Fields to Compliance Queries
    check_mapper = CheckMapper()
    queries = check_mapper.map_extracted_fields_to_queries(extracted_output)
    assert len(queries) > 0

    # 4. Dispatch Queries across domain RAGs using DomainRouter
    router = DomainRouter()
    evidences = router.dispatch_and_query(queries, commodity_type=commodity_type)
    assert len(evidences) >= len(queries)

    # 5. Evaluate Compliance via Compliance Engine
    engine = ComplianceEngine()
    final_result = engine.evaluate_package_compliance(extracted_output["extracted_fields"], evidences)

    assert "overall_status" in final_result
    assert final_result["overall_status"] in [ComplianceStatus.PASS.value, ComplianceStatus.FAIL.value, ComplianceStatus.UNCERTAIN.value]
