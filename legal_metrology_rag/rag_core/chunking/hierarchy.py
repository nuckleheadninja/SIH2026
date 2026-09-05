"""Hierarchy parser maintaining parent-child relations among legal rules, clauses, and schedules."""

from typing import List, Dict, Any


class LegalHierarchy:
    def build_hierarchy_tree(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Builds hierarchical tree mapping Document -> Chapter -> Rule -> Sub-rule -> Clause."""
        tree: Dict[str, Any] = {"chapters": {}}

        for c in chunks:
            chap = c.get("chapter") or "General"
            rule = c.get("rule") or "Rule 1"
            sub_rule = c.get("sub_rule") or "main"

            if chap not in tree["chapters"]:
                tree["chapters"][chap] = {}
            if rule not in tree["chapters"][chap]:
                tree["chapters"][chap][rule] = []

            tree["chapters"][chap][rule].append({
                "chunk_id": c["chunk_id"],
                "sub_rule": sub_rule,
                "clause": c.get("clause"),
                "page": c.get("page_start")
            })

        return tree
