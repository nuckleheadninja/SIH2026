"""Image enhancement techniques: Grayscale, CLAHE, Denoising, Sharpening, Adaptive Thresholding."""
import cv2
import numpy as np
from typing import Tuple

def apply_grayscale(image: np.ndarray) -> np.ndarray:
    """Converts BGR image to 3-channel grayscale for downstream OpenCV compatibility."""
    if len(image.shape) == 2:
        gray = image
    else:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

def apply_clahe(image: np.ndarray, clip_limit: float = 2.0, tile_grid_size: Tuple[int, int] = (8, 8)) -> np.ndarray:
    """Applies Contrast Limited Adaptive Histogram Equalization (CLAHE)."""
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    if len(image.shape) == 3:
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        l_clahe = clahe.apply(l)
        enhanced_lab = cv2.merge((l_clahe, a, b))
        return cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
    else:
        return clahe.apply(image)

def apply_denoise(image: np.ndarray, h: float = 10.0) -> np.ndarray:
    """Applies non-local means denoising while preserving text edge clarity."""
    if len(image.shape) == 3:
        return cv2.fastNlMeansDenoisingColored(image, None, h, h, 7, 21)
    else:
        return cv2.fastNlMeansDenoising(image, None, h, 7, 21)

def apply_sharpening(image: np.ndarray, strength: float = 1.0) -> np.ndarray:
    """Applies high-pass unsharp mask sharpening to enhance small product label font edges."""
    gaussian = cv2.GaussianBlur(image, (0, 0), 3)
    sharpened = cv2.addWeighted(image, 1.0 + strength, gaussian, -strength, 0)
    return sharpened

def apply_adaptive_threshold(image: np.ndarray) -> np.ndarray:
    """Applies adaptive Gaussian thresholding for high contrast binarized view."""
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    return cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)
