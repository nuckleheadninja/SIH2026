# Legal Metrology RAG Module (SIH Problem Statement 26034)

## Overview
This module is a contract-driven, non-chatbot **Legal Metrology RAG System** for pre-packaged commodity compliance in India (Legal Metrology Act, 2009 & Legal Metrology Packaged Commodities Rules, 2011).

It receives structured compliance checks (`check_id`, `field`, `commodity_type`, `query_terms`) and returns structured legal evidence with exact statutory citations.

---

## Directory Architecture

```
legal_metrology_rag/
├── rag_core/                     # Generic domain-agnostic RAG engine
│   ├── ingestion/                # pdf_loader, text_extractor, structure_parser, metadata_extractor
│   ├── chunking/                 # legal_chunker (structure-aware), hierarchy
│   ├── embeddings/               # embedder, model_config
│   ├── retrieval/                # vector_retriever, keyword_retriever (BM25), hybrid_retriever, reranker
│   ├── database/                 # vector_store (add_documents, search, delete), metadata_store
│   ├── evidence/                 # evidence_builder, citation
│   └── base_rag.py               # BaseComplianceRAG abstract base class
├── domains/
│   └── legal_metrology/          # Legal Metrology domain specialization
│       ├── documents/            # raw/, processed/, metadata/
│       ├── catalogue/            # compliance_rules.json, rule_builder, validator
│       ├── query/                # query_builder, check_mapper
│       ├── config.yaml           # domain settings (collection_name: "legal_metrology")
│       ├── rag.py                # LegalMetrologyRAG(BaseComplianceRAG)
│       └── tests/
├── evaluation/                   # Benchmark test questions, retrieval_eval.py, citation_eval.py
├── tests/                        # Comprehensive test suite
├── config.yaml                   # Global defaults
├── requirements.txt
├── main.py                       # CLI runner & demo entry point
└── README.md
```

---

## Guide & Operations

### 1. How to Add Documents
Place raw PDF or text files of Legal Metrology Acts, Rules, or Gazettes in:
`legal_metrology_rag/domains/legal_metrology/documents/raw/`

Example file naming:
`Legal_Metrology_Packaged_Commodities_Rules_2011.pdf`

### 2. How to Rebuild Index
Run `LegalMetrologyRAG.load_documents()` or re-initialize `LegalMetrologyRAG()`:
```python
from legal_metrology_rag.domains.legal_metrology.rag import LegalMetrologyRAG

rag = LegalMetrologyRAG()
rag.load_documents("legal_metrology_rag/domains/legal_metrology/documents/raw")
```

### 3. How to Add or Update Compliance Checks
Edit `legal_metrology_rag/domains/legal_metrology/catalogue/compliance_rules.json` to add new checks:
```json
{
  "check_id": "LM_NEW_001",
  "domain": "legal_metrology",
  "requirement_name": "New Mandatory Declaration Check",
  "check_type": "presence",
  "applies_to": "pre_packaged_commodity",
  "required_observations": ["new_field_text"],
  "query_terms": ["new_field", "declaration"],
  "legal_sources": [
    {
      "document": "Legal Metrology (Packaged Commodities) Rules, 2011",
      "rule": "Rule X",
      "sub_rule": "sub-rule (1)",
      "clause": "clause (a)",
      "schedule": null,
      "page": 15
    }
  ]
}
```

### 4. How to Run Retrieval
Execute via CLI using `main.py`:
```bash
python legal_metrology_rag/main.py
```
Or via Python API:
```python
from legal_metrology_rag.domains.legal_metrology.rag import LegalMetrologyRAG

rag = LegalMetrologyRAG()
query = {
    "check_id": "LM_MRP_001",
    "domain": "legal_metrology",
    "commodity_type": "pre_packaged_commodity",
    "field": "mrp",
    "query_terms": ["MRP", "maximum retail price", "inclusive of all taxes"]
}
evidence = rag.query_compliance(query)
print(evidence)
```

### 5. How to Inspect Citations
The returned evidence dictionary contains a strict `citation` object:
```json
{
  "check_id": "LM_MRP_001",
  "chunk_id": "chk_lm_002",
  "document": "Legal Metrology (Packaged Commodities) Rules, 2011",
  "rule": "Rule 6",
  "sub_rule": "sub-rule (1)",
  "clause": "clause (f)",
  "schedule": null,
  "page": 12,
  "text": "Rule 6(1)(f) The maximum retail price at which the package may be sold...",
  "retrieval_score": 0.94,
  "citation": {
    "document": "Legal Metrology (Packaged Commodities) Rules, 2011",
    "rule": "Rule 6",
    "sub_rule": "sub-rule (1)",
    "clause": "clause (f)",
    "schedule": null,
    "page": 12
  }
}
```

### 6. How to Evaluate Retrieval Benchmark
Run evaluation runner via CLI:
```bash
python legal_metrology_rag/main.py --eval
```
Or execute `pytest`:
```bash
python -m pytest legal_metrology_rag/tests/
```
