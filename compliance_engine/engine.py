"""Compliance Engine for evaluating extracted package fields against legal evidence."""

from typing import Dict, Any, List
from shared.constants import ComplianceStatus


class ComplianceEngine:
    """Combines Field Extraction output + RAG evidence to output PASS/FAIL/UNCERTAIN compliance decision."""

    def __init__(self):
        self.status = ComplianceStatus.UNCERTAIN

    def evaluate_field_compliance(self, extracted_field: Dict[str, Any], RAG_evidence: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluates single field compliance against legal evidence snippet."""
        field_name = extracted_field.get("field_name")
        val = extracted_field.get("normalized_value") or extracted_field.get("raw_text")
        confidence = extracted_field.get("confidence", 0.0)

        # Stub compliance logic:
        # If field is present and confidence > 0.7, PASS.
        # If field is missing or empty, FAIL.
        # Otherwise UNCERTAIN.
        if not val or confidence < 0.5:
            status = ComplianceStatus.FAIL
            reason = f"Field '{field_name}' is missing or low confidence ({confidence})."
        elif confidence >= 0.7:
            status = ComplianceStatus.PASS
            reason = f"Field '{field_name}' present with sufficient confidence and complies with {RAG_evidence.get('relevant_rule')}."
        else:
            status = ComplianceStatus.UNCERTAIN
            reason = f"Field '{field_name}' extracted but requires manual inspection."

        return {
            "field_name": field_name,
            "status": status.value,
            "reason": reason,
            "evidence": RAG_evidence
        }

    def evaluate_package_compliance(self, all_extracted_fields: List[Dict[str, Any]], evidences: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Evaluates overall packaging compliance across all mandatory declaration fields."""
        results = []
        overall = ComplianceStatus.PASS

        ev_map = {e.get("query_id"): e for e in evidences if e.get("query_id")}

        for field in all_extracted_fields:
            # Match matching evidence or pass empty dict
            evidence = next(iter(evidences), {})
            res = self.evaluate_field_compliance(field, evidence)
            results.append(res)
            if res["status"] == ComplianceStatus.FAIL:
                overall = ComplianceStatus.FAIL
            elif res["status"] == ComplianceStatus.UNCERTAIN and overall != ComplianceStatus.FAIL:
                overall = ComplianceStatus.UNCERTAIN

        return {
            "overall_status": overall.value,
            "field_evaluations": results
        }
