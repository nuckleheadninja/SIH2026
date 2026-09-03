"""Configurable Preprocessing Pipeline with preset and auto profiles."""
import numpy as np
from typing import Tuple, List, Dict, Any
from models.image_schema import QualityReport
from .resize import resize_image
from .enhancement import apply_clahe, apply_denoise, apply_sharpening
from .perspective import deskew_image, correct_perspective


class PreprocessingPipeline:
    def __init__(self, config: Dict[str, Any]):
        self.config = config.get("preprocessing", {})
        self.target_long_side = self.config.get("target_long_side", 1600)

    def process(self, image: np.ndarray, quality_report: QualityReport, profile_override: str = None) -> Tuple[np.ndarray, str, List[str]]:
        """
        Applies preprocessing steps based on chosen or auto-detected profile.
        Returns (preprocessed_image, profile_used, applied_operations_list).
        """
        profile = (profile_override or self.config.get("profile", "auto")).lower()

        if profile == "auto":
            profile = self._determine_auto_profile(quality_report)

        processed = image.copy()
        operations: List[str] = []

        # 1. Always apply controlled resize if long side exceeds threshold
        processed, scale = resize_image(processed, target_long_side=self.target_long_side)
        if scale < 1.0:
            operations.append(f"resize (scaled by {scale:.2f})")

        # 2. Apply profile-specific pipeline sequence
        if profile == "low_contrast":
            processed = apply_clahe(processed)
            operations.append("clahe")
            processed = apply_sharpening(processed)
            operations.append("sharpening")

        elif profile == "noisy":
            processed = apply_denoise(processed)
            operations.append("denoise")
            processed = apply_clahe(processed)
            operations.append("clahe")

        elif profile == "perspective":
            processed, warped = correct_perspective(processed)
            if warped:
                operations.append("perspective_correction")
            processed, angle = deskew_image(processed)
            if abs(angle) > 0.0:
                operations.append(f"deskew ({angle:.1f}deg)")
            processed = apply_clahe(processed)
            operations.append("clahe")

        elif profile == "default":
            processed = apply_clahe(processed)
            operations.append("clahe")
            processed = apply_denoise(processed, h=5.0)
            operations.append("mild_denoise")

        else:  # Fallback for unknown profile names
            processed = apply_clahe(processed)
            operations.append("clahe")

        return processed, profile, operations

    def _determine_auto_profile(self, quality: QualityReport) -> str:
        """Determines best preprocessing profile based on quality metrics."""
        if quality.contrast < 40.0:
            return "low_contrast"
        elif quality.blur_score < 100.0:
            return "noisy"
        else:
            return "default"
