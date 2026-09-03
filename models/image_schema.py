"""Image validation and quality report schemas."""
from typing import List, Optional
from pydantic import BaseModel, Field


class ImageMetadata(BaseModel):
    path: str = Field(..., description="Path to the input image file")
    width: int = Field(..., description="Image width in pixels")
    height: int = Field(..., description="Image height in pixels")
    channels: int = Field(default=3, description="Number of color channels")
    aspect_ratio: float = Field(..., description="Width divided by height")
    file_format: str = Field(..., description="Image format extension (e.g. JPG, PNG)")
    file_size_bytes: int = Field(..., description="Size of file on disk in bytes")


class QualityReport(BaseModel):
    width: int = Field(..., description="Image width in pixels")
    height: int = Field(..., description="Image height in pixels")
    blur_score: float = Field(..., description="Laplacian variance blur score (higher = sharper)")
    brightness: float = Field(..., description="Mean pixel brightness (0-255)")
    contrast: float = Field(..., description="Standard deviation of pixel intensity")
    quality_status: str = Field(..., description="Status: acceptable, warning, or rejected")
    warnings: List[str] = Field(default_factory=list, description="List of quality warnings")
