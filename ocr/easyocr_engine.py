"""EasyOCR engine adapter implementation."""
import logging
from typing import List
import numpy as np
from .base import BaseOCREngine, OCRRawDetection

logger = logging.getLogger(__name__)

class EasyOCREngine(BaseOCREngine):
    def __init__(self, use_gpu: bool = False, lang: str = "en"):
        super().__init__(use_gpu=use_gpu, lang=lang)
        self._reader = None
        self._version = "1.7.0"
        self._initialize_engine()

    def _initialize_engine(self):
        try:
            import easyocr
            langs = [self.lang] if isinstance(self.lang, str) else self.lang
            self._reader = easyocr.Reader(langs, gpu=self.use_gpu)
            logger.info("EasyOCR engine initialized successfully.")
        except Exception as e:
            logger.warning(f"EasyOCR initialization warning: {e}")
            self._reader = None

    @property
    def engine_name(self) -> str:
        return "EasyOCR"

    @property
    def engine_version(self) -> str:
        return self._version

    def detect_text(self, image: np.ndarray) -> List[OCRRawDetection]:
        if self._reader is not None:
            try:
                results = self._reader.readtext(image)
                return self._parse_easyocr_results(results)
            except Exception as e:
                logger.error(f"Error during EasyOCR execution: {e}")

        logger.info("Executing mock/fallback text detector for EasyOCR.")
        return []

    def _parse_easyocr_results(self, results) -> List[OCRRawDetection]:
        detections: List[OCRRawDetection] = []
        for bbox_pts, text, conf in results:
            polygon = [[int(pt[0]), int(pt[1])] for pt in bbox_pts]
            xs = [pt[0] for pt in polygon]
            ys = [pt[1] for pt in polygon]
            bbox = [min(xs), min(ys), max(xs), max(ys)]

            detections.append(OCRRawDetection(
                raw_text=text,
                confidence=float(conf),
                polygon=polygon,
                bbox=bbox
            ))
        return detections
