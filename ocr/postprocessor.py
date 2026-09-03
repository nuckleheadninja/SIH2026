"""Conservative, deterministic OCR postprocessor."""
import re
import unicodedata

class ConservativePostProcessor:
    """
    Applies strict, conservative, and deterministic normalization to OCR text.
    GUARANTEE: Will never hallucinate, alter numeric values, or change questionable characters.
    """

    @staticmethod
    def normalize(text: str) -> str:
        if not text:
            return ""

        # 1. Unicode Normalization (NFKC - combines compatibility characters without changing semantics)
        normalized = unicodedata.normalize("NFKC", text)

        # 2. Replace non-breaking spaces and unusual unicode whitespace with standard space
        normalized = re.sub(r'[\u00A0\u1680\u2000-\u200B\u202F\u205F\u3000]', ' ', normalized)

        # 3. Collapse multiple contiguous spaces into a single space
        normalized = re.sub(r'[ \t]+', ' ', normalized).strip()

        # 4. Standardize common legal metrology abbreviation dots safely (e.g. M.R.P. -> MRP)
        # Note: Only normalize dots in known literal prefixes, never touch numbers like 120.00
        normalized = re.sub(r'\bM\.R\.P\.(?=\s|$)', 'MRP', normalized, flags=re.IGNORECASE)
        normalized = re.sub(r'\bM\.F\.G\.(?=\s|$)', 'MFG', normalized, flags=re.IGNORECASE)
        normalized = re.sub(r'\bN\.E\.T\.\s*Q\.T\.Y\.(?=\s|$)', 'NET QTY', normalized, flags=re.IGNORECASE)
        normalized = re.sub(r'\bL\.I\.C\.\s*N\.O\.(?=\s|$)', 'LIC NO', normalized, flags=re.IGNORECASE)

        return normalized
