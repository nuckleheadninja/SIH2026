"""CheckMapper mapping input payload / extracted fields into structured compliance queries."""

from typing import List, Dict, Any
from legal_metrology_rag.domains.legal_metrology.catalogue.rule_builder import RuleBuilder
from legal_metrology_rag.domains.legal_metrology.query.query_builder import QueryBuilder


class CheckMapper:
    def __init__(self, rule_builder: RuleBuilder = None):
        self.rule_builder = rule_builder or RuleBuilder()
        self.qb = QueryBuilder()

    def map_input_to_queries(self, input_payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        fields = input_payload.get("fields") or input_payload.get("extracted_fields", [])
        commodity = input_payload.get("commodity_type", "pre_packaged_commodity")

        queries = []
        for f in fields:
            field_name = f.get("field") or f.get("field_name")
            if not field_name:
                continue

            matching_checks = self.rule_builder.get_checks_for_field(field_name)
            if matching_checks:
                for check in matching_checks:
                    queries.append(self.qb.build_structured_query(
                        check_id=check["check_id"],
                        field=field_name,
                        commodity_type=commodity,
                        check_type=check.get("check_type", "presence"),
                        query_terms=check.get("query_terms", [field_name])
                    ))
            else:
                queries.append(self.qb.build_structured_query(
                    check_id=f"LM_{field_name.upper()}_001",
                    field=field_name,
                    commodity_type=commodity,
                    check_type="presence",
                    query_terms=[field_name, "declaration", "pre-packaged commodity"]
                ))

        return queries

    def map_extracted_fields_to_queries(self, extraction_output: Dict[str, Any]) -> List[Dict[str, Any]]:
        return self.map_input_to_queries(extraction_output)
