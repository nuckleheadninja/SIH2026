"""OCR engine adapter architecture and conservative postprocessing package."""
from .base import BaseOCREngine, OCRRawDetection
from .paddle_engine import PaddleOCREngine
from .easyocr_engine import EasyOCREngine
from .postprocessor import ConservativePostProcessor

__all__ = [
    "BaseOCREngine",
    "OCRRawDetection",
    "PaddleOCREngine",
    "EasyOCREngine",
    "ConservativePostProcessor"
]
