"""Text detector module for extracting raw OCR bounding boxes and text blocks."""

from typing import Dict, Any, List


class TextDetector:
    def __init__(self, engine_name: str = "tesseract"):
        self.engine_name = engine_name

    def detect_text(self, image_path: str) -> List[Dict[str, Any]]:
        """Detect text blocks in image. Returns structured text blocks with bboxes."""
        # Baseline detector implementation stub
        return [
            {
                "block_id": "blk_01",
                "text": "MRP Rs. 120.00",
                "confidence": 0.95,
                "bbox": [100.0, 150.0, 200.0, 30.0]
            },
            {
                "block_id": "blk_02",
                "text": "Net Qty: 500 g",
                "confidence": 0.98,
                "bbox": [100.0, 190.0, 180.0, 25.0]
            }
        ]
