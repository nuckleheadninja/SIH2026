# PRD & Verification Specification: OCR, Vision & Frontend Integration in SIH2026

**Document Type**: Product Requirements Document (PRD) & Autonomous Agent Verification Protocol  
**Target Repository**: `SIH2026` (`https://github.com/adidev001/SIH2026.git`)  
**Integrated Subsystems**: `ocr_module/`, `frontend/`, `shared/schemas/`  
**Downstream Consumers**: `legal_metrology_rag/`, `compliance_engine/`, `integration/`  

---

## 1. Executive Summary & Objective

In this release, the placeholder/mock implementation of `ocr_module/` in `SIH2026` has been upgraded to a production-grade Computer Vision, Text Detection, Multi-Column Layout Analysis, and Regulatory Information Extraction pipeline, supplemented by an interactive Streamlit UI.

### Primary Goal for the Agent:
Verify that the integrated OCR pipeline:
1. Passes all unit tests (`ocr_module/tests/test_ocr.py`) with zero failures.
2. Produces JSON outputs that strictly comply with `shared/schemas/field_extraction.schema.json` and `shared/schemas/ocr_output.schema.json`.
3. Feeds cleanly into downstream consumers (`domain_router.py`, `legal_metrology_rag`, `compliance_engine`, and `integration/end_to_end_test.py`).
4. Runs stably on both CPU (with oneDNN safety guards) and GPU without crashes.

---

## 2. File Inventory & System Architecture

```
SIH2026/
├── ocr_module/
│   ├── ocr/
│   │   ├── preprocessor.py        # [NEW] Anti-glare CLAHE, bilateral de-wrinkling, cylindrical dewarp
│   │   ├── text_detector.py       # [UPGRADED] PaddleOCR 3.x + EasyOCR fallback + test mock safety
│   │   └── confidence_scorer.py   # [UPGRADED] Confidence score thresholding and mean calculation
│   ├── layout/
│   │   └── layout_analyzer.py     # [UPGRADED] Multi-column density clustering & reading-order sorter
│   ├── field_extraction/
│   │   ├── commodity_classifier.py# [UPGRADED] Multi-class food / cosmetic / general classification
│   │   ├── field_rules.py         # [UPGRADED] Standardized regex rules for MRP, Net Qty, FSSAI, Dates, INS
│   │   └── field_mapper.py        # [UPGRADED] Schema translation with fuzzy ingredients & allergen parser
│   ├── tests/
│   │   └── test_ocr.py            # [UPGRADED] 6 comprehensive unit tests + formal JSON Schema validation
│   └── requirements.txt           # [UPGRADED] Dependencies (paddleocr, easyocr, opencv, rapidfuzz)
├── frontend/                      # [NEW] Interactive Dashboard
│   ├── app.py                     # Streamlit App (Live camera, BBox visualizer, RAG JSON exporter)
│   └── camera_utils.py            # IP Webcam stream grabber, autofocus, and torch control
└── shared/
    ├── constants.py               # CommodityType (food, general_commodity, drugs_cosmetics)
    ├── schemas/
    │   ├── ocr_output.schema.json
    │   └── field_extraction.schema.json
    └── sample_data/
        ├── sample_ocr_output.json
        └── sample_field_extraction_output.json
```

---

## 3. Environment Setup & Prerequisites

Before running verification, ensure the Python environment has the necessary dependencies installed:

```bash
# Activate existing repo virtual environment or create a new one
python -m venv venv
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
source venv/bin/activate

# Install OCR and Vision dependencies
pip install -r ocr_module/requirements.txt
```

> [!IMPORTANT]
> **CPU oneDNN Safety Notice**:
> If running on Intel/AMD CPUs with PaddlePaddle 3.x, ensure environment variable `FLAGS_use_mkldnn=0` is set (this is already hardcoded inside `text_detector.py` to prevent `ConvertPirAttribute2RuntimeAttribute` crashes).

---

## 4. Step-by-Step Agent Verification Protocol

The executing agent must perform the following 5 verification steps in sequence:

### Step 1: Unit Test Suite Verification
Run pytest on the OCR module test suite:
```bash
pytest ocr_module/tests/test_ocr.py -v
```

**Expected Result**:
```
collected 6 items

test_text_detector PASSED                     [ 16%]
test_confidence_scorer PASSED                 [ 33%]
test_layout_analyzer PASSED                   [ 50%]
test_commodity_classifier PASSED              [ 66%]
test_field_mapper_with_sample_data PASSED     [ 83%]
test_preprocessor_synthetic_image PASSED      [100%]

============================== 6 passed ==============================
```

---

### Step 2: Contract & Schema Compliance Verification
Verify that `FieldMapper` outputs conform 100% to `shared/schemas/field_extraction.schema.json`.

