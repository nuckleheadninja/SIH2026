"""Confidence scorer for filtering or weighting OCR output."""

from typing import List, Dict, Any


class ConfidenceScorer:
    def __init__(self, min_threshold: float = 0.5):
        self.min_threshold = min_threshold

    def filter_low_confidence(self, text_blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filters out text blocks below minimum confidence threshold."""
        return [b for b in text_blocks if b.get("confidence", 0.0) >= self.min_threshold]

    def compute_average_confidence(self, text_blocks: List[Dict[str, Any]]) -> float:
        """Calculates average confidence score across all blocks."""
        if not text_blocks:
            return 0.0
        scores = [b.get("confidence", 0.0) for b in text_blocks]
        return float(sum(scores) / len(scores))
