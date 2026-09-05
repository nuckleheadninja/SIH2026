import json
from pathlib import Path
from ocr_module.ocr.text_detector import TextDetector
from ocr_module.ocr.confidence_scorer import ConfidenceScorer
from ocr_module.layout.layout_analyzer import LayoutAnalyzer
from ocr_module.field_extraction.field_mapper import FieldMapper
from ocr_module.field_extraction.commodity_classifier import CommodityClassifier
from shared.constants import CommodityType


def test_text_detector():
    detector = TextDetector()
    blocks = detector.detect_text("sample.jpg")
    assert isinstance(blocks, list)
    assert len(blocks) > 0


def test_confidence_scorer():
    scorer = ConfidenceScorer(min_threshold=0.9)
    blocks = [{"text": "A", "confidence": 0.95}, {"text": "B", "confidence": 0.80}]
    filtered = scorer.filter_low_confidence(blocks)
    assert len(filtered) == 1


def test_layout_analyzer():
    analyzer = LayoutAnalyzer(image_height=1000)
    blocks = [{"text": "MRP", "bbox": [10, 10, 100, 20]}]
    augmented = analyzer.analyze_layout(blocks)
    assert "layout" in augmented[0]


def test_commodity_classifier():
    classifier = CommodityClassifier()
    blocks_food = [{"text": "FSSAI Lic No. 12345"}, {"text": "Nutritional Info"}]
    blocks_general = [{"text": "Plastic Bucket 10L"}]

    assert classifier.classify(blocks_food) == CommodityType.FOOD.value
    assert classifier.classify(blocks_general) == CommodityType.GENERAL.value


def test_field_mapper_with_sample_data():
    sample_path = Path(__file__).parent.parent.parent / "shared" / "sample_data" / "sample_ocr_output.json"
    with open(sample_path, "r", encoding="utf-8") as f:
        sample_ocr = json.load(f)

    mapper = FieldMapper()
    res = mapper.extract_fields(sample_ocr)
    assert res["image_id"] == "sample_pkg_001"
    assert "commodity_type" in res
    field_names = [f["field_name"] for f in res["extracted_fields"]]
    assert "mrp" in field_names
