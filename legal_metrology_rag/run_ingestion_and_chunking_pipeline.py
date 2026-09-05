"""Pipeline script executing ingestion, chunking, schema enforcement, and 40-check ground-truth validation."""

import json
import os
from legal_metrology_rag.rag_core.ingestion.pdf_ingestor import PDFIngestor
from legal_metrology_rag.rag_core.chunking.legal_structure_chunker import LegalStructureChunker
from legal_metrology_rag.rag_core.chunking.metadata_enforcer import MetadataEnforcer
from legal_metrology_rag.evaluation.catalogue_validator import CatalogueValidator

PDF_PATH = r"C:\Users\User\Downloads\Book_on_Legal_Metrology_Packaged_Commodities_Rules,2011_with_all_amendments_whatsnews_1.pdf"
RULES_PATH = r"C:\Users\User\Downloads\compliance_rules.json"
OUTPUT_DIR = r"d:\SIH2026\legal_metrology_rag\outputs"


def run_pipeline():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"1. Extracting PDF pages and GSR annotations from {PDF_PATH}...")
    ingestor = PDFIngestor(PDF_PATH)
    extracted_pages = ingestor.extract_pages_and_annotations()

    pages_output_path = os.path.join(OUTPUT_DIR, "extracted_pages_with_annotations.json")
    with open(pages_output_path, "w", encoding="utf-8") as f:
        json.dump(extracted_pages, f, indent=2)
    print(f"   -> Saved page extraction output to {pages_output_path} ({len(extracted_pages)} pages).")

    print("\n2. Chunking text by legal structure (Chapter -> Rule -> Sub-rule -> Clause -> Schedule)...")
    chunker = LegalStructureChunker()
    raw_chunks = chunker.parse_document_into_chunks(extracted_pages)

    print("\n3. Enforcing Task 4 Metadata Schema attributes on chunks...")
    enforcer = MetadataEnforcer()
    sanitized_chunks = enforcer.enforce_schema_batch(raw_chunks)

    chunks_output_path = os.path.join(OUTPUT_DIR, "validated_legal_chunks.json")
    with open(chunks_output_path, "w", encoding="utf-8") as f:
        json.dump(sanitized_chunks, f, indent=2)
    print(f"   -> Saved legal chunks to {chunks_output_path} ({len(sanitized_chunks)} chunks).")

    print("\n4. Running mandatory Task 3 Validation against all 40 ground-truth check_ids in compliance_rules.json...")
    validator = CatalogueValidator(compliance_rules_path=RULES_PATH)
    report = validator.validate_chunks_against_catalogue(sanitized_chunks)

    report_json_path = os.path.join(OUTPUT_DIR, "validation_report.json")
    with open(report_json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    # Generate Markdown Report
    markdown_report_path = os.path.join(OUTPUT_DIR, "validation_report.md")
    with open(markdown_report_path, "w", encoding="utf-8") as f:
        f.write("# Task 3 Ground-Truth Validation Report\n\n")
        f.write(f"**Target PDF**: `{PDF_PATH}`  \n")
        f.write(f"**Ground-Truth Catalogue**: `{RULES_PATH}`  \n")
        f.write(f"**Total Compliance Checks**: {report['summary']['total_checks']}  \n")
        f.write(f"**Matched Checks**: {report['summary']['matched']}  \n")
        f.write(f"**Mismatch Checks**: {report['summary']['mismatch']}  \n")
        f.write(f"**Not Found Checks**: {report['summary']['not_found']}  \n")
        f.write(f"**Pass Rate**: {report['summary']['pass_rate'] * 100:.1f}%\n\n")

        f.write("## Detailed Check Validation Status\n\n")
        f.write("| Check ID | Status | Rule / Sub / Clause / Page | Matched Chunk ID | Consistency Reason |\n")
        f.write("| --- | --- | --- | --- | --- |\n")
        for item in report["details"]:
            cit = item["target_citation"]
            cit_str = f"Rule {cit['rule']}, Sub {cit['sub_rule']}, Clause {cit['clause']}, Pg {cit['page']}"
            f.write(f"| `{item['check_id']}` | **{item['status']}** | `{cit_str}` | `{item.get('matched_chunk_id') or 'N/A'}` | {item['reason']} |\n")

    print(f"   -> Saved JSON report to {report_json_path}")
    print(f"   -> Saved Markdown report to {markdown_report_path}")
    print(f"\nVALIDATION SUMMARY: {report['summary']['matched']}/{report['summary']['total_checks']} MATCHED (Pass Rate: {report['summary']['pass_rate']*100:.1f}%)")

    return report


if __name__ == "__main__":
    run_pipeline()
