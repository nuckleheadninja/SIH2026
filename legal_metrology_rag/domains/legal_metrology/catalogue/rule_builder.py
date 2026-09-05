"""Rule Builder for loading and querying compliance checks from catalogue."""

import json
from typing import Dict, Any, List, Optional


class RuleBuilder:
    def __init__(self, catalogue_path: Optional[str] = None):
        self.checks: List[Dict[str, Any]] = []
        if catalogue_path:
            self.load_catalogue(catalogue_path)

    def load_catalogue(self, path: str):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.checks = data.get("checks", [])

    def get_check_by_id(self, check_id: str) -> Optional[Dict[str, Any]]:
        for c in self.checks:
            if c.get("check_id") == check_id:
                return c
        return None

    def get_checks_for_field(self, field_name: str) -> List[Dict[str, Any]]:
        field_lower = field_name.lower()
        return [
            c for c in self.checks
            if field_lower in c.get("check_id", "").lower()
            or field_lower in c.get("requirement_name", "").lower()
            or any(field_lower in term.lower() for term in c.get("query_terms", []))
        ]
