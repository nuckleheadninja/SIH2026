"""Query builder for generating standardized compliance check queries."""

import uuid
from typing import Dict, Any


class QueryBuilder:
    @staticmethod
    def build_query(field_name: str, field_value: str, commodity_type: str = "general_commodity", declared_font_height_mm: float = None) -> Dict[str, Any]:
        """Constructs compliance query dict matching compliance_check.schema.json."""
        query = {
            "query_id": f"chk_{uuid.uuid4().hex[:8]}",
            "commodity_type": commodity_type,
            "field_name": field_name,
            "field_value": field_value
        }
        if declared_font_height_mm is not None:
            query["declared_font_height_mm"] = declared_font_height_mm
        return query
