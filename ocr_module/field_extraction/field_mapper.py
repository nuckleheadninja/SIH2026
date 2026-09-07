import re
from typing import Dict, Any, List, Optional
from shared.constants import CommodityType
from .commodity_classifier import CommodityClassifier
from .field_rules import FieldRules


class FieldMapper:
    """
    Transforms raw OCR blocks into structured regulatory entities conforming to
    shared/schemas/field_extraction.schema.json.
    
    Includes fuzzy ingredients parsing, allergen isolation, and INS additive tagging.
    """

    def __init__(self):
        self.classifier = CommodityClassifier()

    def extract_fields(self, ocr_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extracts regulatory compliance fields from ocr_data (or list of blocks).
        Returns schema-compliant dictionary.
        """
        if isinstance(ocr_data, list):
            blocks = ocr_data
            image_id = "unknown_image"
        elif isinstance(ocr_data, dict):
            blocks = ocr_data.get("text_blocks") or ocr_data.get("ocr_blocks") or ocr_data.get("blocks", [])
            image_id = ocr_data.get("image_id", "pkg_scan")
        else:
            blocks = []
            image_id = "unknown_image"

        commodity_type = self.classifier.classify(blocks)
        extracted_fields: List[Dict[str, Any]] = []
        found_fields = set()

        # Concatenate text to extract multi-line sections like ingredients
        full_text_lines = [b.get("text", "") for b in blocks]
        full_document_text = "\n".join(full_text_lines)

        # 1. Line-by-line single field extraction
        for block in blocks:
            text = block.get("text", "")
            conf = float(block.get("confidence", 0.90))
            bbox = block.get("bbox", [0, 0, 100, 20])

            # MRP
            if "mrp" not in found_fields:
                mrp_res = FieldRules.parse_mrp(text)
                if mrp_res:
                    extracted_fields.append({
                        "field_name": "mrp",
                        "raw_text": mrp_res["raw_text"],
                        "normalized_value": str(mrp_res["normalized_value"]),
                        "unit": mrp_res["unit"],
                        "confidence": conf,
                        "bbox": bbox
                    })
                    found_fields.add("mrp")

            # Net Quantity
            if "net_quantity" not in found_fields:
                qty_res = FieldRules.parse_net_qty(text)
                if qty_res:
                    extracted_fields.append({
                        "field_name": "net_quantity",
                        "raw_text": qty_res["raw_text"],
                        "normalized_value": str(qty_res["normalized_value"]),
                        "unit": qty_res["unit"],
                        "confidence": conf,
                        "bbox": bbox
                    })
                    found_fields.add("net_quantity")

            # FSSAI
            if "fssai_license" not in found_fields:
                fssai_res = FieldRules.parse_fssai(text)
                if fssai_res:
                    extracted_fields.append({
                        "field_name": "fssai_license",
                        "raw_text": fssai_res["raw_text"],
                        "normalized_value": str(fssai_res["normalized_value"]),
                        "unit": None,
                        "confidence": conf,
                        "bbox": bbox
                    })
                    found_fields.add("fssai_license")

            # Batch Number
            if "batch_number" not in found_fields:
                batch_res = FieldRules.parse_batch(text)
                if batch_res:
                    extracted_fields.append({
                        "field_name": "batch_number",
                        "raw_text": batch_res["raw_text"],
                        "normalized_value": str(batch_res["normalized_value"]),
                        "unit": None,
                        "confidence": conf,
                        "bbox": bbox
                    })
                    found_fields.add("batch_number")

            # Dates
            date_res = FieldRules.parse_dates(text)
            if date_res["mfg_date"] and "mfg_date" not in found_fields:
                extracted_fields.append({
                    "field_name": "mfg_date",
                    "raw_text": date_res["mfg_date"]["raw_text"],
                    "normalized_value": str(date_res["mfg_date"]["normalized_value"]),
                    "unit": None,
                    "confidence": conf,
                    "bbox": bbox
                })
                found_fields.add("mfg_date")

            if date_res["expiry_date"] and "expiry_date" not in found_fields:
                extracted_fields.append({
                    "field_name": "expiry_date",
                    "raw_text": date_res["expiry_date"]["raw_text"],
                    "normalized_value": str(date_res["expiry_date"]["normalized_value"]),
                    "unit": None,
                    "confidence": conf,
                    "bbox": bbox
                })
                found_fields.add("expiry_date")

        # 2. Ingredients, Allergens & INS Additives Extraction (Fuzzy Header matching)
        ing_data = self._extract_ingredients(full_document_text, blocks)
        if ing_data:
            extracted_fields.append({
                "field_name": "ingredients",
                "raw_text": ing_data["raw_text"],
                "normalized_value": ", ".join(ing_data["items"]),
                "unit": None,
                "confidence": ing_data["confidence"],
                "bbox": ing_data["bbox"]
            })

            if ing_data.get("allergens"):
                extracted_fields.append({
                    "field_name": "allergens",
                    "raw_text": ", ".join(ing_data["allergens"]),
                    "normalized_value": ", ".join(ing_data["allergens"]),
                    "unit": None,
                    "confidence": ing_data["confidence"],
                    "bbox": ing_data["bbox"]
                })

            if ing_data.get("ins_additives"):
                extracted_fields.append({
                    "field_name": "ins_additives",
                    "raw_text": ", ".join(ing_data["ins_additives"]),
                    "normalized_value": ", ".join(ing_data["ins_additives"]),
                    "unit": None,
                    "confidence": ing_data["confidence"],
                    "bbox": ing_data["bbox"]
                })

        return {
            "image_id": image_id,
            "commodity_type": commodity_type,
            "extracted_fields": extracted_fields
        }

    def _extract_ingredients(self, doc_text: str, blocks: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Fuzzy header detection for degraded packaging (e.g. 'NGREDETEES', 'INGREDIENTS:').
        Strips nutrition table values and isolates allergens/INS codes.
        """
        # Fuzzy header regex
        ing_header_pattern = re.compile(r"(?:[in1l][ng]{1,2}r[e3]d[ie1][e3]n?t[es]{1,3}|ingredients?)\s*[:\-\.]?", re.IGNORECASE)
        match = ing_header_pattern.search(doc_text)
        if not match:
            return None

        start_pos = match.end()
        candidate = doc_text[start_pos:]

        # Terminate when nutrition table, instructions, or storage conditions begin
        stop_pattern = re.compile(
            r"(?:nutritio\w*|typical\s*values|serving\s*size|good\s*to\s*know|how\s*to\s*prepare|cook\s*any\s*dish|mfg|mrp|packed\s*by|marketed\s*by|storage|keep\s*in\s*a\s*cool|tastes\s*best)",
            re.IGNORECASE
        )
        stop_match = stop_pattern.search(candidate)
        raw_ing_text = candidate[:stop_match.start()].strip() if stop_match else candidate[:600].strip()

        # Find corresponding bounding box and confidence from matching blocks
        bbox = [0, 0, 500, 100]
        conf = 0.90
        for b in blocks:
            if ing_header_pattern.search(b.get("text", "")):
                bbox = b.get("bbox", bbox)
                conf = float(b.get("confidence", conf))
                break

        # Extract INS codes
        ins_codes = []
        for m in FieldRules.INS_PATTERN.finditer(raw_ing_text):
            code = f"INS {m.group(1)}"
            if code not in ins_codes:
                ins_codes.append(code)

        # Extract allergens
        allergens = []
        lower_raw = raw_ing_text.lower()
        for allergen in FieldRules.KNOWN_ALLERGENS:
            if re.search(rf"\b{allergen}\b", lower_raw):
                allergens.append(allergen.capitalize())

        # Clean individual ingredient items
        clean_text = re.sub(r"^[^\w]+", "", raw_ing_text)
        
        # Protect punctuation inside parentheses
        def _protect_parens(text: str) -> str:
            depth = 0
            chars = []
            for ch in text:
                if ch == "(":
                    depth += 1
                elif ch == ")":
                    depth = max(0, depth - 1)
                if depth > 0:
                    if ch == ",":
                        chars.append("§COMMA§")
                    elif ch == ";":
                        chars.append("§SEMI§")
                    elif ch == ".":
                        chars.append("§DOT§")
                    else:
                        chars.append(ch)
                else:
                    chars.append(ch)
            return "".join(chars)

        protected = _protect_parens(clean_text)
        raw_items = re.split(r"[,;•\n\r]+|\.(?=\s*[A-Z])|\s{2,}", protected)
        cleaned_items = []
        for item in raw_items:
            item_clean = (
                item.replace("§COMMA§", ",")
                .replace("§SEMI§", ";")
                .replace("§DOT§", ".")
                .strip(" .;:\"'-_")
            )
            if item_clean.startswith("(") and item_clean.endswith(")"):
                item_clean = item_clean[1:-1].strip()
            # Strip noise words like "Allergen Note:", numbers, etc.
            item_clean = re.sub(r"^(?:allergen\s*note:?|may\s*contain|contains:?)\s*", "", item_clean, flags=re.IGNORECASE).strip()
            if len(item_clean) >= 3 and not re.match(r"^\d+$", item_clean):
                cleaned_items.append(item_clean)

        return {
            "raw_text": raw_ing_text,
            "items": cleaned_items,
            "allergens": allergens,
            "ins_additives": ins_codes,
            "bbox": bbox,
            "confidence": conf
        }
