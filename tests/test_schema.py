"""Unit tests for Pydantic schema validation and evidence preservation."""
from models.ocr_schema import (
    GeometryModel,
    LayoutModel,
    OrientationModel,
    VisualModel,
    OCRBlockModel
)

def test_ocr_block_schema():
    geom = GeometryModel(
        x1=100, y1=100, x2=300, y2=150,
        width_px=200, height_px=50,
        center_x=200, center_y=125, center=[200, 125],
        area=10000, aspect_ratio=4.0
    )
    layout = LayoutModel(
        coordinate_reference="image",
        relative_x=0.1667,
        relative_y=0.1562,
        region="top-left"
    )
    orient = OrientationModel(angle_degrees=0.0, category="horizontal")
    visual = VisualModel(font_height_px=50, font_height_mm=None, scale_calibrated=False)

    block = OCRBlockModel(
        id="ocr_001",
        raw_text="M.R.P. ₹ 120.00",
        normalized_text="MRP ₹ 120.00",
        confidence=0.96,
        confidence_level="high",
        polygon=[[100, 100], [300, 100], [300, 150], [100, 150]],
        bbox=[100, 100, 300, 150],
        geometry=geom,
        layout=layout,
        orientation=orient,
        visual=visual,
        reading_order=1
    )

    block_json = block.model_dump()
    assert block_json["raw_text"] == "M.R.P. ₹ 120.00"
    assert block_json["normalized_text"] == "MRP ₹ 120.00"
    assert block_json["layout"]["coordinate_reference"] == "image"
    assert block_json["layout"]["region"] == "top-left"
    assert block_json["visual"]["font_height_mm"] is None
    assert block_json["visual"]["scale_calibrated"] is False
