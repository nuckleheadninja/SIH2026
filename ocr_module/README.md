# OCR & Field Extraction Module

## Overview
This module detects text on product packaging, computes confidence scores, performs spatial layout analysis (font height, position), and maps text blocks to standardized Legal Metrology declaration fields.

## Directory Layout
- `ocr/`: `text_detector.py`, `confidence_scorer.py`
- `layout/`: `layout_analyzer.py`
- `field_extraction/`: `field_mapper.py`, `field_rules.py`
- `tests/`: Module unit tests

## How to Run Standalone

1. Install module dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run test suite:
   ```bash
   pytest tests/
   ```

3. Example Usage:
   ```python
   from ocr_module.ocr.text_detector import TextDetector
   from ocr_module.layout.layout_analyzer import LayoutAnalyzer
   from ocr_module.field_extraction.field_mapper import FieldMapper

   detector = TextDetector()
   blocks = detector.detect_text("path/to/packaging.jpg")
   
   analyzer = LayoutAnalyzer()
   blocks_with_layout = analyzer.analyze_layout(blocks)

   mapper = FieldMapper()
   result = mapper.extract_fields({"image_id": "test_001", "text_blocks": blocks_with_layout})
   print(result)
   ```
