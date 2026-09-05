"""Main CLI runner for Legal Metrology RAG module (SIH Problem Statement 26034)."""

import sys
import json
from legal_metrology_rag.domains.legal_metrology.rag import LegalMetrologyRAG
from legal_metrology_rag.domains.legal_metrology.query.check_mapper import CheckMapper
from legal_metrology_rag.evaluation.retrieval_eval import RetrievalEvaluator


def run_demo(sample_input: dict) -> list:
    """Runs complete end-to-end Legal Metrology RAG check from input contract payload."""
    rag = LegalMetrologyRAG()
    check_mapper = CheckMapper()

    # 1. Map input fields into structured compliance queries
    queries = check_mapper.map_input_to_queries(sample_input)

    # 2. Query compliance evidence for each check query
    evidences = []
    for q in queries:
        ev = rag.query_compliance(q)
        evidences.append(ev)

    return evidences


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--eval":
        print("Running Legal Metrology RAG Retrieval Evaluation Benchmark...")
        rag = LegalMetrologyRAG()
        evaluator = RetrievalEvaluator()
        res = evaluator.evaluate(rag, "legal_metrology_rag/evaluation/legal_metrology_test_questions.json")
        print(json.dumps(res, indent=2))
    else:
        sample_input = {
            "package_id": "PKG_00123",
            "commodity_type": "pre_packaged_commodity",
            "fields": [
                {"field": "mrp", "value": "₹120", "confidence": 0.96},
                {"field": "net_quantity", "value": "500 g", "confidence": 0.98},
                {"field": "manufacturer_details", "value": "Acme Pvt Ltd", "confidence": 0.95}
            ]
        }
        print("Executing Legal Metrology RAG Compliance Checks...")
        results = run_demo(sample_input)
        print(json.dumps(results, indent=2))
