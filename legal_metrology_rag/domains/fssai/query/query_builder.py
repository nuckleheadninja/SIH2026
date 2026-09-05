"""QueryBuilder in FSSAI domain."""

import uuid
from typing import Dict, Any


class QueryBuilder:
    @staticmethod
    def build_query(field_name: str, field_value: str, commodity_type: str = "food") -> Dict[str, Any]:
        return {
            "query_id": f"fssai_{uuid.uuid4().hex[:8]}",
            "commodity_type": commodity_type,
            "field_name": field_name,
            "field_value": field_value,
            "domain": "fssai"
        }
