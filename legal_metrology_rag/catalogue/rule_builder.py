"""Rule Builder for constructing legal compliance catalogue rules programmatically."""

import json
from typing import Dict, Any, List


class RuleBuilder:
    def __init__(self, catalogue_path: str = None):
        self.rules: List[Dict[str, Any]] = []
        if catalogue_path:
            self.load_catalogue(catalogue_path)

    def load_catalogue(self, path: str):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.rules = data.get("rules", [])

    def add_rule(self, rule_id: str, rule_name: str, rule_number: str, mandatory: bool, description: str, keywords: List[str]):
        self.rules.append({
            "rule_id": rule_id,
            "rule_name": rule_name,
            "rule_number": rule_number,
            "mandatory": mandatory,
            "description": description,
            "keywords": keywords
        })

    def get_rules_for_field(self, field_name: str) -> List[Dict[str, Any]]:
        matching = []
        for r in self.rules:
            if field_name.lower() in r["rule_id"].lower() or any(field_name.lower() in k.lower() for k in r["keywords"]):
                matching.append(r)
        return matching
