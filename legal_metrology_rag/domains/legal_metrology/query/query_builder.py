"""QueryBuilder in legal_metrology constructing structured compliance query objects."""

from typing import Dict, Any, List


class QueryBuilder:
    @staticmethod
    def build_structured_query(
        check_id: str,
        field: str,
        commodity_type: str = "pre_packaged_commodity",
        check_type: str = "presence",
        query_terms: List[str] = None
    ) -> Dict[str, Any]:
        """Constructs structured query matching Step 7 schema."""
        terms = query_terms or [field, "pre-packaged commodity", "declaration"]
        return {
            "check_id": check_id,
            "domain": "legal_metrology",
            "commodity_type": commodity_type,
            "field": field,
            "check_type": check_type,
            "query_terms": terms
        }
