"""Flask API Server for Legal Metrology & FSSAI OCR Layout Analysis Dashboard."""
import os
import sys
import time
import re
import json
import logging
import traceback
from flask import Flask, request, jsonify, send_from_directory
from main import process_image, load_config
from utils.create_sample_label import generate_sample_label

app = Flask(__name__, static_folder="static")
CONFIG = load_config("config.yaml")

# Ensure required directories exist
os.makedirs("input", exist_ok=True)
os.makedirs("output", exist_ok=True)
os.makedirs("static", exist_ok=True)

@app.errorhandler(Exception)
def handle_global_error(e):
    """Global exception handler ensuring API always returns JSON errors."""
    logging.error(f"Unhandled Exception: {e}\n{traceback.format_exc()}")
    return jsonify({
        "status": "failed",
        "error_code": "SERVER_ERROR",
        "message": str(e)
    }), 500

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/static/<path:filename>")
def serve_static(filename):
    return send_from_directory("static", filename)

@app.route("/output/<path:filename>")
def serve_output(filename):
    return send_from_directory("output", filename)

@app.route("/input/<path:filename>")
def serve_input(filename):
    return send_from_directory("input", filename)

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "module": "OCR & Layout Analysis"})

@app.route("/api/analyze", methods=["POST"])
def analyze():
    if "file" not in request.files:
        return jsonify({"status": "failed", "error_code": "NO_FILE", "message": "No image file provided"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"status": "failed", "error_code": "EMPTY_FILENAME", "message": "Selected file has no filename"}), 400

    try:
        # Sanitize filename and generate unique timestamped stem to avoid path encoding issues
        raw_name = os.path.basename(file.filename)
        ext = os.path.splitext(raw_name)[1].lower()
        if not ext:
            ext = ".jpg"
        
        clean_stem = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in os.path.splitext(raw_name)[0]).strip("_")
        if not clean_stem:
            clean_stem = "custom_product"

        timestamp = int(time.time() * 1000)
        document_id = f"{clean_stem}_{timestamp}"
        unique_filename = f"{document_id}{ext}"
        
        save_path = os.path.join("input", unique_filename)
        file.save(save_path)

        # Process image through OCR & Layout pipeline
        result = process_image(save_path, CONFIG, document_id=document_id)

        # Attach relative URLs for frontend display
        if result.get("status") == "success":
            result["artifacts"] = {
                "original_image_url": f"/input/{unique_filename}",
                "annotated_image_url": f"/output/{document_id}/annotated.jpg",
                "preprocessed_image_url": f"/output/{document_id}/preprocessed.jpg",
                "json_url": f"/output/{document_id}/ocr_result.json"
            }

        return jsonify(result)
    except Exception as e:
        return jsonify({"status": "failed", "error_code": "PROCESSING_ERROR", "message": str(e)}), 500

@app.route("/api/sample", methods=["POST"])
def analyze_sample():
    sample_name = request.json.get("sample", "product_001.jpg") if request.is_json else "product_001.jpg"
    sample_path = os.path.join("input", sample_name)

    if not os.path.exists(sample_path):
        generate_sample_label(sample_path)

    stem = os.path.splitext(sample_name)[0]
    result = process_image(sample_path, CONFIG, document_id=stem)

    if result.get("status") == "success":
        result["artifacts"] = {
            "original_image_url": f"/input/{sample_name}",
            "annotated_image_url": f"/output/{stem}/annotated.jpg",
            "preprocessed_image_url": f"/output/{stem}/preprocessed.jpg",
            "json_url": f"/output/{stem}/ocr_result.json"
        }

    return jsonify(result)

if __name__ == "__main__":
    host = "127.0.0.1"
    port = 8000
    print(f"\n=======================================================")
    print(f"AI Legal Metrology Dashboard running at: http://{host}:{port}")
    print(f"=======================================================\n")
    app.run(host=host, port=port, debug=False)
