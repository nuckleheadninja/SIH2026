# Package Compliance Checker

Automated compliance verification system for pre-packaged commodities against Legal Metrology Rules and domain-specific regulations (e.g., FSSAI).

## Directory Structure & Ownership

```
package-compliance-checker/
├── README.md                              # Project overview, who owns what, how to run end-to-end
├── .gitignore
├── .github/
│   └── workflows/
│       ├── test-ocr.yml                   # CI for ocr_module only
│       └── test-rag.yml                   # CI for legal_metrology_rag only
│
├── shared/                                 # ★ THE CONTRACT — both agree early, edit rarely
│   ├── schemas/
│   │   ├── ocr_output.schema.json          # text, bbox, confidence, layout
│   │   ├── field_extraction.schema.json    # field, value, bbox, confidence, commodity_type
│   │   ├── compliance_check.schema.json    # structured check query format
│   │   └── evidence_output.schema.json     # RAG's returned evidence + citation format
│   ├── sample_data/
│   │   ├── sample_ocr_output.json
│   │   ├── sample_field_extraction_output.json
│   │   └── sample_compliance_check.json
│   └── constants.py                        # PASS/FAIL/UNCERTAIN/NOT_APPLICABLE, domain names, etc.
│
├── ocr_module/                             # ★ OCR & FIELD EXTRACTION MODULE
│   ├── ocr/                                # text_detector.py, confidence_scorer.py
│   ├── layout/                             # layout_analyzer.py
│   ├── field_extraction/                   # field_mapper.py, field_rules.py, commodity_classifier.py
│   ├── tests/
│   ├── requirements.txt
│   └── README.md
│
├── legal_metrology_rag/                    # ★ MULTI-DOMAIN RAG MODULE
│   ├── rag_core/                           # SHARED ENGINE — used by all domain RAGs
│   │   ├── ingestion/                      # pdf_loader, text_extractor, structure_parser, metadata_extractor
│   │   ├── chunking/                       # legal_chunker, hierarchy
│   │   ├── embeddings/                     # embedder, model_config
│   │   ├── retrieval/                      # vector, keyword, hybrid_retriever, reranker
│   │   ├── database/                       # vector_store (add, search, delete), metadata_store
│   │   ├── evidence/                       # evidence_builder, citation
│   │   └── base_rag.py                     # BaseComplianceRAG abstract base class
│   ├── domains/
│   │   ├── legal_metrology/                # Legal Metrology domain RAG (LegalMetrologyRAG)
│   │   └── fssai/                          # FSSAI Food Safety domain RAG (FSSAIRAG)
│   ├── dispatcher/
│   │   └── domain_router.py                # Routes queries (always legal_metrology; if food -> also fssai)
│   ├── evaluation/                         # Benchmarks & retrieval/citation evaluators
│   ├── tests/                              # Integration tests across rag_core + domains
│   ├── config.yaml
│   ├── requirements.txt
│   ├── main.py
│   └── README.md
│
├── compliance_engine/                      # ★ COMPLIANCE DECISION ENGINE (Stub)
│   ├── engine.py                           # Field Extraction output + RAG evidence -> PASS/FAIL/UNCERTAIN
│   ├── tests/
│   └── README.md                           # Marked "not yet implemented"
│
└── integration/
    ├── end_to_end_test.py                  # Full pipeline: OCR -> Dispatcher -> RAG(s) -> Engine
    └── README.md
```

## Running Tests

```bash
python -m pytest shared/ ocr_module/ legal_metrology_rag/ compliance_engine/ integration/
```
