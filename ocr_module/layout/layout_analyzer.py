import cv2
import numpy as np
from typing import List, Dict, Any, Optional


class LayoutAnalyzer:
    """
    Spatial Layout & Multi-Column Density Clustering Engine.
    - Prevents text interleaving between adjacent packaging columns (e.g. ingredients vs nutrition)
    - Groups text blocks into semantic layout zones (top, middle, bottom)
    - Sorts blocks into natural human reading order
    - Augments blocks with font_height_px and layout metadata
    """

    def __init__(self, image_height: int = 1000, image_width: int = 1000, column_gap_threshold: int = 40):
        self.image_height = max(1, image_height)
        self.image_width = max(1, image_width)
        self.column_gap_threshold = column_gap_threshold

    def analyze_layout(
        self,
        blocks: List[Dict[str, Any]],
        image: Optional[np.ndarray] = None
    ) -> List[Dict[str, Any]]:
        """
        Augments OCR blocks with spatial layout position and reading-order sequence.
        Guarantees presence of "layout" and "layout_position" in every block.
        """
        if not blocks:
            return []

        # If an image is provided, refine dimensions
        if image is not None:
            self.image_height, self.image_width = image.shape[:2]

        # Step 1: Assign layout_position and font_height
        for i, block in enumerate(blocks):
            bbox = block.get("bbox", [0, 0, 50, 20])
            x, y, w, h = bbox[0], bbox[1], bbox[2], bbox[3]

            block["font_height_px"] = int(h)
            if "block_id" not in block:
                block["block_id"] = f"blk_{i+1:03d}"

            # Zone partition (top 25%, middle 55%, bottom 20%)
            y_ratio = y / float(self.image_height)
            if y_ratio < 0.25:
                pos = "top"
            elif y_ratio > 0.80:
                pos = "bottom"
            else:
                pos = "middle"

            block["layout_position"] = pos
            # Backward-compatibility alias expected by tests:
            block["layout"] = pos

        # Step 2: Multi-column separation and reading order sort
        sorted_blocks = self._cluster_and_sort_reading_order(blocks)
        return sorted_blocks

    def _cluster_and_sort_reading_order(self, blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Sorts blocks into true reading order:
        First clusters into vertical columns, then sorts top-to-bottom within each column.
        """
        if len(blocks) <= 1:
            return blocks

        # Group into columns based on x-coordinate overlap
        sorted_by_x = sorted(blocks, key=lambda b: b.get("bbox", [0, 0, 0, 0])[0])
        columns = []
        current_col = [sorted_by_x[0]]

        for block in sorted_by_x[1:]:
            prev_block = current_col[-1]
            prev_x, _, prev_w, _ = prev_block.get("bbox", [0, 0, 0, 0])
            curr_x, _, _, _ = block.get("bbox", [0, 0, 0, 0])

            # If horizontal distance exceeds column gap threshold, start a new column
            if (curr_x - (prev_x + prev_w)) > self.column_gap_threshold:
                columns.append(current_col)
                current_col = [block]
            else:
                current_col.append(block)

        columns.append(current_col)

        # Sort top-to-bottom within each column
        ordered_blocks = []
        for col in columns:
            col_sorted_by_y = sorted(col, key=lambda b: b.get("bbox", [0, 0, 0, 0])[1])
            ordered_blocks.extend(col_sorted_by_y)

        return ordered_blocks

    def estimate_quality_score(self, image: np.ndarray) -> float:
        """
        Calculates sharpness score using Laplacian variance.
        Values near 1.0 indicate crisp high-contrast text; values below 0.3 indicate severe motion blur.
        """
        if image is None or image.size == 0:
            return 0.5
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        variance = cv2.Laplacian(gray, cv2.CV_64F).var()
        score = min(1.0, max(0.05, variance / 500.0))
        return round(score, 3)

    @staticmethod
    def check_rule9_font_compliance(
        net_quantity_val: float,
        unit: str,
        numeral_height_px: int,
        pdp_height_px: int
    ) -> Dict[str, Any]:
        """
        Legal Metrology (Packaged Commodities) Rules, 2011 — Rule 9(1) Table 1 verification.
        Computes statutory minimum numeral height and compliance verdict.
        """
        unit_clean = unit.lower().strip()
        mult = 1000.0 if unit_clean in ("kg", "l", "ltr", "litre", "litres") else 1.0
        base_qty = net_quantity_val * mult

        if base_qty <= 50.0:
            req_min_mm = 1.0
        elif base_qty <= 200.0:
            req_min_mm = 2.0
        elif base_qty <= 1000.0:
            req_min_mm = 4.0
        else:
            req_min_mm = 6.0

        pdp_h = max(1, pdp_height_px)
        ratio = numeral_height_px / float(pdp_h)
        est_height_mm = ratio * 150.0  # Approx 150mm PDP height reference
        is_compliant = est_height_mm >= (req_min_mm * 0.80)

        return {
            "is_compliant": bool(is_compliant),
            "status": "PASS" if is_compliant else "FAIL",
            "net_quantity_val": net_quantity_val,
            "unit": unit_clean,
            "numeral_height_px": int(numeral_height_px),
            "font_ratio_pdp_pct": round(ratio * 100, 2),
            "est_height_mm": round(est_height_mm, 1),
            "required_min_mm": req_min_mm,
            "regulation_id": "Legal Metrology (Packaged Commodities) Rules, 2011 — Rule 9(1) Table 1",
            "penalty_provision": "Section 36(1) of Legal Metrology Act, 2009 (Fine up to ₹25,000 for first offence, ₹50,000 for subsequent offence)",
            "recommendation": f"Ensure net quantity numerals are printed with minimum height of {req_min_mm} mm.",
        }
