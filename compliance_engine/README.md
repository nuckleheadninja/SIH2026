# Compliance Engine (Stub / Future Integration Point)

> **Status**: Stub implementation. Marked for future integration once full OCR and RAG models are trained and integrated.

## Description
The Compliance Engine takes:
1. Standardized **Field Extraction Output** from `ocr_module/` (`field_extraction.schema.json`)
2. Legal **Evidence & Citations** from `legal_metrology_rag/` (`evidence_output.schema.json`)

It processes both payloads to return a final compliance verdict (`PASS`, `FAIL`, `UNCERTAIN`, `NOT_APPLICABLE`) along with structured reasoning.

## How to Test Standalone
```bash
pytest tests/
```
