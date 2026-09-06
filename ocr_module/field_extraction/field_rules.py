import re
from typing import Optional, Dict, Any, Tuple


class FieldRules:
    """
    Standardized regulatory compliance regex patterns and normalization rules
    governed by Legal Metrology (Packaged Commodities) Rules and FSSAI Packaging Regulations.
    """

    # MRP Rules (Currency, amount, taxes)
    MRP_PATTERNS = [
        re.compile(r"(?:M\.?R\.?P\.?|MAX(?:IMUM)?\s*RETAIL\s*PRICE)[^\d₹Rs]*[₹Rs\.]*\s*([0-9]+(?:[\.,][0-9]{1,2})?)", re.IGNORECASE),
        re.compile(r"(?:₹|Rs\.?)\s*([0-9]+(?:[\.,][0-9]{1,2})?)", re.IGNORECASE)
    ]

    # Net Quantity Rules (value + metric unit)
    NET_QTY_PATTERNS = [
        re.compile(r"(?:NET\s*(?:QTY|QUANTITY|WT|WEIGHT|CONTENT)?)[^\d]*([0-9]+(?:\.[0-9]+)?)\s*(kg|g|gm|gms|mg|l|ltr|litres?|ml|piece|pieces|pcs|count|u|units?)\b", re.IGNORECASE),
        re.compile(r"\b([0-9]+(?:\.[0-9]+)?)\s*(kg|g|gm|gms|l|ltr|ml)\b", re.IGNORECASE)
    ]

    # Dates: Manufacturing / Packaging / Expiry / Best Before
    MFG_PATTERNS = [
        re.compile(r"(?:MFD|MFG|PACKED|PKD|DATE\s*OF\s*(?:MFG|PACKING))[^\d]*([0-9]{1,2}[\/\-\.][0-9]{1,2}[\/\-\.][0-9]{2,4}|[A-Za-z]{3,9}\s*['\.]?\s*[0-9]{2,4}|[0-9]{1,2}\s*[A-Za-z]{3,9}\s*[0-9]{2,4})", re.IGNORECASE)
    ]

    EXPIRY_PATTERNS = [
        re.compile(r"(?:EXP(?:IRY)?|USE\s*BY|BEST\s*BEFORE)[^\d]*([0-9]{1,2}[\/\-\.][0-9]{1,2}[\/\-\.][0-9]{2,4}|[A-Za-z]{3,9}\s*['\.]?\s*[0-9]{2,4}|[0-9]{1,2}\s*[A-Za-z]{3,9}\s*[0-9]{2,4}|[0-9]+\s*MONTHS?)", re.IGNORECASE)
    ]

    # FSSAI 14-Digit License
    FSSAI_PATTERNS = [
        re.compile(r"(?:FSSAI|LIC(?:ENCE)?\s*(?:NO\.?)?)[^\d]*([12]\d{13})", re.IGNORECASE),
        re.compile(r"\b([12]\d{13})\b")
    ]

    # Batch / Lot Number
    BATCH_PATTERNS = [
        re.compile(r"(?:BATCH|LOT|B\.?\s*NO\.?)[^\w]*([A-Z0-9\-\/]+)", re.IGNORECASE)
    ]

    # Consumer Care / Feedback
    CONSUMER_CARE_PATTERNS = [
        re.compile(r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)", re.IGNORECASE),
        re.compile(r"(?:TOLL\s*FREE|HELPLINE|CALL|CARE)[^\d]*(\d{3,5}[-\s]?\d{3,4}[-\s]?\d{3,4}|\d{10,11})", re.IGNORECASE)
    ]

    # INS Additive codes: e.g. INS 330, INS 170(i), (330)
    INS_PATTERN = re.compile(r"(?:INS\s*|E\s*|\()([0-9]{3,4}[a-z]?(?:\([i-v]+\))?)\)?", re.IGNORECASE)

    # Common allergens in Indian FMCG
    KNOWN_ALLERGENS = [
        "wheat", "gluten", "milk", "dairy", "soy", "soya", "peanut", "peanuts",
        "tree nuts", "almond", "cashew", "mustard", "sulphite", "sulphites", "sesame", "egg", "fish"
    ]

    @classmethod
    def parse_mrp(cls, text: str) -> Optional[Dict[str, Any]]:
        for pat in cls.MRP_PATTERNS:
            m = pat.search(text)
            if m:
                raw_val = m.group(1).replace(",", ".")
                try:
                    val = float(raw_val)
                    return {"raw_text": m.group(0), "normalized_value": val, "unit": "INR"}
                except ValueError:
                    pass
        return None

    @classmethod
    def parse_net_qty(cls, text: str) -> Optional[Dict[str, Any]]:
        for pat in cls.NET_QTY_PATTERNS:
            m = pat.search(text)
            if m:
                val_str = m.group(1)
                unit_str = m.group(2).lower()
                # Standardize units: gm/gms -> g, ltr/litres -> l
                if unit_str in ["gm", "gms"]:
                    unit_str = "g"
                elif unit_str in ["ltr", "litre", "litres"]:
                    unit_str = "l"
                try:
                    val = float(val_str)
                    return {"raw_text": m.group(0), "normalized_value": val, "unit": unit_str}
                except ValueError:
                    pass
        return None

    @classmethod
    def parse_fssai(cls, text: str) -> Optional[Dict[str, Any]]:
        for pat in cls.FSSAI_PATTERNS:
            m = pat.search(text)
            if m:
                lic = m.group(1)
                if len(lic) == 14 and lic.isdigit():
                    return {"raw_text": m.group(0), "normalized_value": lic, "unit": None}
        return None

    @classmethod
    def parse_batch(cls, text: str) -> Optional[Dict[str, Any]]:
        for pat in cls.BATCH_PATTERNS:
            m = pat.search(text)
            if m:
                return {"raw_text": m.group(0), "normalized_value": m.group(1).strip(), "unit": None}
        return None

    @classmethod
    def parse_dates(cls, text: str) -> Dict[str, Optional[Dict[str, Any]]]:
        result = {"mfg_date": None, "expiry_date": None}
        for pat in cls.MFG_PATTERNS:
            m = pat.search(text)
            if m:
                result["mfg_date"] = {"raw_text": m.group(0), "normalized_value": m.group(1).strip(), "unit": None}
                break

        for pat in cls.EXPIRY_PATTERNS:
            m = pat.search(text)
            if m:
                result["expiry_date"] = {"raw_text": m.group(0), "normalized_value": m.group(1).strip(), "unit": None}
                break

        return result
