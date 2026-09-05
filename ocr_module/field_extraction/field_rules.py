"""Regex patterns and rules for extracting mandatory packaging fields."""

import re
from typing import Optional, Dict

FIELD_PATTERNS: Dict[str, str] = {
    "mrp": r"(?i)(?:m\.?r\.?p\.?|max(?:imum)?\s*retail\s*price)[\s:]*(?:rs\.?|₹)?\s*([\d,]+(?:\.\d{2})?)",
    "net_quantity": r"(?i)(?:net\s*(?:qty|quantity|wt|weight)|n\.w\.)[\s:]*([\d\.]+\s*(?:g|kg|ml|l|net|units?))",
    "date_of_manufacture": r"(?i)(?:mfd|mfg|pkd|date\s*of\s*(?:mfg|manufacture|pkg|packing))[\s:]*([0-9]{2}[/\.-][0-9]{2,4}|[a-zA-Z]{3}\s*[0-9]{4})",
    "expiry_date": r"(?i)(?:exp(?:iry)?|use\s*by|best\s*before)[\s:]*([0-9]{2}[/\.-][0-9]{2,4}|[a-zA-Z]{3}\s*[0-9]{4}|\d+\s*months?)",
    "consumer_care": r"(?i)(?:consumer\s*care|customer\s*care|helpline|feedback)[\s:]*([^\n]+)"
}


class FieldRules:
    @staticmethod
    def match_field(text: str, field_name: str) -> Optional[str]:
        """Matches a field pattern against raw text string."""
        pattern = FIELD_PATTERNS.get(field_name)
        if not pattern:
            return None
        match = re.search(pattern, text)
        if match:
            return match.group(0).strip()
        return None
