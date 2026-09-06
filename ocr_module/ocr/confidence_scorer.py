from typing import List, Dict, Any


class ConfidenceScorer:
    """
    Evaluates and filters OCR text blocks based on detection confidence thresholds.
    """

    def __init__(self, min_threshold: float = 0.5):
        self.min_threshold = min_threshold

    def filter_low_confidence(self, blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Returns only blocks whose confidence meets or exceeds min_threshold.
        """
        filtered = []
        for block in blocks:
            conf = block.get("confidence", 1.0)
            if conf >= self.min_threshold:
                filtered.append(block)
        return filtered

    def calculate_average_confidence(self, blocks: List[Dict[str, Any]]) -> float:
        """
        Calculates the mean confidence across all detected blocks.
        """
        if not blocks:
            return 0.0
        scores = [b.get("confidence", 0.0) for b in blocks]
        return round(sum(scores) / len(scores), 4)
