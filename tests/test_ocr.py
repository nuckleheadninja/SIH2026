"""Unit tests for OCR postprocessor and pipeline integration."""
from ocr.postprocessor import ConservativePostProcessor
from main import process_image, load_config
from utils.create_sample_label import generate_sample_label

def test_conservative_postprocessor():
    raw_1 = "M.R.P.  ₹ 120.00 "
    norm_1 = ConservativePostProcessor.normalize(raw_1)
    assert norm_1 == "MRP ₹ 120.00"

    # Verify numbers & potential digit ambiguities are NEVER altered
    raw_2 = "NET QTY: 500g ₹1O0"
    norm_2 = ConservativePostProcessor.normalize(raw_2)
    assert "₹1O0" in norm_2  # Must not hallucinate '1O0' into '100'

def test_end_to_end_pipeline(tmp_path):
    img_path = str(tmp_path / "test_product.jpg")
    generate_sample_label(img_path)

    config = {
        "ocr": {"engine": "paddleocr", "use_gpu": False},
        "preprocessing": {"profile": "auto"},
        "output": {"output_dir": str(tmp_path / "output")}
    }

    result = process_image(img_path, config)
    assert result["status"] == "success"
    assert len(result["ocr_blocks"]) > 0
    assert result["ocr_engine"]["name"] == "PaddleOCR"
    assert result["quality"]["quality_status"] in ["acceptable", "warning"]
