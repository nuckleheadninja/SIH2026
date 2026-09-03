"""Aspect ratio preserving resize module."""
import cv2
import numpy as np
from typing import Tuple

def resize_image(image: np.ndarray, target_long_side: int = 1600) -> Tuple[np.ndarray, float]:
    """
    Resizes image maintaining aspect ratio such that the long side equals target_long_side.
    If image long side is already smaller than target_long_side, returns original.
    Returns (resized_image, scale_factor).
    scale_factor = resized_dim / original_dim.
    """
    height, width = image.shape[:2]
    long_side = max(height, width)

    if long_side <= target_long_side:
        return image, 1.0

    scale = target_long_side / float(long_side)
    new_width = int(round(width * scale))
    new_height = int(round(height * scale))

    resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
    return resized, scale
