"""Geometry and text angle orientation computation."""
import math
from typing import List, Tuple
from models.ocr_schema import GeometryModel, OrientationModel, VisualModel

def compute_geometry(bbox: List[int]) -> GeometryModel:
    """
    Computes bounding box coordinates, width, height, center, area, and aspect ratio.
    bbox format: [x1, y1, x2, y2]
    """
    x1, y1, x2, y2 = [int(v) for v in bbox]
    width_px = max(1, x2 - x1)
    height_px = max(1, y2 - y1)
    center_x = x1 + (width_px // 2)
    center_y = y1 + (height_px // 2)
    area = width_px * height_px
    aspect_ratio = round(width_px / float(height_px), 4)

    return GeometryModel(
        x1=x1,
        y1=y1,
        x2=x2,
        y2=y2,
        width_px=width_px,
        height_px=height_px,
        center_x=center_x,
        center_y=center_y,
        center=[center_x, center_y],
        area=area,
        aspect_ratio=aspect_ratio
    )

def compute_orientation(polygon: List[List[int]]) -> OrientationModel:
    """
    Calculates text rotation angle in degrees using top edge of polygon [(x1,y1), (x2,y2)].
    Categorizes into horizontal, rotated, vertical, or unknown.
    """
    if not polygon or len(polygon) < 2:
        return OrientationModel(angle_degrees=0.0, category="horizontal")

    p1, p2 = polygon[0], polygon[1]
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]

    angle_rad = math.atan2(dy, dx)
    angle_deg = math.degrees(angle_rad)

    # Normalize angle to range (-180, 180]
    angle_deg = round(angle_deg, 2)
    abs_angle = abs(angle_deg)

    if abs_angle < 10.0 or abs_angle > 170.0:
        category = "horizontal"
    elif 80.0 <= abs_angle <= 100.0:
        category = "vertical"
    else:
        category = "rotated"

    return OrientationModel(
        angle_degrees=angle_deg,
        category=category
    )

def compute_visual_metrics(height_px: int) -> VisualModel:
    """
    Computes visual font height approximation in pixels.
    Leaves font_height_mm as None and scale_calibrated as False.
    """
    return VisualModel(
        font_height_px=height_px,
        font_height_mm=None,
        scale_calibrated=False
    )
