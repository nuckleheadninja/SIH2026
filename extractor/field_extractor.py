"""Legal Metrology & FSSAI Product Detail Field Extractor.

Extracts structured key product fields (MRP, Net Qty, Mfg Date, Batch No, FSSAI Lic No, Brand Title)
from raw OCR evidence blocks using deterministic Regex pattern matching and spatial heuristics.
"""
import re
from typing import List, Dict, Any, Optional

class ProductFieldExtractor:
    def __init__(self):
        # Regex patterns for key Legal Metrology fields
        self.mrp_pattern = re.compile(
            r'(?:m\.?r\.?p\.?|max(?:imum)?\s*retail\s*price|price)\s*[:\.-]?\s*(?:₹|rs\.?|inr)?\s*([0-9]+(?:\.[0-9]{1,2})?)',
            re.IGNORECASE
        )
        self.currency_pattern = re.compile(r'(?:₹|rs\.?|inr)\s*([0-9]+(?:\.[0-9]{1,2})?)', re.IGNORECASE)
        
        self.net_qty_pattern = re.compile(
            r'(?:net\s*(?:qty|weight|wt|volume|vol|contents?))\s*[:\.-]?\s*([0-9]+(?:\.[0-9]+)?\s*(?:g|kg|ml|l|ltr|liter|litres|gm|grams|kgm|pcs|n))\b',
            re.IGNORECASE
        )
        self.standalone_qty_pattern = re.compile(
            r'\b([0-9]+(?:\.[0-9]+)?\s*(?:g|kg|ml|l|ltr|liter|gm|grams|pcs))\b',
            re.IGNORECASE
        )
        
        self.mfg_date_pattern = re.compile(
            r'(?:mfg|mfd|date\s*of\s*mfg|manufactured|pkd|packed)\s*[:\.-]?\s*([0-9]{1,2}[/\.-][0-9]{2,4}|[a-z]{3}[/\.-][0-9]{2,4})',
            re.IGNORECASE
        )
        self.exp_date_pattern = re.compile(
            r'(?:exp|expiry|use\s*by|best\s*before)\s*[:\.-]?\s*([0-9]{1,2}[/\.-][0-9]{2,4}|[a-z]{3}[/\.-][0-9]{2,4}|\d+\s*months?)',
            re.IGNORECASE
        )
        
        self.batch_pattern = re.compile(
            r'(?:batch|lot|b\.?\s*no|bno)\s*[:\.-]?\s*([a-z0-9\-_]+)',
            re.IGNORECASE
        )
        
        self.fssai_pattern = re.compile(
            r'(?:fssai|lic\.?\s*no\.?|license\s*no\.?)\s*[:\.-]?\s*([0-9]{14})\b',
            re.IGNORECASE
        )
        self.standalone_14digit = re.compile(r'\b([0-9]{14})\b')

    def extract_fields(self, ocr_blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Parses OCR blocks and extracts structured Legal Metrology fields.
        Returns a dictionary of key-value product details with source block evidence.
        """
        extracted = {
            "brand_title": {"value": None, "confidence": 0.0, "evidence_block_id": None},
            "mrp": {"value": None, "raw_text": None, "confidence": 0.0, "evidence_block_id": None},
            "net_quantity": {"value": None, "raw_text": None, "confidence": 0.0, "evidence_block_id": None},
            "mfg_date": {"value": None, "raw_text": None, "confidence": 0.0, "evidence_block_id": None},
            "expiry_date": {"value": None, "raw_text": None, "confidence": 0.0, "evidence_block_id": None},
            "batch_number": {"value": None, "raw_text": None, "confidence": 0.0, "evidence_block_id": None},
            "fssai_lic_no": {"value": None, "raw_text": None, "confidence": 0.0, "evidence_block_id": None},
        }

        if not ocr_blocks:
            return extracted

        # Sort blocks by font height / font size to find candidate Brand Title
        sorted_by_size = sorted(ocr_blocks, key=lambda b: b.get("visual", {}).get("font_height_px", 0), reverse=True)
        if sorted_by_size:
            top_block = sorted_by_size[0]
            extracted["brand_title"] = {
                "value": top_block.get("normalized_text", top_block.get("raw_text")),
                "confidence": top_block.get("confidence", 0.9),
                "evidence_block_id": top_block.get("id")
            }

        # Iterate through OCR blocks to match field patterns
        for block in ocr_blocks:
            text = block.get("normalized_text", block.get("raw_text", ""))
            raw = block.get("raw_text", text)
            block_id = block.get("id")
            conf = block.get("confidence", 0.9)

            # 1. MRP Extraction
            if not extracted["mrp"]["value"]:
                mrp_match = self.mrp_pattern.search(raw) or self.mrp_pattern.search(text)
                if mrp_match:
                    extracted["mrp"] = {
                        "value": f"₹ {mrp_match.group(1)}",
                        "raw_text": raw,
                        "confidence": conf,
                        "evidence_block_id": block_id
                    }
                elif "mrp" in text.lower() or "price" in text.lower() or "₹" in text:
                    curr_match = self.currency_pattern.search(raw)
                    if curr_match:
                        extracted["mrp"] = {
                            "value": f"₹ {curr_match.group(1)}",
                            "raw_text": raw,
                            "confidence": conf,
                            "evidence_block_id": block_id
                        }
                    else:
                        extracted["mrp"] = {
                            "value": raw,
                            "raw_text": raw,
                            "confidence": conf,
                            "evidence_block_id": block_id
                        }

            # 2. Net Quantity Extraction
            if not extracted["net_quantity"]["value"]:
                qty_match = self.net_qty_pattern.search(raw) or self.net_qty_pattern.search(text)
                if qty_match:
                    extracted["net_quantity"] = {
                        "value": qty_match.group(1),
                        "raw_text": raw,
                        "confidence": conf,
                        "evidence_block_id": block_id
                    }
                elif "net" in text.lower() or "qty" in text.lower() or "weight" in text.lower():
                    st_match = self.standalone_qty_pattern.search(raw)
                    if st_match:
                        extracted["net_quantity"] = {
                            "value": st_match.group(1),
                            "raw_text": raw,
                            "confidence": conf,
                            "evidence_block_id": block_id
                        }
                    else:
                        extracted["net_quantity"] = {
                            "value": raw,
                            "raw_text": raw,
                            "confidence": conf,
                            "evidence_block_id": block_id
                        }

            # 3. Mfg Date Extraction
            if not extracted["mfg_date"]["value"]:
                mfg_match = self.mfg_date_pattern.search(raw) or self.mfg_date_pattern.search(text)
                if mfg_match:
                    extracted["mfg_date"] = {
                        "value": mfg_match.group(1),
                        "raw_text": raw,
                        "confidence": conf,
                        "evidence_block_id": block_id
                    }
                elif "mfg" in text.lower() or "mfd" in text.lower() or "packed" in text.lower():
                    extracted["mfg_date"] = {
                        "value": raw,
                        "raw_text": raw,
                        "confidence": conf,
                        "evidence_block_id": block_id
                    }

            # 4. Expiry / Best Before Extraction
            if not extracted["expiry_date"]["value"]:
                exp_match = self.exp_date_pattern.search(raw) or self.exp_date_pattern.search(text)
                if exp_match:
                    extracted["expiry_date"] = {
                        "value": exp_match.group(1),
                        "raw_text": raw,
                        "confidence": conf,
                        "evidence_block_id": block_id
                    }

            # 5. Batch Number Extraction
            if not extracted["batch_number"]["value"]:
                batch_match = self.batch_pattern.search(raw) or self.batch_pattern.search(text)
                if batch_match:
                    extracted["batch_number"] = {
                        "value": batch_match.group(1),
                        "raw_text": raw,
                        "confidence": conf,
                        "evidence_block_id": block_id
                    }
                elif "batch" in text.lower() or "lot" in text.lower():
                    extracted["batch_number"] = {
                        "value": raw,
                        "raw_text": raw,
                        "confidence": conf,
                        "evidence_block_id": block_id
                    }

            # 6. FSSAI License Number Extraction
            if not extracted["fssai_lic_no"]["value"]:
                fssai_match = self.fssai_pattern.search(raw) or self.fssai_pattern.search(text)
                if fssai_match:
                    extracted["fssai_lic_no"] = {
                        "value": fssai_match.group(1),
                        "raw_text": raw,
                        "confidence": conf,
                        "evidence_block_id": block_id
                    }
                else:
                    digit14 = self.standalone_14digit.search(raw)
                    if digit14:
                        extracted["fssai_lic_no"] = {
                            "value": digit14.group(1),
                            "raw_text": raw,
                            "confidence": conf,
                            "evidence_block_id": block_id
                        }

        return extracted
