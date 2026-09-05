"""RetrievalEvaluator measuring retrieval accuracy and hit rate over structured check queries."""

import json
from typing import Dict, Any, List


class RetrievalEvaluator:
    def evaluate(self, rag_instance, test_cases_file: str) -> Dict[str, Any]:
        """Runs evaluation benchmark across test cases and computes Hit Rate."""
        with open(test_cases_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        test_cases = data.get("test_cases", [])
        if not test_cases:
            return {"total": 0, "hits": 0, "hit_rate": 0.0}

        hits = 0
        details = []

        for tc in test_cases:
            query = {
                "check_id": tc["check_id"],
                "domain": "legal_metrology",
                "commodity_type": tc["commodity_type"],
                "field": tc["field"],
                "query_terms": tc["query_terms"]
            }

            evidence = rag_instance.query_compliance(query)
            expected = tc["expected_rule"].lower()

            rule_got = (evidence.get("rule") or "").lower()
            text_got = (evidence.get("text") or "").lower()
            sched_got = (evidence.get("schedule") or "").lower()

            is_hit = expected in rule_got or expected in text_got or expected in sched_got
            if is_hit:
                hits += 1

            details.append({
                "check_id": tc["check_id"],
                "expected": tc["expected_rule"],
                "rule_retrieved": evidence.get("rule"),
                "is_hit": is_hit
            })

        hit_rate = float(hits / len(test_cases))
        return {
            "total_test_cases": len(test_cases),
            "hits": hits,
            "hit_rate": hit_rate,
            "details": details
        }
