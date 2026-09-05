"""CheckMapper in FSSAI domain."""

from typing import List, Dict, Any
from legal_metrology_rag.domains.fssai.query.query_builder import QueryBuilder


class CheckMapper:
    def __init__(self):
        self.qb = QueryBuilder()

    def map_input_to_queries(self, input_payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        fields = input_payload.get("fields") or input_payload.get("extracted_fields", [])
        commodity = input_payload.get("commodity_type", "food")

        queries = []
        for f in fields:
            field_name = f.get("field") or f.get("field_name")
            if field_name:
                queries.append(self.qb.build_query(field_name, "val", commodity_type=commodity))
        return queries

    def map_extracted_fields_to_queries(self, extraction_output: Dict[str, Any]) -> List[Dict[str, Any]]:
        return self.map_input_to_queries(extraction_output)
