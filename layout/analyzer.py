"""Reading order sorting and pairwise spatial relationship calculation engine."""
import math
from typing import List, Dict, Any
from models.ocr_schema import OCRBlockModel, SpatialRelationModel

class LayoutAnalyzer:
    def __init__(self, distance_threshold_px: float = 150.0):
        self.distance_threshold = distance_threshold_px

    def sort_reading_order(self, blocks: List[OCRBlockModel]) -> List[OCRBlockModel]:
        """
        Sorts OCR blocks in natural human reading order:
        Primary sort: Top to Bottom (center_y). Blocks within 15px Y difference are grouped in same line.
        Secondary sort: Left to Right (center_x).
        Assigns 1-indexed reading_order property.
        """
        if not blocks:
            return []

        # Custom sorting comparator using vertical line binning
        def sort_key(b: OCRBlockModel):
            line_bin = b.geometry.center_y // 20  # 20px vertical line bin
            return (line_bin, b.geometry.center_x)

        sorted_blocks = sorted(blocks, key=sort_key)

        # Update reading_order indices
        for idx, block in enumerate(sorted_blocks, start=1):
            block.reading_order = idx

        return sorted_blocks

    def compute_spatial_relationships(self, blocks: List[OCRBlockModel]) -> List[SpatialRelationModel]:
        """
        Calculates pairwise deterministic geometric relationships between OCR blocks.
        Relationships: above, below, left_of, right_of, near, aligned_with, same_region.
        """
        relations: List[SpatialRelationModel] = []
        num_blocks = len(blocks)

        for i in range(num_blocks):
            for j in range(num_blocks):
                if i == j:
                    continue

                b1 = blocks[i]
                b2 = blocks[j]

                c1_x, c1_y = b1.geometry.center_x, b1.geometry.center_y
                c2_x, c2_y = b2.geometry.center_x, b2.geometry.center_y

                dist = math.sqrt((c2_x - c1_x) ** 2 + (c2_y - c1_y) ** 2)

                # Check horizontal/vertical alignment (within 10px)
                if abs(c1_x - c2_x) <= 10 or abs(c1_y - c2_y) <= 10:
                    relations.append(SpatialRelationModel(
                        source=b1.id,
                        relation="aligned_with",
                        target=b2.id,
                        distance_px=round(dist, 2)
                    ))

                # Check same region
                if b1.layout.region == b2.layout.region:
                    relations.append(SpatialRelationModel(
                        source=b1.id,
                        relation="same_region",
                        target=b2.id,
                        distance_px=round(dist, 2)
                    ))

                # Check 'above' / 'below'
                # b1 is above b2 if b1.y2 < b2.y1 and x ranges overlap
                x_overlap = min(b1.geometry.x2, b2.geometry.x2) - max(b1.geometry.x1, b2.geometry.x1)
                if b1.geometry.y2 <= b2.geometry.y1 and x_overlap > -20:
                    relations.append(SpatialRelationModel(
                        source=b1.id,
                        relation="above",
                        target=b2.id,
                        distance_px=round(dist, 2)
                    ))

                # Check 'left_of' / 'right_of'
                y_overlap = min(b1.geometry.y2, b2.geometry.y2) - max(b1.geometry.y1, b2.geometry.y1)
                if b1.geometry.x2 <= b2.geometry.x1 and y_overlap > -20:
                    relations.append(SpatialRelationModel(
                        source=b1.id,
                        relation="left_of",
                        target=b2.id,
                        distance_px=round(dist, 2)
                    ))

                # Check proximity ('near')
                if dist <= self.distance_threshold:
                    relations.append(SpatialRelationModel(
                        source=b1.id,
                        relation="near",
                        target=b2.id,
                        distance_px=round(dist, 2)
                    ))

        return relations
