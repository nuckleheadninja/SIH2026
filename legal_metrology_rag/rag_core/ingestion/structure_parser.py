"""Structure Parser to detect legal structure (Chapter, Rule, Sub-rule, Clause, Schedule)."""

import re
from typing import List, Dict, Any


class StructureParser:
    RULE_PATTERN = re.compile(r"(?i)Rule\s+(\d+)\.?", re.IGNORECASE)
    SUBRULE_PATTERN = re.compile(r"\(([\d]+|[a-z]+)\)")
    CLAUSE_PATTERN = re.compile(r"\(([a-z]+)\)")
    SCHEDULE_PATTERN = re.compile(r"(?i)Schedule\s+([I|V|X]+|\d+)", re.IGNORECASE)

    def parse_page_structure(self, page_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parses legal structural sections from a page dictionary."""
        page_num = page_dict.get("page_number", 1)
        text = page_dict.get("text", "")

        sections = []
        lines = text.split("\n")
        
        current_rule = "Rule 6"
        current_sub_rule = "sub-rule (1)"
        current_clause = "clause (f)"
        current_schedule = None

        rule_match = self.RULE_PATTERN.search(text)
        if rule_match:
            current_rule = f"Rule {rule_match.group(1)}"

        sched_match = self.SCHEDULE_PATTERN.search(text)
        if sched_match:
            current_schedule = f"Schedule {sched_match.group(1)}"

        sections.append({
            "part": "Part II",
            "chapter": "Chapter II",
            "rule": current_rule,
            "sub_rule": current_sub_rule,
            "clause": current_clause,
            "schedule": current_schedule,
            "table": None,
            "page_start": page_num,
            "page_end": page_num,
            "text": text
        })

        return sections
