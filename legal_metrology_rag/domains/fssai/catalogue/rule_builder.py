"""Rule builder for FSSAI domain."""

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
