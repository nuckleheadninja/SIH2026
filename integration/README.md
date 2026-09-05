# Integration & End-to-End Testing

## Overview
This folder contains end-to-end integration tests connecting:
1. `ocr_module/` (Text detection, layout analysis, field extraction)
2. `legal_metrology_rag/` (Query mapping, legal rule retrieval, citation generation)
3. `compliance_engine/` (Verdict decision engine)

## How to Run End-to-End Tests

```bash
pytest integration/end_to_end_test.py
```
