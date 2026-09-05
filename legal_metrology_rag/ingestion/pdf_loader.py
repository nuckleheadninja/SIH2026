"""PDF Loader for loading raw legal metrology PDF files."""

import os
from typing import Dict, Any


class PDFLoader:
    def __init__(self, raw_dir: str = "documents/raw"):
        self.raw_dir = raw_dir

    def load_pdf(self, pdf_filename: str) -> Dict[str, Any]:
        """Loads PDF document and returns document metadata stub."""
        file_path = os.path.join(self.raw_dir, pdf_filename)
        return {
            "filename": pdf_filename,
            "filepath": file_path,
            "status": "loaded" if os.path.exists(file_path) else "mock_loaded"
        }
