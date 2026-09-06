# 🛡️ Package Compliance Checker — SIH 26034

Automated multi-domain compliance verification system for pre-packaged commodities against **Legal Metrology (Packaged Commodities) Rules, 2011** and domain-specific regulations (e.g., **FSSAI Food Safety Regulations**).

---

## 🌟 Key Features & Subsystems

1. **📷 Computer Vision & OCR Module (`ocr_module/`)**:
   - **Preprocessing**: CLAHE anti-glare filtering, bilateral de-wrinkling, and cylindrical surface dewarping (`preprocessor.py`).
   - **Text Detection**: Dual-engine PaddleOCR 3.x with EasyOCR fallback and CPU oneDNN stability guards (`text_detector.py`).
   - **Layout Analysis**: Multi-column spatial density clustering and reading-order sorter (`layout_analyzer.py`).
   - **Field Extraction**: Multi-class product classification (Food, Cosmetics, General) and standardized regex/fuzzy rules for MRP, Net Quantity, Mfg/Expiry Dates, FSSAI License, INS Additive numbers, and Allergen tagging (`field_mapper.py`, `field_rules.py`).

2. **⚖️ Multi-Domain Legal Metrology RAG (`legal_metrology_rag/`)**:
   - **Structure-Aware Legal Chunker**: Hierarchical legal document chunking supporting Rule, Sub-Rule, Clause, and Schedule citations.
   - **Hybrid Retrieval Engine**: Vector search (Dense embeddings via `sentence-transformers` + ChromaDB) combined with BM25 Keyword retrieval (`rank_bm25`).
   - **Domain Router & Dispatcher**: Programmatic dispatch to Legal Metrology and FSSAI rules catalogues based on detected commodity type.
   - **Citation & Evidence Builder**: Generates immutable audit evidence payloads with exact page, rule, and text citations.

3. **📊 Compliance Decision Engine (`compliance_engine/`)**:
   - Compares extracted label fields against legal evidence constraints.
   - Outputs standardized `PASS` / `FAIL` / `UNCERTAIN` verdicts per declaration field and overall package compliance status.

4. **📱 SurakshaScan Live Dashboard (`frontend/`)**:
   - Streamlit interface supporting live phone camera capture via IP Webcam (1080p/4K), built-in webcam capture, and image uploads.
   - Interactive bounding-box visualizer, extracted field inspection, clean ingredient lists, allergen alerts, and RAG JSON payload export.

5. **🔄 End-to-End Master Pipeline (`verify_all.py` & `integration/`)**:
   - One-click script verifying complete integration flow from OCR -> Domain Router -> RAG -> Compliance Engine.

---

## 📁 Repository Architecture & Structure

```
SIH2026/
├── verify_all.py                          # One-Click Verification Script (OCR -> RAG -> Engine)
├── README.md                              # Master project overview & operation guide
├── VERIFICATION_PRD.md                    # PRD & Autonomous Agent Verification Protocol
├── venv/                                  # Virtual environment directory
│
├── shared/                                # Canonical Schemas & Data Contracts
│   ├── constants.py                       # ComplianceStatus, CommodityType constants
│   ├── schemas/
│   │   ├── ocr_output.schema.json         # Raw OCR bounding box & text contract
│   │   ├── field_extraction.schema.json   # Extracted label fields contract
│   │   ├── compliance_check.schema.json   # Compliance check query schema
│   │   └── evidence_output.schema.json    # Returned RAG evidence & citation format
│   └── sample_data/
│       ├── sample_ocr_output.json
│       └── sample_field_extraction_output.json
│
├── ocr_module/                            # Computer Vision & Extraction Module
│   ├── ocr/                               # text_detector.py, preprocessor.py, confidence_scorer.py
│   ├── layout/                            # layout_analyzer.py
│   ├── field_extraction/                  # field_mapper.py, field_rules.py, commodity_classifier.py
│   ├── tests/                             # test_ocr.py unit test suite
│   ├── requirements.txt
│   └── README.md
│
├── legal_metrology_rag/                   # Multi-Domain RAG Subsystem
│   ├── rag_core/                          # Shared RAG Engine (ingestion, chunking, retrieval, vector_store)
│   ├── domains/                           # Domain specializations (legal_metrology/, fssai/)
│   ├── dispatcher/                        # domain_router.py
│   ├── evaluation/                        # Benchmarks & retrieval evaluators
│   ├── tests/                             # Integration tests for RAG engine
│   ├── main.py                            # RAG CLI runner & benchmark launcher
│   ├── requirements.txt
│   └── README.md
│
├── compliance_engine/                     # Regulatory Decision Engine
│   ├── engine.py                          # Decision evaluator (PASS / FAIL / UNCERTAIN)
│   ├── tests/                             # test_engine.py
│   └── README.md
│
├── integration/                           # Integration Testing
│   ├── end_to_end_test.py                 # Full integration test suite
│   └── README.md
│
└── frontend/                              # Interactive Streamlit UI
    ├── app.py                             # SurakshaScan Streamlit Dashboard
    └── camera_utils.py                    # IP Webcam connector, autofocus, torch control
```

---

## 🛠️ Quick Start & Environment Setup

### 1. Prerequisites
- Python 3.10 or higher
- OpenCV & PyTorch system prerequisites

### 2. Create & Activate Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
Install requirements for all modules into the activated virtual environment:
```bash
pip install -r ocr_module/requirements.txt -r legal_metrology_rag/requirements.txt streamlit httpx
```

> [!NOTE]
> **CPU Safety Notice**: If running on Intel/AMD CPUs with PaddlePaddle 3.x, `FLAGS_use_mkldnn=0` is automatically applied inside `text_detector.py` to ensure crash-free inference.

---

## 🚀 Running the Project & Verification

### Step 1: Master Pipeline Verification
Run the one-click verification script to execute the full pipeline (OCR Extraction -> Contract Validation -> Domain Router -> Legal RAG -> Compliance Evaluation):

```bash
python verify_all.py
```

### Step 2: Automated Unit & Integration Test Suite
Run `pytest` across all test directories:

```bash
python -m pytest ocr_module/tests/ legal_metrology_rag/tests/ compliance_engine/tests/ integration/ -v
```

### Step 3: Run RAG Subsystem & Benchmarks
To run the RAG CLI runner with default sample inputs:
```bash
python legal_metrology_rag/main.py
```
To run the retrieval evaluation benchmark:
```bash
python legal_metrology_rag/main.py --eval
```

### Step 4: Launch SurakshaScan Streamlit Dashboard
To launch the interactive dashboard:

```bash
streamlit run frontend/app.py
```
Open your browser at `http://localhost:8501`.

---

## 📑 Data Schema Contracts

All inter-subsystem data flow is strictly typed and validated against JSON Schemas defined in `shared/schemas/`:

- **OCR Output**: Validated against `shared/schemas/ocr_output.schema.json`
- **Field Extraction**: Validated against `shared/schemas/field_extraction.schema.json`
- **RAG Evidence Output**: Validated against `shared/schemas/evidence_output.schema.json`

To manually validate sample output against schema:
```bash
python -c "import json, jsonschema; sample = json.load(open('shared/sample_data/sample_field_extraction_output.json')); schema = json.load(open('shared/schemas/field_extraction.schema.json')); jsonschema.validate(instance=sample, schema=schema); print('SCHEMA VALIDATION PASSED')"
```

---

## 📜 License & Acknowledgments
Built for **Smart India Hackathon (SIH) 2026** — Problem Statement 26034 (Automated Compliance Checking for Pre-Packaged Commodities).
