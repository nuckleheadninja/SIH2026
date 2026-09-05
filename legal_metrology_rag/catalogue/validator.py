"""Validator to check structure and integrity of compliance rule definitions."""

from typing import Dict, Any, List


class RuleValidator:
    REQUIRED_FIELDS = {"rule_id", "rule_name", "rule_number", "mandatory", "description", "keywords"}

    def validate_rule(self, rule: Dict[str, Any]) -> bool:
        """Validates that a compliance rule dictionary contains all required keys."""
        return self.REQUIRED_FIELDS.issubset(rule.keys())

    def validate_catalogue(self, rules: List[Dict[str, Any]]) -> bool:
        """Validates all rules in a catalogue list."""
        return all(self.validate_rule(r) for r in rules)
