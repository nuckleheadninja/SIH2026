"""Rule validator in FSSAI domain."""

from typing import Dict, Any, List


class RuleValidator:
    REQUIRED_FIELDS = {"rule_id", "rule_name", "rule_number", "mandatory", "description", "keywords"}

    def validate_rule(self, rule: Dict[str, Any]) -> bool:
        return self.REQUIRED_FIELDS.issubset(rule.keys())

    def validate_catalogue(self, rules: List[Dict[str, Any]]) -> bool:
        return all(self.validate_rule(r) for r in rules)
