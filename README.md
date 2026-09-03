# OCR + Layout Analysis Module for AI-Based Legal Metrology & FSSAI Compliance Checker

**SIH Problem Statement ID:** 26034 | **Ministry of Consumer Affairs**

This repository contains the foundational **OCR & Spatial Layout Analysis Module** (Stages 1–4 of the overall compliance verification pipeline) designed for scanning packaged food/commodity product labels.

---

## Key Features

1. **Evidence-Preserving Schema**: Retains `raw_text`, `normalized_text`, polygon vertices, bounding boxes, confidence %, orientation angles, font pixel height, and spatial grid regions without discarding original OCR output.
2. **Deterministic Post-Processing**: Performs conservative normalization (whitespace, unicode, standard label prefixes like `M.R.P.` to `MRP`) **without hallucination**. Never silently changes ambiguous text like `₹1O0` to `₹100`.
3. **Image Quality Inspection**: Performs blur scoring (Laplacian variance), contrast inspection, and brightness validation. Warns without rejecting imperfect real-world photos.
4. **Adaptive Preprocessing Pipeline**: Configurable profiles (`DEFAULT`, `LOW_CONTRAST`, `NOISY`, `PERSPECTIVE`, `AUTO`) supporting CLAHE, unsharp masking, bilateral denoising, deskewing, and perspective correction.
5. **3x3 Spatial Grid Classification**: Assigns spatial regions (`top-left`, `top-center`, `top-right`, `middle-left`, `center`, `middle-right`, `bottom-left`, `bottom-center`, `bottom-right`) based on normalized image coordinates (`coordinate_reference: "image"`).
6. **Pairwise Spatial Relationships**: Calculates deterministic geometric relationships (`above`, `below`, `left_of`, `right_of`, `near`, `aligned_with`, `same_region`) to assist downstream Field Extraction and RAG reasoning.
7. **Modular OCR Architecture**: Modular `BaseOCREngine` interface supporting `PaddleOCR` (primary) and `EasyOCR` with graceful fallback capabilities.

---

## Directory Structure

```text
SIH2026/
│
├── ocr/                  # OCR Engine adapters & conservative postprocessor
│   ├── base.py           # Abstract OCR engine interface
│   ├── paddle_engine.py  # PaddleOCR adapter with fallback
│   ├── easyocr_engine.py # EasyOCR adapter
│   └── postprocessor.py # Conservative text normalization
│
├── preprocessing/        # Image validation & preprocessing pipeline
│   ├── validation.py     # Quality inspection & blur scoring
│   ├── resize.py         # Aspect ratio preserving resize
│   ├── enhancement.py    # CLAHE, Denoise, Sharpening, Thresholding
│   ├── perspective.py    # Deskewing & Perspective transform
│   └── pipeline.py       # Configurable preprocessing pipeline
│
├── layout/               # Geometry & spatial analysis
│   ├── geometry.py       # Bounding box, center, area, angle math
│   ├── region.py         # 3x3 Grid region classifier
│   └── analyzer.py       # Reading order & spatial relations
│
├── models/               # Pydantic schemas
│   ├── image_schema.py   # Quality report & image metadata
│   └── ocr_schema.py     # OCR Block, Geometry, Layout, Result models
│
├── utils/                # Utilities & Visualizations
│   ├── image_utils.py    # I/O functions
│   ├── visualization.py  # Debug overlay generator
│   └── logging_utils.py  # Standardized console logging
│
├── tests/                # Automated unit tests
├── input/                # Input image directory
├── output/               # Output JSON and annotated image directory
├── config.yaml           # Centralized configuration
├── requirements.txt      # Dependency specification
└── main.py               # CLI entrypoint pipeline
```

---

## Quick Start

### 1. Installation

```bash
pip install -r requirements.txt
```

### 2. Run Inference on Sample Product Label

If no input image is provided, running `main.py` automatically generates a synthetic sample packaged product label in `input/product_001.jpg` and runs the complete pipeline:

```bash
python main.py
```

To run on a custom image or folder:

```bash
python main.py --input input/my_product.jpg --config config.yaml
```

To enable multi-pass OCR:

```bash
python main.py --input input/product_001.jpg --multi-pass
```

### 3. Run Unit Tests

Execute the unit test suite covering validation, geometry, relative coordinates, region classification, schemas, and end-to-end OCR execution:

```bash
pytest tests/
```

---

## Output Artifacts

For every processed image `product_001.jpg`, an output folder is generated at `output/product_001/`:

1. **`ocr_result.json`**: Structured evidence JSON containing image metadata, quality inspection report, applied preprocessing profile, OCR engine details, OCR text blocks, and spatial relationships.
2. **`annotated.jpg`**: Visual debug overlay showing bounding polygons, text block IDs, OCR raw text, confidence score %, and spatial region tags.
3. **`preprocessed.jpg`**: The exact image fed into the OCR engine after CLAHE/denoising/sharpening.

---

## CPU vs GPU Execution

Execution device is controlled via `config.yaml`:

```yaml
ocr:
  engine: paddleocr
  use_gpu: false  # Set to true when running on GPU / CUDA enabled environment
```

---

## Integration Contract for Next Modules

The `ocr_result.json` produced by this module serves as the immutable evidence contract for downstream modules:

1. **Field Extraction Module**: Consumes `ocr_blocks` and maps text blocks to legal fields (`MRP`, `NET QTY`, `MFG DATE`, `ADDRESS`, `INGREDIENTS`, `FSSAI LIC NO`).
2. **Legal Metrology & FSSAI RAG Modules**: Consumes extracted fields and spatial regions to perform citable legal compliance checks.