Execute this Python one-liner in the repository root:
```bash
python -c "import json, jsonschema; from pathlib import Path; from ocr_module.field_extraction.field_mapper import FieldMapper; sample = json.load(open('shared/sample_data/sample_ocr_output.json')); schema = json.load(open('shared/schemas/field_extraction.schema.json')); res = FieldMapper().extract_fields(sample); jsonschema.validate(instance=res, schema=schema); print('SCHEMA VALIDATION PASSED: 100% COMPLIANT')"
```

**Expected Output**:
`SCHEMA VALIDATION PASSED: 100% COMPLIANT`

---

### Step 3: End-to-End Downstream Integration Test
Verify that the output of `ocr_module` passes cleanly into the team's downstream RAG dispatcher and compliance engine.

Run the repository's integration test:
```bash
python integration/end_to_end_test.py
```

If running individual components programmatically:
```python
import json
from ocr_module.field_extraction.field_mapper import FieldMapper
from legal_metrology_rag.dispatcher.domain_router import DomainRouter

# 1. Load OCR data
with open("shared/sample_data/sample_ocr_output.json", "r") as f:
    ocr_data = json.load(f)

# 2. Extract fields
mapper = FieldMapper()
extracted = mapper.extract_fields(ocr_data)

# 3. Route to domain RAG
router = DomainRouter()
domain = router.route(extracted)
print(f"Domain routed to: {domain}")
assert domain in ["fssai", "legal_metrology"]
```

---

### Step 4: Real Image Inference Verification
Verify that `TextDetector` and `PackagingPreprocessor` can process a real image file or numpy array without error:

```python
import cv2
import numpy as np
from ocr_module.ocr.preprocessor import PackagingPreprocessor
from ocr_module.ocr.text_detector import TextDetector
from ocr_module.field_extraction.field_mapper import FieldMapper

# Create a test synthetic label
img = np.full((300, 600, 3), 255, dtype=np.uint8)
cv2.putText(img, "MRP Rs. 150.00", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)
cv2.putText(img, "Net Qty: 200 g", (30, 160), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)
cv2.putText(img, "FSSAI Lic. No. 10012345678901", (30, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)

# Run full pipeline
detector = TextDetector()
blocks = detector.detect_text(img)
mapper = FieldMapper()
result = mapper.extract_fields(blocks)

print(f"Extracted {len(result['extracted_fields'])} fields: {[f['field_name'] for f in result['extracted_fields']]}")
assert any(f["field_name"] == "mrp" for f in result["extracted_fields"])
assert any(f["field_name"] == "net_quantity" for f in result["extracted_fields"])
```

---

### Step 5: Frontend UI Launch Verification
Verify that the interactive Streamlit dashboard boots without syntax or import errors:

```bash
streamlit run frontend/app.py --server.headless true
```

**Checkpoints**:
- Navigate to `http://localhost:8501`.
- Verify the following components render properly:
  - 📷 Camera input & WiFi / IP Webcam selector.
  - 🖼️ Bounding box overlay inspection tab.
  - 📋 Clean ingredients & allergen badges.
  - 📥 Download RAG JSON payload button.

---

## 5. Acceptance Criteria Checklist

| Check | Requirement | Verification Method | Pass Condition |
| :---: | :--- | :--- | :---: |
| ✅ | Unit Test Coverage | `pytest ocr_module/tests/test_ocr.py` | 6/6 tests pass |
| ✅ | Schema Fidelity | `jsonschema.validate` against `field_extraction.schema.json` | 0 validation errors |
| ✅ | CPU Stability | PaddleOCR inference on CPU | No oneDNN / PIR runtime crash |
| ✅ | Multi-column Layout | `LayoutAnalyzer.analyze_layout` | Column clustering prevents text mixing |
| ✅ | Ingredients & Allergens | Fuzzy header extraction (`NGREDETEES`, `INGREDIENTS:`) | Clean item list + isolated allergens |
| ✅ | INS Additive Tagging | Regex detection for INS numbers | E.g. `INS 330`, `INS 170(i)` captured |
| ✅ | Downstream Integration | Feed output into `DomainRouter` & `ComplianceEngine` | No KeyError or unexpected types |
| ✅ | Frontend Usability | `streamlit run frontend/app.py` | UI opens cleanly on port 8501 |

---

## 6. Git Commit & PR Protocol

Once all checks pass, commit and open a PR into the main repository branch:

```bash
git checkout -b feature/real-ocr-pipeline
git add ocr_module/ frontend/
git commit -m "feat(ocr): integrate production PaddleOCR, anti-glare preprocessor, layout analysis and field extraction"
git push origin feature/real-ocr-pipeline
```

*(Create a Pull Request against `main` for team review and merge).*
