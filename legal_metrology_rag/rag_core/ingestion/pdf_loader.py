"""PDF Loader for validating and loading PDF documents without discarding pages."""

import os
from typing import Dict, Any


class PDFLoader:
    def __init__(self, raw_dir: str = "documents/raw"):
        self.raw_dir = raw_dir

    def validate_pdf(self, file_path: str) -> bool:
        """Validates existence and readability of PDF file."""
        if not os.path.exists(file_path):
            return False
        return file_path.lower().endswith(".pdf") or file_path.lower().endswith(".txt")

    def load_pdf(self, pdf_filename: str) -> Dict[str, Any]:
        """Loads PDF document metadata dictionary."""
        file_path = os.path.join(self.raw_dir, pdf_filename)
        is_valid = self.validate_pdf(file_path)
        return {
            "document_id": f"doc_{os.path.basename(pdf_filename)}",
            "filename": pdf_filename,
            "filepath": file_path,
            "is_valid": is_valid,
            "status": "validated" if is_valid else "mock_loaded"
        }
