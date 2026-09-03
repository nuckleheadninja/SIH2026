"""Relative coordinate normalization and 3x3 spatial grid region classifier."""
from typing import Tuple
from models.ocr_schema import LayoutModel

def compute_relative_coordinates(center_x: int, center_y: int, image_width: int, image_height: int) -> Tuple[float, float]:
    """Computes image-relative normalized coordinates (0.0 to 1.0)."""
    rel_x = round(center_x / float(max(1, image_width)), 4)
    rel_y = round(center_y / float(max(1, image_height)), 4)
    return rel_x, rel_y

def classify_region(rel_x: float, rel_y: float) -> str:
    """
    Classifies block center coordinates into one of the 9 regions of a 3x3 spatial grid:
    - top-left, top-center, top-right
    - middle-left, center, middle-right
    - bottom-left, bottom-center, bottom-right
    """
    # Vertical grid partition (Y)
    if rel_y < 0.3333:
        v_part = "top"
    elif rel_y < 0.6666:
        v_part = "middle"
    else:
        v_part = "bottom"

    # Horizontal grid partition (X)
    if rel_x < 0.3333:
        h_part = "left"
    elif rel_x < 0.6666:
        h_part = "center"
    else:
        h_part = "right"

    if v_part == "middle" and h_part == "center":
        return "center"
    else:
        return f"{v_part}-{h_part}"

def create_layout_model(center_x: int, center_y: int, image_width: int, image_height: int) -> LayoutModel:
    """Creates LayoutModel using coordinate_reference='image'."""
    rel_x, rel_y = compute_relative_coordinates(center_x, center_y, image_width, image_height)
    region = classify_region(rel_x, rel_y)

    return LayoutModel(
        coordinate_reference="image",
        relative_x=rel_x,
        relative_y=rel_y,
        region=region
    )
