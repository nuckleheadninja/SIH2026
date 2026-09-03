"""OCR data schemas preserving evidence, geometry, layout, and spatial relationships."""
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field
from .image_schema import QualityReport, ImageMetadata


class GeometryModel(BaseModel):
    x1: int = Field(..., description="Top-left X coordinate in pixels")
    y1: int = Field(..., description="Top-left Y coordinate in pixels")
    x2: int = Field(..., description="Bottom-right X coordinate in pixels")
    y2: int = Field(..., description="Bottom-right Y coordinate in pixels")
    width_px: int = Field(..., description="Bounding box width in pixels")
    height_px: int = Field(..., description="Bounding box height in pixels")
    center_x: int = Field(..., description="Center X coordinate in pixels")
    center_y: int = Field(..., description="Center Y coordinate in pixels")
    center: List[int] = Field(..., description="[center_x, center_y] array")
    area: int = Field(..., description="Bounding box area in square pixels")
    aspect_ratio: float = Field(..., description="Width divided by height")


class LayoutModel(BaseModel):
    coordinate_reference: str = Field(default="image", description="Reference system ('image' or 'package')")
    relative_x: float = Field(..., description="Normalized center X (center_x / image_width, 0.0-1.0)")
    relative_y: float = Field(..., description="Normalized center Y (center_y / image_height, 0.0-1.0)")
    region: str = Field(..., description="3x3 spatial grid region name")


class OrientationModel(BaseModel):
    angle_degrees: float = Field(..., description="Approximate text rotation angle in degrees")
    category: str = Field(..., description="Orientation category: horizontal, rotated, vertical, unknown")


class VisualModel(BaseModel):
    font_height_px: int = Field(..., description="Estimated font height in pixels")
    font_height_mm: Optional[float] = Field(default=None, description="Physical font height in mm (if scale calibrated)")
    scale_calibrated: bool = Field(default=False, description="Whether pixel to mm scale has been calibrated")


class OCRBlockModel(BaseModel):
    id: str = Field(..., description="Unique block identifier e.g. ocr_001")
    raw_text: str = Field(..., description="Original, unaltered OCR text output")
    normalized_text: str = Field(..., description="Deterministically normalized OCR text")
    confidence: float = Field(..., description="Confidence score from OCR engine (0.0 to 1.0)")
    confidence_level: str = Field(..., description="Confidence category: high, medium, or low")
    polygon: List[List[int]] = Field(..., description="List of [x, y] vertex coordinates representing the bounding polygon")
    bbox: List[int] = Field(..., description="Axis-aligned bounding box [x1, y1, x2, y2]")
    geometry: GeometryModel = Field(..., description="Detailed geometric parameters")
    layout: LayoutModel = Field(..., description="Spatial layout and grid region classification")
    orientation: OrientationModel = Field(..., description="Text orientation and angle")
    visual: VisualModel = Field(..., description="Visual text sizing metadata")
    reading_order: int = Field(..., description="Sequence index in top-to-bottom, left-to-right reading order")


class SpatialRelationModel(BaseModel):
    source: str = Field(..., description="Source OCR block ID")
    relation: str = Field(..., description="Geometric relationship: above, below, left_of, right_of, near, aligned_with, same_region")
    target: str = Field(..., description="Target OCR block ID")
    distance_px: float = Field(..., description="Euclidean distance in pixels between centers")


class PreprocessingInfoModel(BaseModel):
    profile: str = Field(..., description="Preprocessing profile used")
    operations: List[str] = Field(default_factory=list, description="Ordered list of applied preprocessing steps")


class OCREngineInfoModel(BaseModel):
    name: str = Field(..., description="OCR Engine name e.g. PaddleOCR")
    version: str = Field(..., description="Engine version or build info")
    device: str = Field(default="cpu", description="Execution device: cpu or gpu")


class OCRResultModel(BaseModel):
    document_id: str = Field(..., description="Unique document identifier")
    status: str = Field(default="success", description="Processing status: success, warning, or failed")
    image: ImageMetadata = Field(..., description="Input image metadata")
    quality: QualityReport = Field(..., description="Image quality inspection report")
    preprocessing: PreprocessingInfoModel = Field(..., description="Applied preprocessing steps")
    ocr_engine: OCREngineInfoModel = Field(..., description="OCR engine information")
    ocr_blocks: List[OCRBlockModel] = Field(default_factory=list, description="Extracted OCR text blocks")
    spatial_relations: List[SpatialRelationModel] = Field(default_factory=list, description="Spatial relationships between OCR blocks")
    ocr_pass: str = Field(default="primary", description="Pass identifier (e.g., primary, multi_pass_enhanced)")


class ErrorResponseModel(BaseModel):
    status: str = Field(default="failed", description="Error status")
    error_code: str = Field(..., description="Standardized error code e.g. OCR_EMPTY_RESULT")
    message: str = Field(..., description="Human readable error message")
    document_id: Optional[str] = Field(default=None, description="Document ID if available")
    quality: Optional[QualityReport] = Field(default=None, description="Quality report if image was loaded")
