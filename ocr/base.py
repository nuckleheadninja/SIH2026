"""Abstract base class interface for modular OCR engines."""
from abc import ABC, abstractmethod
from typing import List, Tuple
from dataclasses import dataclass
import numpy as np


@dataclass
class OCRRawDetection:
    raw_text: str
    confidence: float
    polygon: List[List[int]]
    bbox: List[int]  # [x1, y1, x2, y2]


class BaseOCREngine(ABC):
    def __init__(self, use_gpu: bool = False, lang: str = "en"):
        self.use_gpu = use_gpu
        self.lang = lang

    @abstractmethod
    def detect_text(self, image: np.ndarray) -> List[OCRRawDetection]:
        """
        Executes text detection and recognition on an input image numpy ndarray.
        Returns a list of OCRRawDetection objects preserving original polygons and confidences.
        """
        pass

    @property
    @abstractmethod
    def engine_name(self) -> str:
        pass

    @property
    @abstractmethod
    def engine_version(self) -> str:
        pass
