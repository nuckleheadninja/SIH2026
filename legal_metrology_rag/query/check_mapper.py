"""Check mapper to translate extracted field results into compliance check query list."""

from typing import List, Dict, Any
from legal_metrology_rag.query.query_builder import QueryBuilder


class CheckMapper:
    def __init__(self):
        self.query_builder = QueryBuilder()

    def map_extracted_fields_to_queries(self, extraction_output: Dict[str, Any], commodity_type: str = "packaged_commodity") -> List[Dict[str, Any]]:
        """Maps output of field_extraction.schema.json into compliance check queries."""
        fields = extraction_output.get("extracted_fields", [])
        queries = []
        for f in fields:
            name = f.get("field_name")
            val = f.get("normalized_value") or f.get("raw_text")
            if name and val:
                queries.append(self.query_builder.build_query(
                    field_name=name,
                    field_value=val,
                    commodity_type=commodity_type
                ))
        return queries
