"""Rule validator ensuring catalogue entries contain all mandatory schema attributes."""

from typing import Dict, Any, List


class RuleValidator:
    REQUIRED_CHECK_FIELDS = {
        "check_id",
        "domain",
        "requirement_name",
        "check_type",
        "applies_to",
        "required_observations",
        "query_terms",
        "legal_sources"
    }

    REQUIRED_SOURCE_FIELDS = {"document", "rule", "sub_rule", "clause", "schedule", "page"}

    def validate_check(self, check: Dict[str, Any]) -> bool:
        if not self.REQUIRED_CHECK_FIELDS.issubset(check.keys()):
            return False
        
        sources = check.get("legal_sources", [])
        if not isinstance(sources, list) or len(sources) == 0:
            return False

        for src in sources:
            if not self.REQUIRED_SOURCE_FIELDS.issubset(src.keys()):
                return False

        return True

    def validate_catalogue(self, checks: List[Dict[str, Any]]) -> bool:
        return all(self.validate_check(c) for c in checks)
