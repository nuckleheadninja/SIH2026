import sys
import json
from pathlib import Path

# Automatically ensure integrated_package root is in sys.path
PACKAGE_ROOT = Path(__file__).parent.parent.parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from ocr_module.ocr.preprocessor import PackagingPreprocessor
from ocr_module.ocr.text_detector import TextDetector
from ocr_module.ocr.confidence_scorer import ConfidenceScorer
from ocr_module.layout.layout_analyzer import LayoutAnalyzer
from ocr_module.field_extraction.field_mapper import FieldMapper
from ocr_module.field_extraction.commodity_classifier import CommodityClassifier
from shared.constants import CommodityType


def test_text_detector():
    """Verifies TextDetector handles mock strings and returns valid blocks."""
    detector = TextDetector()
    blocks = detector.detect_text("sample.jpg")
    assert isinstance(blocks, list)
    assert len(blocks) > 0
    assert "text" in blocks[0]
    assert "confidence" in blocks[0]


def test_confidence_scorer():
    """Verifies threshold filtering."""
    scorer = ConfidenceScorer(min_threshold=0.9)
    blocks = [{"text": "A", "confidence": 0.95}, {"text": "B", "confidence": 0.80}]
    filtered = scorer.filter_low_confidence(blocks)
    assert len(filtered) == 1
    assert filtered[0]["text"] == "A"


def test_layout_analyzer():
    """Verifies layout position augmentation and column clustering."""
    analyzer = LayoutAnalyzer(image_height=1000)
    blocks = [{"text": "MRP", "bbox": [10, 10, 100, 20]}]
    augmented = analyzer.analyze_layout(blocks)
    assert "layout" in augmented[0]
    assert "layout_position" in augmented[0]
    assert "font_height_px" in augmented[0]


def test_commodity_classifier():
    """Verifies classification between food, drugs/cosmetics, and general."""
    classifier = CommodityClassifier()
    blocks_food = [{"text": "FSSAI Lic No. 12345"}, {"text": "Nutritional Info"}]
    blocks_general = [{"text": "Plastic Bucket 10L"}]

    assert classifier.classify(blocks_food) == CommodityType.FOOD.value
    assert classifier.classify(blocks_general) == CommodityType.GENERAL.value


def test_field_mapper_with_sample_data():
    """Verifies extraction and schema compliance against sample OCR output."""
    sample_path = Path(__file__).parent.parent.parent / "shared" / "sample_data" / "sample_ocr_output.json"
    with open(sample_path, "r", encoding="utf-8") as f:
        sample_ocr = json.load(f)

    mapper = FieldMapper()
    res = mapper.extract_fields(sample_ocr)
    assert res["image_id"] == "sample_pkg_001"
    assert "commodity_type" in res

    field_names = [f["field_name"] for f in res["extracted_fields"]]
    assert "mrp" in field_names
    assert "net_quantity" in field_names

    # Formal JSON schema validation
    schema_path = Path(__file__).parent.parent.parent / "shared" / "schemas" / "field_extraction.schema.json"
    if schema_path.exists():
        import jsonschema
        with open(schema_path, "r", encoding="utf-8") as sf:
            schema = json.load(sf)
        jsonschema.validate(instance=res, schema=schema)


def test_field_mapper_food_with_ingredients():
    """Verifies fuzzy ingredients, allergens, and INS extraction on food packaging."""
    food_ocr = {
        "image_id": "food_sample_001",
        "text_blocks": [
            {"text": "FSSAI Lic. No. 10012011000168", "confidence": 0.98, "bbox": [10, 10, 200, 20]},
            {"text": "MRP Rs. 14.00", "confidence": 0.96, "bbox": [10, 40, 100, 20]},
            {"text": "Net Qty: 70 g", "confidence": 0.95, "bbox": [10, 70, 80, 20]},
            {"text": "Ingredients: Wheat Flour, Palm Oil, Salt, Acidity Regulator (INS 330), Allergen Note: May contain Milk and Soy.", "confidence": 0.94, "bbox": [10, 100, 500, 50]}
        ]
    }
    mapper = FieldMapper()
    res = mapper.extract_fields(food_ocr)
    assert res["commodity_type"] == CommodityType.FOOD.value

    field_names = [f["field_name"] for f in res["extracted_fields"]]
    assert "mrp" in field_names
    assert "net_quantity" in field_names
    assert "fssai_license" in field_names
    assert "ingredients" in field_names
    assert "allergens" in field_names
    assert "ins_additives" in field_names


def test_preprocessor_synthetic_image():
    """Verifies preprocessor functions on synthetic image array without error."""
    import numpy as np
    img = np.full((100, 100, 3), 200, dtype=np.uint8)
    processed = PackagingPreprocessor.preprocess_image(img, apply_anti_glare=True, apply_dewrinkle=True)
    assert processed is not None
    assert processed.shape == (100, 100, 3)
