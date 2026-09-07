"""
server.py — FastAPI Backend Server for SurakshaScan & SIH2026 Compliance Checker

Exposes /scan/upload endpoint for frontend Streamlit UI and REST clients.
Flow: Image -> Preprocessor -> PaddleOCR TextDetector -> LayoutAnalyzer -> FieldMapper 
      -> CheckMapper -> DomainRouter (Legal Metrology & FSSAI RAG) -> ComplianceEngine
"""

import sys
import uuid
import json
import logging
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Ensure repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ocr_module.ocr.preprocessor import PackagingPreprocessor
from ocr_module.ocr.text_detector import TextDetector
from ocr_module.layout.layout_analyzer import LayoutAnalyzer
from ocr_module.field_extraction.field_mapper import FieldMapper
from legal_metrology_rag.domains.legal_metrology.query.check_mapper import CheckMapper
from legal_metrology_rag.dispatcher.domain_router import DomainRouter
from compliance_engine.engine import ComplianceEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SurakshaScan-Server")

app = FastAPI(
    title="SurakshaScan Backend API",
    description="Automated Legal Metrology & Food Safety Compliance Engine API",
    version="1.0.0",
)

# Enable CORS for local Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lazy singletons for heavy models
_detector = None
_layout_analyzer = None
_field_mapper = None
_check_mapper = None
_domain_router = None
_compliance_engine = None

def get_pipeline():
    global _detector, _layout_analyzer, _field_mapper, _check_mapper, _domain_router, _compliance_engine
    if _detector is None:
        logger.info("Initializing OCR TextDetector...")
        _detector = TextDetector()
    if _layout_analyzer is None:
        _layout_analyzer = LayoutAnalyzer()
    if _field_mapper is None:
        _field_mapper = FieldMapper()
    if _check_mapper is None:
        _check_mapper = CheckMapper()
    if _domain_router is None:
        logger.info("Initializing DomainRouter & Legal RAG vector stores...")
        _domain_router = DomainRouter()
    if _compliance_engine is None:
        _compliance_engine = ComplianceEngine()
    
    return (
        _detector,
        _layout_analyzer,
        _field_mapper,
        _check_mapper,
        _domain_router,
        _compliance_engine,
    )


@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "SurakshaScan Legal Metrology Compliance Engine API",
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/scan/upload")
async def scan_upload(
    file: UploadFile = File(...),
    product_category: str = Form("General Food"),
    is_curved: str = Form("false"),
    use_hindi: str = Form("false"),
):
    scan_id = f"SCAN_{uuid.uuid4().hex[:8].upper()}"
    logger.info(f"Processing scan {scan_id}: file={file.filename}, category={product_category}")

    try:
        # 1. Read file bytes & decode CV2 image
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image file format")

        detector, layout_analyzer, field_mapper, check_mapper, domain_router, compliance_engine = get_pipeline()

        # 2. Preprocess if curved bottle/can
        is_curved_bool = is_curved.lower() in ["true", "1", "yes"]
        if is_curved_bool:
            preprocessor = PackagingPreprocessor()
            img = preprocessor.preprocess_cylindrical_dewarp(img)
            img = preprocessor.preprocess_clahe(img)

        # 3. Detect text blocks
        blocks = detector.detect_text(img)
        logger.info(f"Detected {len(blocks)} raw text blocks")

        # 4. Analyze layout
        blocks = layout_analyzer.analyze_layout(blocks)

        # 5. Map fields
        extracted_data = field_mapper.extract_fields(blocks)
        extracted_fields_list = extracted_data.get("extracted_fields", [])
        commodity_type = extracted_data.get("commodity_type", "general_commodity")

        # 6. Generate RAG compliance queries & query evidence
        queries = check_mapper.map_extracted_fields_to_queries(extracted_data)
        evidences = domain_router.dispatch_and_query(queries, commodity_type=commodity_type)

        # 7. Evaluate package compliance
        evaluation = compliance_engine.evaluate_package_compliance(extracted_fields_list, evidences)
        overall_status = evaluation.get("overall_status", "UNCERTAIN")
        is_compliant = overall_status == "PASS"

        # 8. Transform extracted fields into clean response dictionary for Streamlit frontend
        fields_by_name = {}
        for f in extracted_fields_list:
            fname = f.get("field_name")
            val = f.get("normalized_value") or f.get("raw_text")
            if fname == "net_quantity":
                fields_by_name[fname] = {"raw": f"{val} {f.get('unit', '')}".strip(), "value": val, "unit": f.get("unit")}
            else:
                fields_by_name[fname] = val

        # Missing mandatory fields check
        mandatory = ["mrp", "net_quantity", "mfg_date", "fssai_license", "manufacturer"]
        missing_fields = [m for m in mandatory if m not in fields_by_name or not fields_by_name[m]]

        # Construct compliance issues list for frontend display
        issues = []
        for fe in evaluation.get("field_evaluations", []):
            if fe.get("status") in ["FAIL", "UNCERTAIN"]:
                issues.append({
                    "severity": "critical" if fe.get("status") == "FAIL" else "warning",
                    "detail": fe.get("reason", "Field compliance check failed"),
                    "recommendation": f"Ensure {fe.get('field_name')} declaration is printed clearly as per Legal Metrology Rules.",
                    "regulation_id": fe.get("evidence", {}).get("relevant_rule", "Legal Metrology (Packaged Commodities) Rules, 2011"),
                })

        # Add missing field issue if any
        for mf in missing_fields:
            issues.append({
                "severity": "critical",
                "detail": f"Mandatory declaration field '{mf}' was not detected on the product label.",
                "recommendation": f"Add mandatory declaration '{mf}' in legible font size as mandated by Rule 6.",
                "regulation_id": "Legal Metrology Rule 6(1)",
            })

        response_payload = {
            "scan_id": scan_id,
            "ocr_detections_count": len(blocks),
            "extracted_data": {
                "mrp": fields_by_name.get("mrp"),
                "net_quantity": fields_by_name.get("net_quantity"),
                "mfg_date": fields_by_name.get("mfg_date"),
                "expiry_date": fields_by_name.get("expiry_date"),
                "fssai_license": fields_by_name.get("fssai_license"),
                "manufacturer": fields_by_name.get("manufacturer"),
                "country_of_origin": fields_by_name.get("country_of_origin"),
                "consumer_care": fields_by_name.get("consumer_care"),
                "allergens": extracted_data.get("allergens", []),
                "ingredients": extracted_data.get("ingredients", []),
                "additives": extracted_data.get("additives", []),
            },
            "missing_mandatory_fields": missing_fields,
            "compliance": {
                "is_compliant": is_compliant and len(missing_fields) == 0,
                "issues": issues,
                "overall_status": overall_status,
            },
            "rag_payload": {
                "commodity_type": commodity_type,
                "extracted_fields": extracted_fields_list,
                "evidences": evidences,
            },
        }

        return response_payload

    except Exception as e:
        logger.error(f"Error processing scan {scan_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
