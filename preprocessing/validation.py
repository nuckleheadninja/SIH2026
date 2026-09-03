"""Image validation and quality inspection implementation."""
import os
import cv2
import numpy as np
from typing import Tuple, List
from models.image_schema import QualityReport, ImageMetadata

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

def validate_image(image_path: str) -> Tuple[bool, ImageMetadata, QualityReport, Optional_np_array]:
    """
    Validates file existence, format, decodability, and inspects quality metrics.
    Does NOT reject an image solely because it is imperfect.
    Returns (success_flag, ImageMetadata, QualityReport, cv2_image_ndarray)
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file does not exist: {image_path}")

    ext = os.path.splitext(image_path)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported image extension '{ext}'. Supported formats: {SUPPORTED_EXTENSIONS}")

    file_size = os.path.getsize(image_path)
    if file_size == 0:
        raise ValueError(f"Image file is empty (0 bytes): {image_path}")

    image = cv2.imread(image_path)
    if image is None:
        try:
            stream = np.fromfile(image_path, dtype=np.uint8)
            image = cv2.imdecode(stream, cv2.IMREAD_COLOR)
        except Exception:
            image = None

    if image is None:
        raise ValueError(f"Failed to decode image from path: {image_path}")

    height, width = image.shape[:2]
    channels = image.shape[2] if len(image.shape) > 2 else 1
    aspect_ratio = round(width / float(height), 4)

    metadata = ImageMetadata(
        path=image_path,
        width=width,
        height=height,
        channels=channels,
        aspect_ratio=aspect_ratio,
        file_format=ext[1:].upper(),
        file_size_bytes=file_size
    )

    # Convert to grayscale for quality calculations
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    # Quality metrics computation
    blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    brightness = float(np.mean(gray))
    contrast = float(np.std(gray))

    warnings: List[str] = []
    status = "acceptable"

    if blur_score < 100.0:
        warnings.append(f"Image appears blurry (Laplacian variance: {blur_score:.1f} < 100.0)")
        status = "warning"

    if brightness < 40.0:
        warnings.append(f"Image is dark (Brightness: {brightness:.1f} < 40.0)")
        status = "warning"
    elif brightness > 220.0:
        warnings.append(f"Image is overexposed (Brightness: {brightness:.1f} > 220.0)")
        status = "warning"

    if contrast < 35.0:
        warnings.append(f"Image has low contrast (Contrast std: {contrast:.1f} < 35.0)")
        status = "warning"

    if width < 300 or height < 300:
        warnings.append(f"Low image resolution ({width}x{height} pixels)")
        status = "warning"

    quality_report = QualityReport(
        width=width,
        height=height,
        blur_score=round(blur_score, 2),
        brightness=round(brightness, 2),
        contrast=round(contrast, 2),
        quality_status=status,
        warnings=warnings
    )

    return True, metadata, quality_report, image


# Helper type annotation workaround
Optional_np_array = np.ndarray
