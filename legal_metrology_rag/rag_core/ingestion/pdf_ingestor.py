"""PDFIngestor for page-by-page text extraction, printed page mapping, strikethrough/repeal detection, and structured GSR amendment annotation parsing."""

import os
import re
import pdfplumber
from typing import List, Dict, Any


class PDFIngestor:
    """Extracts pages, printed page numbers, inline annotations, and amendment footnotes from consolidated Legal Metrology PDFs."""

    GSR_PATTERN = re.compile(
        r"(?i)(?P<prefix>[\*\#\d\$\@]+)?\s*(?P<action>Substituted|amended|Omitted|Inserted|Replaced)?(?:\s*/\s*amended)?\s*vide\s*(?:G\.?S\.?R\.?|GSR)?\s*(?P<gsr>[\d\w\(\)]+)\s*(?:dated\s*)?(?P<date>[0-9a-zA-Z\s,]+?)(?:(?:\,\s*|(?:\s*came\s*into\s*force\s*)?)w\.?e\.?f\.?\s*(?P<wef>[0-9\.\/a-zA-Z]+(?:\s*\(now\s*w\.e\.f\s*[0-9\.\/a-zA-Z\s\(\)E\d\.\,]+)?))?",
        re.IGNORECASE
    )

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path

    def extract_pages_and_annotations(self) -> List[Dict[str, Any]]:
        """Extracts page-by-page text, printed page numbers, and structured amendment annotations."""
        if not os.path.exists(self.pdf_path):
            raise FileNotFoundError(f"PDF file not found at path: {self.pdf_path}")

        extracted_pages = []

        with pdfplumber.open(self.pdf_path) as pdf:
            for pdf_page_idx, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                lines = [line.strip() for line in text.split("\n") if line.strip()]

                # Determine printed page number from page text footer/header
                printed_page = self._detect_printed_page(lines, pdf_page_idx)

                # Extract amendment footnotes and GSR annotations
                annotations = self._extract_amendments_from_lines(lines, printed_page)

                # Detect omitted or repealed text passages
                omitted_passages = [line for line in lines if "omitted" in line.lower() or "repealed" in line.lower()]

                extracted_pages.append({
                    "pdf_page_index": pdf_page_idx,
                    "printed_page": printed_page,
                    "page_text": text,
                    "lines": lines,
                    "annotations": annotations,
                    "omitted_passages": omitted_passages
                })

        return extracted_pages

    def _detect_printed_page(self, lines: List[str], pdf_page_idx: int) -> int:
        """Detects the printed page number at top/bottom of page, defaulting to offset formula."""
        if lines:
            # Check last line for standalone page number
            last_line = lines[-1].strip()
            if last_line.isdigit():
                return int(last_line)
            # Check first line for standalone page number
            first_line = lines[0].strip()
            if first_line.isdigit():
                return int(first_line)

        # Fallback mapping: Page 6 of PDF corresponds to Printed Page 5/6
        return max(1, pdf_page_idx - 1)

    def _extract_amendments_from_lines(self, lines: List[str], printed_page: int) -> List[Dict[str, Any]]:
        """Parses lines for GSR amendment notification footnotes."""
        annotations = []
        full_page_str = "\n".join(lines)

        for line in lines:
            if "vide" in line.lower() or "gsr" in line.lower() or "substituted" in line.lower() or "omitted" in line.lower():
                match = self.GSR_PATTERN.search(line)
                if match:
                    action = match.group("action") or ("Omitted" if "omitted" in line.lower() else "Substituted/Amended")
                    gsr = match.group("gsr") or "Unknown GSR"
                    date_str = match.group("date").strip() if match.group("date") else None
                    wef_str = match.group("wef").strip() if match.group("wef") else None

                    annotations.append({
                        "raw_annotation": line,
                        "action": action.strip(),
                        "gsr_number": f"GSR {gsr}".strip(),
                        "date": date_str,
                        "effective_from": wef_str,
                        "printed_page": printed_page
                    })

        return annotations
