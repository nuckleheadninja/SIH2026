"""Commodity classifier to categorize packaging into commodity_type (e.g., 'food', 'drugs_cosmetics', 'general_commodity')."""

from typing import List, Dict, Any
from shared.constants import CommodityType

FOOD_KEYWORDS = ["fssai", "ingredients", "nutrition", "nutritional", "veg", "non-veg", "calories", "sugar", "protein", "carbohydrates", "fat", "serving size"]
DRUG_KEYWORDS = ["schedule h", "pharmacopoeia", "dosage", "active ingredient", "composition", "mg/ml"]


class CommodityClassifier:
    def classify(self, text_blocks: List[Dict[str, Any]]) -> str:
        """Classifies text blocks into a CommodityType string."""
        all_text = " ".join(block.get("text", "").lower() for block in text_blocks)
        
        if any(kw in all_text for kw in FOOD_KEYWORDS):
            return CommodityType.FOOD.value
        elif any(kw in all_text for kw in DRUG_KEYWORDS):
            return CommodityType.DRUGS_COSMETICS.value
        else:
            return CommodityType.GENERAL.value
