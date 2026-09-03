"""Main CLI entrypoint for AI-Based Legal Metrology & FSSAI OCR + Layout Analysis Module."""
import os
import sys
import time
import json
import yaml
import argparse
from typing import Dict, Any, List

from models.image_schema import QualityReport, ImageMetadata
from models.ocr_schema import (
    OCRResultModel,
    OCRBlockModel,
    PreprocessingInfoModel,
    OCREngineInfoModel,
    ErrorResponseModel
)
from preprocessing.validation import validate_image
from preprocessing.pipeline import PreprocessingPipeline
from ocr.paddle_engine import PaddleOCREngine
from ocr.easyocr_engine import EasyOCREngine
from ocr.postprocessor import ConservativePostProcessor
from layout.geometry import compute_geometry, compute_orientation, compute_visual_metrics
from layout.region import create_layout_model
from layout.analyzer import LayoutAnalyzer
from utils.image_utils import save_image
from utils.visualization import draw_ocr_visualization
from utils.logging_utils import setup_logger

logger = setup_logger("OCR_Pipeline")

def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    if not os.path.exists(config_path):
        logger.warning(f"Config file '{config_path}' not found. Using defaults.")
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def process_image(image_path: str, config: Dict[str, Any], document_id: str = None, pass_name: str = "primary") -> Dict[str, Any]:
    start_time = time.time()
    stem = os.path.splitext(os.path.basename(image_path))[0]
    doc_id = document_id or stem

    logger.info(f"--- Starting OCR & Layout Analysis for: {image_path} ---")

    # Step 1: Image Validation
    try:
        _, metadata, quality_report, raw_image = validate_image(image_path)
        logger.info(f"Image loaded: {metadata.width}x{metadata.height} | Quality status: {quality_report.quality_status}")
        for w in quality_report.warnings:
            logger.warning(f"Quality Warning: {w}")
    except Exception as e:
        logger.error(f"Image validation failed for {image_path}: {e}")
        err = ErrorResponseModel(
            status="failed",
            error_code="INVALID_IMAGE",
            message=str(e),
            document_id=doc_id
        )
        return err.model_dump()

    # Step 2: Preprocessing
    pipeline = PreprocessingPipeline(config)
    preprocessed_img, profile_used, applied_ops = pipeline.process(raw_image, quality_report)
    logger.info(f"Preprocessing profile: '{profile_used}' | Applied ops: {applied_ops}")

    # Step 3: OCR Engine Execution
    ocr_config = config.get("ocr", {})
    engine_choice = ocr_config.get("engine", "paddleocr").lower()
    use_gpu = ocr_config.get("use_gpu", False)
    lang = ocr_config.get("language", "en")

    if engine_choice == "easyocr":
        engine = EasyOCREngine(use_gpu=use_gpu, lang=lang)
    else:
        engine = PaddleOCREngine(use_gpu=use_gpu, lang=lang)

    logger.info(f"Executing OCR engine: {engine.engine_name} v{engine.engine_version}")
    raw_detections = engine.detect_text(preprocessed_img)

    if not raw_detections:
        logger.warning("No text detected by OCR engine.")

    # Step 4-11: Postprocessing, Geometry, Layout, Orientation, Sizing
    high_thresh = ocr_config.get("high_confidence_threshold", 0.90)
    med_thresh = ocr_config.get("medium_confidence_threshold", 0.70)

    ocr_blocks: List[OCRBlockModel] = []
    total_conf = 0.0
    low_conf_count = 0

    for idx, det in enumerate(raw_detections, start=1):
        block_id = f"ocr_{idx:03d}"

        # 4. Conservative Text Normalization
        norm_text = ConservativePostProcessor.normalize(det.raw_text)

        # Confidence level assignment
        if det.confidence >= high_thresh:
            conf_level = "high"
        elif det.confidence >= med_thresh:
            conf_level = "medium"
        else:
            conf_level = "low"
            low_conf_count += 1

        total_conf += det.confidence

        # 5-6. Geometry & Orientation
        geom = compute_geometry(det.bbox)
        orient = compute_orientation(det.polygon)
        visual = compute_visual_metrics(geom.height_px)

        # 7-8. Relative coordinates & 3x3 Grid Region
        layout_mod = create_layout_model(
            center_x=geom.center_x,
            center_y=geom.center_y,
            image_width=metadata.width,
            image_height=metadata.height
        )

        block = OCRBlockModel(
            id=block_id,
            raw_text=det.raw_text,
            normalized_text=norm_text,
            confidence=round(det.confidence, 4),
            confidence_level=conf_level,
            polygon=det.polygon,
            bbox=det.bbox,
            geometry=geom,
            layout=layout_mod,
            orientation=orient,
            visual=visual,
            reading_order=idx
        )
        ocr_blocks.append(block)

    # Step 11-12: Reading Order Sorting & Pairwise Spatial Relationships
    analyzer = LayoutAnalyzer(distance_threshold_px=config.get("layout", {}).get("spatial_relation_distance_threshold", 150))
    ocr_blocks = analyzer.sort_reading_order(ocr_blocks)
    spatial_relations = analyzer.compute_spatial_relationships(ocr_blocks)

    # Build Structured Output Result Model
    preprocessing_info = PreprocessingInfoModel(
        profile=profile_used,
        operations=applied_ops
    )

    ocr_engine_info = OCREngineInfoModel(
        name=engine.engine_name,
        version=engine.engine_version,
        device="gpu" if use_gpu else "cpu"
    )

    result = OCRResultModel(
        document_id=doc_id,
        status="success",
        image=metadata,
        quality=quality_report,
        preprocessing=preprocessing_info,
        ocr_engine=ocr_engine_info,
        ocr_blocks=ocr_blocks,
        spatial_relations=spatial_relations,
        ocr_pass=pass_name
    )

    elapsed = round(time.time() - start_time, 2)
    avg_conf = round(total_conf / max(1, len(ocr_blocks)), 4)
    logger.info(f"Processed {len(ocr_blocks)} OCR blocks | Avg confidence: {avg_conf} | Low conf blocks: {low_conf_count} | Time: {elapsed}s")

    # Step 21: Output Artifact Generation
    out_dir = config.get("output", {}).get("output_dir", "output")
    doc_out_dir = os.path.join(out_dir, doc_id)
    os.makedirs(doc_out_dir, exist_ok=True)

    # 1. JSON result export
    json_path = os.path.join(doc_out_dir, "ocr_result.json")
    result_dict = result.model_dump()

    # Extract Key Legal Metrology & FSSAI Product Fields
    from extractor.field_extractor import ProductFieldExtractor
    field_extractor = ProductFieldExtractor()
    result_dict["extracted_fields"] = field_extractor.extract_fields(result_dict.get("ocr_blocks", []))

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result_dict, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved OCR result JSON to: {json_path}")

    # 2. Annotated image export
    if config.get("output", {}).get("save_annotated_image", True):
        annotated_img = draw_ocr_visualization(raw_image, ocr_blocks, config)
        annotated_path = os.path.join(doc_out_dir, "annotated.jpg")
        save_image(annotated_img, annotated_path)
        logger.info(f"Saved annotated image to: {annotated_path}")

    # 3. Preprocessed image export
    if config.get("output", {}).get("save_preprocessed_image", True):
        prep_path = os.path.join(doc_out_dir, "preprocessed.jpg")
        save_image(preprocessed_img, prep_path)
        logger.info(f"Saved preprocessed image to: {prep_path}")

    return result_dict

def main():
    parser = argparse.ArgumentParser(description="AI Legal Metrology & FSSAI Compliance - OCR & Layout Analysis Module")
    parser.add_argument("--input", type=str, default="input/product_001.jpg", help="Path to input image or directory")
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to config yaml")
    parser.add_argument("--multi-pass", action="store_true", help="Enable multi-pass OCR pass on enhanced image")
    args = parser.parse_args()

    config = load_config(args.config)

    # If input is a synthetic file that doesn't exist, create synthetic sample image
    if not os.path.exists(args.input) and args.input == "input/product_001.jpg":
        from utils.create_sample_label import generate_sample_label
        generate_sample_label(args.input)

    if os.path.isdir(args.input):
        files = [os.path.join(args.input, f) for f in os.listdir(args.input) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
        for f in files:
            process_image(f, config)
    else:
        result = process_image(args.input, config)
        if args.multi_pass and result.get("status") == "success":
            logger.info("--- Executing Multi-Pass OCR Pass 2 ---")
            process_image(args.input, config, pass_name="enhanced_pass_2")

if __name__ == "__main__":
    main()
