"""Field mapper to transform OCR output text blocks into structured field extraction data."""

from typing import List, Dict, Any
from ocr_module.field_extraction.field_rules import FieldRules, FIELD_PATTERNS
from ocr_module.field_extraction.commodity_classifier import CommodityClassifier


class FieldMapper:
    def __init__(self):
        self.rules = FieldRules()
        self.classifier = CommodityClassifier()

    def extract_fields(self, ocr_output: Dict[str, Any]) -> Dict[str, Any]:
        """Maps OCR text blocks to standardized field extractions matching field_extraction.schema.json."""
        image_id = ocr_output.get("image_id", "unknown_image")
        text_blocks = ocr_output.get("text_blocks", [])

        # Classify commodity type
        commodity_type = self.classifier.classify(text_blocks)

        extracted = []
        for block in text_blocks:
            raw_text = block.get("text", "")
            bbox = block.get("bbox", [0.0, 0.0, 0.0, 0.0])
            confidence = block.get("confidence", 0.0)

            for field_name in FIELD_PATTERNS.keys():
                match = self.rules.match_field(raw_text, field_name)
                if match:
                    extracted.append({
                        "field_name": field_name,
                        "raw_text": raw_text,
                        "normalized_value": match,
                        "confidence": confidence,
                        "bbox": bbox
                    })

        return {
            "image_id": image_id,
            "commodity_type": commodity_type,
            "extracted_fields": extracted
        }
