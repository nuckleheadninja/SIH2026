"""Hierarchy parser for maintaining parent-child relations among legal rules and schedules."""

from typing import Dict, Any, List


class LegalHierarchy:
    def __init__(self):
        self.hierarchy_tree = {}

    def build_hierarchy(self, sections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Builds hierarchical mapping of Act -> Chapter -> Rule -> Schedule."""
        tree = {"Act": "Legal Metrology Act, 2009", "Chapters": {}}
        for sec in sections:
            chap = sec.get("chapter", "General")
            rule = sec.get("rule_number", "Unclassified")
            if chap not in tree["Chapters"]:
                tree["Chapters"][chap] = []
            tree["Chapters"][chap].append(rule)
        self.hierarchy_tree = tree
        return tree
