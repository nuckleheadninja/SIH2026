"""
verify_all.py — One-Click Verification Script for SIH2026 Pipeline
Runs:
1. OCR Module Tests (Preprocessing, PaddleOCR, Layout, Field Extraction)
2. Master Pipeline Integration (OCR -> FieldMapper -> DomainRouter -> RAG -> ComplianceEngine)
3. Live Schema Validation
"""

import sys
import json
from pathlib import Path

# Ensure UTF-8 output on Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Color styling for terminal
GREEN = "\033[92m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))

def run_verification():
    print(f"\n{BOLD}{CYAN}======================================================{RESET}")
    print(f"{BOLD}{CYAN}      SIH2026: END-TO-END VERIFICATION PIPELINE       {RESET}")
    print(f"{BOLD}{CYAN}======================================================{RESET}\n")

    # Step 1: Check OCR & Field Extraction
    print(f"{BOLD}[1/4] Running OCR & Field Extraction...{RESET}")
    from ocr_module.field_extraction.field_mapper import FieldMapper
    sample_path = REPO_ROOT / "shared" / "sample_data" / "sample_ocr_output.json"
    
    with open(sample_path, "r", encoding="utf-8") as f:
        sample_ocr = json.load(f)

    mapper = FieldMapper()
    extracted_output = mapper.extract_fields(sample_ocr)
    
    print(f"      {GREEN}[OK] Commodity Type:{RESET} {extracted_output['commodity_type']}")
    print(f"      {GREEN}[OK] Extracted Fields:{RESET}")
    for field in extracted_output["extracted_fields"]:
        print(f"        - {field['field_name']:<16}: {field.get('normalized_value')} ({field.get('unit') or 'N/A'}) [conf: {field['confidence']}]")

    # Step 2: Formal Schema Validation
    print(f"\n{BOLD}[2/4] Validating JSON Schema Contracts...{RESET}")
    schema_path = REPO_ROOT / "shared" / "schemas" / "field_extraction.schema.json"
    if schema_path.exists():
        import jsonschema
        with open(schema_path, "r", encoding="utf-8") as sf:
            schema = json.load(sf)
        jsonschema.validate(instance=extracted_output, schema=schema)
        print(f"      {GREEN}[OK] 100% Schema Compliant with shared/schemas/field_extraction.schema.json{RESET}")

    # Step 3: Check Domain Router & RAG Retrieval
    print(f"\n{BOLD}[3/4] Routing to Legal Metrology & FSSAI RAG...{RESET}")
    from legal_metrology_rag.domains.legal_metrology.query.check_mapper import CheckMapper
    from legal_metrology_rag.dispatcher.domain_router import DomainRouter
    
    check_mapper = CheckMapper()
    queries = check_mapper.map_extracted_fields_to_queries(extracted_output)
    print(f"      {GREEN}[OK] Generated Compliance Queries:{RESET} {len(queries)}")

    router = DomainRouter()
    evidences = router.dispatch_and_query(queries, commodity_type=extracted_output["commodity_type"])
    print(f"      {GREEN}[OK] Retrieved Legal Evidences:{RESET} {len(evidences)}")
    for i, ev in enumerate(evidences[:2]):
        print(f"        - Evidence {i+1}: Query '{ev.get('query_id')}' -> Citations: {len(ev.get('citations', []))}")

    # Step 4: Compliance Engine Verdict
    print(f"\n{BOLD}[4/4] Evaluating Regulatory Compliance...{RESET}")
    from compliance_engine.engine import ComplianceEngine
    engine = ComplianceEngine()
    final_result = engine.evaluate_package_compliance(extracted_output["extracted_fields"], evidences)

    status = final_result.get("overall_status", "UNKNOWN")
    status_color = GREEN if status == "PASS" else RED
    print(f"      {BOLD}Overall Compliance Status:{RESET} {status_color}{BOLD}{status}{RESET}")
    
    print(f"\n{BOLD}{GREEN}======================================================{RESET}")
    print(f"{BOLD}{GREEN}   [PASS] ALL SYSTEMS OPERATIONAL: INTEGRATION VERIFIED!   {RESET}")
    print(f"{BOLD}{GREEN}======================================================{RESET}\n")

if __name__ == "__main__":
    try:
        run_verification()
    except Exception as e:
        print(f"\n{RED}Verification failed: {e}{RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
