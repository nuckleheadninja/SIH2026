"""Layout analyzer for extracting bounding box properties, text positioning, and font heights."""

from typing import List, Dict, Any


class LayoutAnalyzer:
    def __init__(self, image_width: float = 1000.0, image_height: float = 1000.0):
        self.image_width = image_width
        self.image_height = image_height

    def analyze_layout(self, text_blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Augments text blocks with font height and spatial region layout metadata."""
        augmented = []
        for block in text_blocks:
            bbox = block.get("bbox", [0.0, 0.0, 0.0, 0.0])
            font_height_px = bbox[3] if len(bbox) >= 4 else 0.0
            
            # Simple region spatial heuristic
            y_mid = bbox[1] + (bbox[3] / 2.0)
            if y_mid < self.image_height / 3.0:
                pos = "top"
            elif y_mid < (2.0 * self.image_height / 3.0):
                pos = "middle"
            else:
                pos = "bottom"

            block_copy = dict(block)
            block_copy["layout"] = {
                "font_height_px": font_height_px,
                "position": pos
            }
            augmented.append(block_copy)
        return augmented
