import re
from typing import List, Dict, Any
from shared.constants import CommodityType


class CommodityClassifier:
    """
    Classifies the commodity category of packaging based on extracted textual cues.
    Categories:
    - FOOD ('food')
    - GENERAL ('general_commodity')
    - DRUGS_COSMETICS ('drugs_cosmetics')
    """

    FOOD_KEYWORDS = [
        r"\bfssai\b", r"\bnutrition", r"\bingredients?\b", r"\bedible\b",
        r"\bcalories?\b", r"\bprotein\b", r"\bcarbohydrate\b", r"\badded sugars?\b",
        r"\bflavour\b", r"\bmasala\b", r"\bspices?\b", r"\bveg(an)?\b", r"\bnon-veg\b",
        r"\bserve\b", r"\benergy\b", r"\bwheat\b", r"\boil\b", r"\bfat\b"
    ]

    DRUG_COSMETIC_KEYWORDS = [
        r"\bmfg\s*lic\b", r"\bcosmetic\b", r"\bshampoo\b", r"\blotion\b",
        r"\bfor external use only\b", r"\bparaben\b", r"\bpharmaceutical\b",
        r"\bdose\b", r"\btablet\b", r"\bcapsule\b", r"\bophthalmic\b", r"\bointment\b"
    ]

    def classify(self, blocks: List[Dict[str, Any]]) -> str:
        """
        Determines commodity type from text blocks.
        Returns 'food', 'drugs_cosmetics', or 'general_commodity'.
        """
        if not blocks:
            return CommodityType.GENERAL.value

        combined_text = " ".join(b.get("text", "") for b in blocks).lower()

        # Score food keywords
        food_score = sum(1 for pat in self.FOOD_KEYWORDS if re.search(pat, combined_text, re.IGNORECASE))
        
        # Score drug/cosmetics keywords
        drug_score = sum(1 for pat in self.DRUG_COSMETIC_KEYWORDS if re.search(pat, combined_text, re.IGNORECASE))

        if food_score >= 1 and food_score >= drug_score:
            return CommodityType.FOOD.value
        elif drug_score >= 1:
            return CommodityType.DRUGS_COSMETICS.value
        else:
            return CommodityType.GENERAL.value
