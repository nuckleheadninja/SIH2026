"""
LegalQueryParser: Detects explicit legal references (Rules, Sub-rules, Clauses, Sections, Schedules)
in user or structured query strings.
"""

import re
from typing import Dict, Any, Optional, List


class LegalQueryParser:
    """Parses legal queries to extract explicit Rule, Section, and Schedule references."""

    ORDINAL_TO_ROMAN = {
        "first": "I", "1st": "I", "1": "I", "i": "I",
        "second": "II", "2nd": "II", "2": "II", "ii": "II",
        "third": "III", "3rd": "III", "3": "III", "iii": "III",
        "fourth": "IV", "4th": "IV", "4": "IV", "iv": "IV",
        "fifth": "V", "5th": "V", "5": "V", "v": "V",
        "sixth": "VI", "6th": "VI", "6": "VI", "vi": "VI",
        "seventh": "VII", "7th": "VII", "7": "VII", "vii": "VII"
    }

    # Regex patterns
    # Rule with clause: Rule 6(1)(e)
    RULE_CLAUSE_PATTERN = re.compile(r"\brule\s+(\d+)\s*\(\s*(\d+)\s*\)\s*\(\s*([a-z]{1,2})\s*\)", re.IGNORECASE)
    # Rule with sub-rule: Rule 6(1) or Rule 7(2)
    RULE_SUBRULE_PATTERN = re.compile(r"\brule\s+(\d+)\s*\(\s*(\d+)\s*\)", re.IGNORECASE)
    # Rule with clause shorthand: Rule 24(a)
    RULE_RULE_CLAUSE_PATTERN = re.compile(r"\brule\s+(\d+)\s*\(\s*([a-z]{1,2})\s*\)", re.IGNORECASE)
    # Simple Rule: Rule 6 or Rule 27
    RULE_SIMPLE_PATTERN = re.compile(r"\brule\s+(\d+)\b", re.IGNORECASE)
    # Clause standalone or rule clause shorthand: 6(1)(e) or 24(a)
    SHORTHAND_CLAUSE_PATTERN = re.compile(r"\b(\d+)\s*\(\s*(\d+)\s*\)\s*\(\s*([a-z]{1,2})\s*\)\b", re.IGNORECASE)
    SHORTHAND_SUBRULE_PATTERN = re.compile(r"\b(\d+)\s*\(\s*(\d+)\s*\)\b", re.IGNORECASE)
    SHORTHAND_RULE_CLAUSE_PATTERN = re.compile(r"\b(\d+)\s*\(\s*([a-z]{1,2})\s*\)\b", re.IGNORECASE)

    # Section pattern: Section 18 or Section 18(1)
    SECTION_PATTERN = re.compile(r"\bsection\s+(\d+)(?:\s*\(\s*(\d+)\s*\))?", re.IGNORECASE)

    # Schedule pattern: Schedule II, Third Schedule, Schedule 3, 2nd Schedule
    SCHEDULE_PATTERN = re.compile(
        r"\b(?:schedule\s+(vii|vi|v|iv|iii|ii|i|\d+|1st|2nd|3rd|4th|5th|6th|7th)|(first|second|third|fourth|fifth|sixth|seventh)\s+schedule)\b",
        re.IGNORECASE
    )

    @classmethod
    def parse(cls, query: str) -> Dict[str, Any]:
        """
        Parses a query string for explicit legal references.
        Returns structured dictionary containing detected metadata fields.
        """
        if not query or not isinstance(query, str):
            return cls._empty_result()

        q_lower = query.lower().strip()

        rule: Optional[str] = None
        sub_rule: Optional[str] = None
        clause: Optional[str] = None
        section: Optional[str] = None
        schedule: Optional[str] = None
        raw_matches: List[str] = []

        # 1. Parse Schedule
        sched_match = cls.SCHEDULE_PATTERN.search(q_lower)
        if sched_match:
            raw_sched = sched_match.group(1) or sched_match.group(2)
            if raw_sched:
                norm_sched = cls.ORDINAL_TO_ROMAN.get(raw_sched.lower(), raw_sched.upper())
                schedule = norm_sched
                raw_matches.append(sched_match.group(0))

        # 2. Parse Clause / Sub-rule / Rule
        # A. Rule 6(1)(e)
        rc_match = cls.RULE_CLAUSE_PATTERN.search(q_lower)
        if rc_match:
            r_num, sr_num, c_let = rc_match.groups()
            rule = r_num
            sub_rule = f"{r_num}({sr_num})"
            clause = f"{r_num}({sr_num})({c_let.lower()})"
            raw_matches.append(rc_match.group(0))
        else:
            # B. Rule 6(1) or Rule 7(2)
            rsr_match = cls.RULE_SUBRULE_PATTERN.search(q_lower)
            if rsr_match:
                r_num, sr_num = rsr_match.groups()
                rule = r_num
                sub_rule = f"{r_num}({sr_num})"
                raw_matches.append(rsr_match.group(0))
            else:
                # C. Rule 24(a) shorthand
                rrc_match = cls.RULE_RULE_CLAUSE_PATTERN.search(q_lower)
                if rrc_match:
                    r_num, c_let = rrc_match.groups()
                    rule = r_num
                    sub_rule = f"{r_num}({c_let.lower()})"
                    clause = f"{r_num}({c_let.lower()})"
                    raw_matches.append(rrc_match.group(0))
                else:
                    # D. Rule 6 or Rule 27
                    rs_match = cls.RULE_SIMPLE_PATTERN.search(q_lower)
                    if rs_match:
                        r_num = rs_match.group(1)
                        rule = r_num
                        raw_matches.append(rs_match.group(0))

        # D. Rule shorthand clause like 24(a) if rule not matched yet
        if not rule:
            src_match = cls.SHORTHAND_RULE_CLAUSE_PATTERN.search(q_lower)
            if src_match:
                r_num, c_let = src_match.groups()
                rule = r_num
                clause = f"{r_num}({c_let.lower()})"
                sub_rule = f"{r_num}({c_let.lower()})"
                raw_matches.append(src_match.group(0))

        # 3. Parse Section
        sec_match = cls.SECTION_PATTERN.search(q_lower)
        if sec_match:
            sec_num = sec_match.group(1)
            sec_sub = sec_match.group(2)
            section = f"{sec_num}({sec_sub})" if sec_sub else sec_num
            raw_matches.append(sec_match.group(0))

        explicit_provision = bool(rule or sub_rule or clause or section or schedule)

        return {
            "rule": rule,
            "sub_rule": sub_rule,
            "clause": clause,
            "section": section,
            "schedule": schedule,
            "explicit_provision": explicit_provision,
            "raw_matches": raw_matches
        }

    @staticmethod
    def _empty_result() -> Dict[str, Any]:
        return {
            "rule": None,
            "sub_rule": None,
            "clause": None,
            "section": None,
            "schedule": None,
            "explicit_provision": False,
            "raw_matches": []
        }
