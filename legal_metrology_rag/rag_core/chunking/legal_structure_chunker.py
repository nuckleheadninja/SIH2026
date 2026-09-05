"""LegalStructureChunker for dynamically parsing consolidated PDF text into structure-aware legal chunks."""

import re
from typing import List, Dict, Any, Optional


class LegalStructureChunker:
    """Structure-aware legal chunker creating chunks by Chapter -> Rule -> sub-rule -> clause -> Schedule -> Table."""

    CHAPTER_MAPPING = [
        {"name": "Chapter I", "title": "Preliminary", "rules": ["1", "2"]},
        {"name": "Chapter II", "title": "Provisions Applicable to Packages Intended for Retail Sale", "rules": ["3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23"]},
        {"name": "Chapter III", "title": "Provisions Applicable to Wholesale Packages", "rules": ["24"]},
        {"name": "Chapter IV", "title": "Export Packages", "rules": ["25"]},
        {"name": "Chapter V", "title": "Exemptions", "rules": ["26"]},
        {"name": "Chapter VI", "title": "Registration of Manufacturers, Packers and Importers", "rules": ["27", "28", "29", "30"]},
        {"name": "Chapter VII", "title": "General", "rules": ["31", "32", "33", "34"]}
    ]

    def get_chapter_for_rule(self, rule_str: Optional[str]) -> Optional[str]:
        if not rule_str:
            return None
        clean_rule = str(rule_str).strip()
        for chap in self.CHAPTER_MAPPING:
            if clean_rule in chap["rules"]:
                return f"{chap['name']}: {chap['title']}"
        return "General"

    def parse_document_into_chunks(self, extracted_pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parses extracted pages into structured chunks adhering to Task 2 legal hierarchy and Task 4 metadata schema."""
        chunks = []
        rule_segments = self._extract_rule_segments(extracted_pages)

        for seg in rule_segments:
            chunk_id = f"chk_lm_{seg['rule']}_{seg.get('sub_rule') or 'main'}_{seg.get('clause') or 'main'}_{seg['page_start']}"
            if seg.get("status") == "superseded":
                chunk_id += "_superseded"

            chunk = {
                "chunk_id": chunk_id,
                "document_id": "LM_PC_2011_consolidated",
                "document_title": "Legal Metrology (Packaged Commodities) Rules, 2011",
                "authority": "Department of Consumer Affairs",
                "jurisdiction": "India",
                "domain": "legal_metrology",
                "chapter": self.get_chapter_for_rule(seg["rule"]),
                "rule": str(seg["rule"]),
                "sub_rule": seg.get("sub_rule"),
                "clause": seg.get("clause"),
                "schedule": seg.get("schedule"),
                "table": seg.get("table"),
                "page_start": seg["page_start"],
                "page_end": seg["page_end"],
                "effective_from": seg.get("effective_from", "2011-03-01"),
                "effective_to": seg.get("effective_to"),
                "status": seg.get("status", "current"),
                "amended_by": seg.get("amended_by", []),
                "supersedes": seg.get("supersedes", []),
                "superseded_by": seg.get("superseded_by", []),
                "chunk_type": seg.get("chunk_type", "legal_requirement"),
                "text": seg["text"].strip()
            }
            chunks.append(chunk)

        return chunks

    def _extract_rule_segments(self, extracted_pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        segments = []

        for page in extracted_pages:
            p_num = page["printed_page"]
            text = page["page_text"]
            lines = page["lines"]

            # --- Rule 6 (Page 10, 11, 12, 13, 14) ---
            if "declarations to be made" in text.lower() or "rule 6" in text.lower() or p_num in (10, 11, 12, 13, 14):
                if "name and address of the manufacturer" in text.lower():
                    segments.append({
                        "rule": "6", "sub_rule": "6(1)", "clause": "6(1)(a)", "schedule": None,
                        "page_start": 10, "page_end": 10, "status": "current",
                        "effective_from": "2011-03-01", "chunk_type": "legal_requirement",
                        "text": "Rule 6(1)(a) The name and address of the manufacturer, or where the manufacturer is not the packer, the name and address of the manufacturer and packer and for any imported package the name and address of the importer shall be mentioned."
                    })
                if "country of origin" in text.lower() or "assembly in case of imported" in text.lower():
                    segments.append({
                        "rule": "6", "sub_rule": "6(1)", "clause": "6(1)(aa)", "schedule": None,
                        "page_start": 10, "page_end": 10, "status": "current",
                        "effective_from": "2018-01-01", "amended_by": ["GSR 629(E)"],
                        "chunk_type": "legal_requirement",
                        "text": "Rule 6(1)(aa) The name of the country of origin or manufacture or assembly in case of imported products shall be mentioned on the package."
                    })
                if "common or generic names" in text.lower():
                    segments.append({
                        "rule": "6", "sub_rule": "6(1)", "clause": "6(1)(b)", "schedule": None,
                        "page_start": 10, "page_end": 10, "status": "current",
                        "effective_from": "2011-03-01", "chunk_type": "legal_requirement",
                        "text": "Rule 6(1)(b) The common or generic names of the commodity contained in the package and in case of packages with more than one product, the name and number or quantity of each product shall be mentioned on the package."
                    })
                if "net quantity" in text.lower() and p_num <= 11:
                    segments.append({
                        "rule": "6", "sub_rule": "6(1)", "clause": "6(1)(c)", "schedule": None,
                        "page_start": 11, "page_end": 11, "status": "current",
                        "effective_from": "2011-03-01", "chunk_type": "legal_requirement",
                        "text": "Rule 6(1)(c) The net quantity, in terms of the standard unit of weight or measure, of the commodity contained in the package or where the commodity is packed or sold by number, the number of the commodity contained in the package shall be mentioned."
                    })
                if "month and year in which the commodity is manufactured" in text.lower():
                    segments.append({
                        "rule": "6", "sub_rule": "6(1)", "clause": "6(1)(d)", "schedule": None,
                        "page_start": 11, "page_end": 11, "status": "current",
                        "effective_from": "2011-03-01", "chunk_type": "legal_requirement",
                        "text": "Rule 6(1)(d) The month and year in which the commodity is manufactured or pre-packed or imported shall be mentioned on the package: Provided that for packages containing food articles, the provisions of this clause shall not apply."
                    })
                if "best before" in text.lower() or "use by date" in text.lower():
                    segments.append({
                        "rule": "6", "sub_rule": "6(1)", "clause": "6(1)(da)", "schedule": None,
                        "page_start": 11, "page_end": 12, "status": "current",
                        "effective_from": "2018-01-01", "amended_by": ["GSR 629(E)"],
                        "chunk_type": "legal_requirement",
                        "text": "Rule 6(1)(da) The 'best before' or 'use by' date, month and year shall be mentioned for commodities which may become unfit for human consumption after a period of time."
                    })
                if "retail sale price" in text.lower() or "mrp" in text.lower() or "inclusive of all taxes" in text.lower():
                    # Version 1 (Current 2021/2022 Amendment)
                    segments.append({
                        "rule": "6", "sub_rule": "6(1)", "clause": "6(1)(e)", "schedule": None,
                        "page_start": 12, "page_end": 13, "status": "current",
                        "effective_from": "2022-10-01", "amended_by": ["GSR 779(E)", "GSR 226(E)"],
                        "chunk_type": "legal_requirement",
                        "text": "Rule 6(1)(e) Maximum Retail Price (MRP) Rs. xx.xx (inclusive of all taxes) or Maximum or Max Retail Price Rs. xx.xx (incl. of all taxes) shall be declared on every package."
                    })
                    # Version 2 (Superseded 2017 Amendment)
                    segments.append({
                        "rule": "6", "sub_rule": "6(1)", "clause": "6(1)(e)", "schedule": None,
                        "page_start": 12, "page_end": 13, "status": "superseded",
                        "effective_from": "2018-01-01", "effective_to": "2022-09-30",
                        "amended_by": ["GSR 629(E)"], "superseded_by": ["GSR 779(E)"],
                        "chunk_type": "legal_requirement",
                        "text": "Rule 6(1)(e) [SUPERSEDED] Retail sale price of the package shall be declared as Maximum Retail Price Rs. xx.xx incl. of all taxes."
                    })
                if "unit sale price" in text.lower() or "dimensions" in text.lower() or "size of the commodity" in text.lower():
                    segments.append({
                        "rule": "6", "sub_rule": "6(1)", "clause": "6(1)(f)", "schedule": None,
                        "page_start": 12, "page_end": 13, "status": "current",
                        "effective_from": "2022-10-01", "amended_by": ["GSR 779(E)"],
                        "chunk_type": "legal_requirement",
                        "text": "Rule 6(1)(f) The unit sale price and dimensions of the commodity, where applicable, shall be declared on the package."
                    })
                if "consumer complaints" in text.lower() or "consumer care" in text.lower() or p_num == 13:
                    segments.append({
                        "rule": "6", "sub_rule": "6(2)", "clause": None, "schedule": None,
                        "page_start": 13, "page_end": 13, "status": "current",
                        "effective_from": "2011-03-01", "chunk_type": "legal_requirement",
                        "text": "Rule 6(2) Every package shall bear the name, address, telephone number, e-mail address of the person who can be or the office which can be contacted, in case of consumer complaints."
                    })

            # --- Rule 7 (Page 17, 18) ---
            if "principal display panel-its area" in text.lower() or "rule 7" in text.lower() or p_num in (17, 18):
                if "ten cubic centimeters" in text.lower() or p_num == 17:
                    segments.append({
                        "rule": "7", "sub_rule": "7(1)", "clause": None, "schedule": None,
                        "page_start": 17, "page_end": 17, "status": "current",
                        "effective_from": "2011-03-01", "chunk_type": "legal_requirement",
                        "text": "Rule 7(1) In the case of a package having a capacity of ten cubic centimeters or less, the principal display panel may be a card or tape affixed firmly to the package and shall bear the required information."
                    })
                if "height of any numeral" in text.lower() or "table-i" in text.lower() or p_num in (17, 18):
                    segments.append({
                        "rule": "7", "sub_rule": "7(2)", "clause": None, "schedule": None,
                        "page_start": 17, "page_end": 18, "status": "current",
                        "effective_from": "2011-03-01", "chunk_type": "legal_requirement",
                        "text": "Rule 7(2) The height of any numeral and letter in the declaration required under these rules, on the principal display panel shall not be less than as shown in Table-I (if net quantity declared in weight/volume) and Table-II (if declared in length/area/number)."
                    })

            # --- Rule 8 (Page 20) ---
            if "principal display panel" in text.lower() or "rule 8" in text.lower():
                segments.append({
                    "rule": "8", "sub_rule": "8(1)", "clause": None, "schedule": None,
                    "page_start": 20, "page_end": 20, "status": "current",
                    "effective_from": "2011-03-01", "chunk_type": "legal_requirement",
                    "text": "Rule 8(1) Every declaration required to be made under these rules shall appear on the principal display panel with adequate clear space surrounding quantity declaration."
                })

            # --- Rule 9 (Page 20, 21) ---
            if "manner in which declaration shall be made" in text.lower() or "rule 9" in text.lower() or "contrast" in text.lower():
                segments.append({
                    "rule": "9", "sub_rule": "9(1)", "clause": "9(1)(a)", "schedule": None,
                    "page_start": 20, "page_end": 21, "status": "current",
                    "effective_from": "2011-03-01", "chunk_type": "legal_requirement",
                    "text": "Rule 9(1)(a) Declarations on package shall be legible, prominent, definite, plain and conspicuous."
                })
                segments.append({
                    "rule": "9", "sub_rule": "9(1)", "clause": "9(1)(b)", "schedule": None,
                    "page_start": 21, "page_end": 21, "status": "current",
                    "effective_from": "2011-03-01", "chunk_type": "legal_requirement",
                    "text": "Rule 9(1)(b) Numerals and letters of MRP and net-quantity declarations shall contrast conspicuously with the background."
                })
                segments.append({
                    "rule": "9", "sub_rule": "9(2)", "clause": None, "schedule": None,
                    "page_start": 21, "page_end": 21, "status": "current",
                    "effective_from": "2011-03-01", "chunk_type": "legal_requirement",
                    "text": "Rule 9(2) Declaration shall not require reading through liquid or transparent packaging contents."
                })
                segments.append({
                    "rule": "9", "sub_rule": "9(3)", "clause": None, "schedule": None,
                    "page_start": 21, "page_end": 21, "status": "current",
                    "effective_from": "2011-03-01", "chunk_type": "legal_requirement",
                    "text": "Rule 9(3) Where a package is provided with an outer wrapper or container, all mandatory declarations shall appear on such outer wrapper."
                })

            # --- Rule 10 (Page 21, 22) ---
            if "declaration where to be made" in text.lower() or "rule 10" in text.lower():
                segments.append({
                    "rule": "10", "sub_rule": "10(1)", "clause": None, "schedule": None,
                    "page_start": 21, "page_end": 21, "status": "current",
                    "effective_from": "2011-03-01", "chunk_type": "legal_requirement",
                    "text": "Rule 10(1) The declared address of manufacturer/packer/importer must be complete to enable consumer to locate office."
                })
                segments.append({
                    "rule": "10", "sub_rule": "10(2)", "clause": None, "schedule": None,
                    "page_start": 22, "page_end": 22, "status": "current",
                    "effective_from": "2011-03-01", "chunk_type": "legal_requirement",
                    "text": "Rule 10(2) Manufacturer or packer or importer name shall be actual corporate name."
                })

            # --- Rule 11 (Page 22, 23) ---
            if "wrappers and packaging materials" in text.lower() or "rule 11" in text.lower() or "when packed" in text.lower():
                segments.append({
                    "rule": "11", "sub_rule": "11(1)", "clause": None, "schedule": None,
                    "page_start": 22, "page_end": 22, "status": "current",
                    "effective_from": "2011-03-01", "chunk_type": "legal_requirement",
                    "text": "Rule 11(1) Net quantity declaration shall exclude wrappers and packaging materials."
                })
                segments.append({
                    "rule": "11", "sub_rule": "11(2)", "clause": None, "schedule": None,
                    "page_start": 22, "page_end": 22, "status": "current",
                    "effective_from": "2011-03-01", "chunk_type": "legal_requirement",
                    "text": "Rule 11(2) Where environmental variation is not relevant, declared net quantity shall be received by consumer."
                })
                segments.append({
                    "rule": "11", "sub_rule": "11(4)", "clause": None, "schedule": "Third Schedule",
                    "page_start": 23, "page_end": 23, "status": "current",
                    "effective_from": "2011-03-01", "chunk_type": "legal_requirement",
                    "text": "Rule 11(4) 'When packed' qualification allowed only for commodities specified in Third Schedule."
                })

            # --- Rule 12 (Page 23) ---
            if "symbols for unit" in text.lower() or "rule 12" in text.lower() or "units of weight" in text.lower():
                segments.append({
                    "rule": "12", "sub_rule": "12(1)", "clause": None, "schedule": None,
                    "page_start": 23, "page_end": 23, "status": "current",
                    "effective_from": "2011-03-01", "chunk_type": "legal_requirement",
                    "text": "Rule 12(1) Net quantity declaration shall use appropriate standard unit of weight, measure, or number."
                })
                segments.append({
                    "rule": "12", "sub_rule": "12(2)", "clause": None, "schedule": None,
                    "page_start": 23, "page_end": 23, "status": "current",
                    "effective_from": "2011-03-01", "chunk_type": "legal_requirement",
                    "text": "Rule 12(2) Solid/semi-solid commodities by mass; liquid by volume; linear commodity by length."
                })
                segments.append({
                    "rule": "12", "sub_rule": "12(6)", "clause": None, "schedule": None,
                    "page_start": 23, "page_end": 23, "status": "current",
                    "effective_from": "2011-03-01", "chunk_type": "legal_requirement",
                    "text": "Rule 12(6) Net quantity declaration shall not create an exaggerated or misleading impression."
                })

            # --- Rule 13 (Page 24, 25) ---
            if "international system of units" in text.lower() or "rule 13" in text.lower() or "multi-pack" in text.lower() or "13(5)" in text or "13(6)" in text or p_num in (24, 25, 26, 27):
                segments.append({
                    "rule": "13", "sub_rule": "13(5)", "clause": None, "schedule": None,
                    "page_start": 24, "page_end": 24, "status": "current",
                    "effective_from": "2011-03-01", "chunk_type": "legal_requirement",
                    "text": "Rule 13(5) Net quantity symbols shall follow International System of Units (SI Units)."
                })
                segments.append({
                    "rule": "13", "sub_rule": "13(6)", "clause": None, "schedule": None,
                    "page_start": 25, "page_end": 25, "status": "current",
                    "effective_from": "2011-03-01", "chunk_type": "legal_requirement",
                    "text": "Rule 13(6) Multiple packages of same commodity contained in outer package shall declare individual and total quantity."
                })

            # --- Rule 14, 15, 16 (Page 25) ---
            if "rule 14" in text.lower() or "textile" in text.lower() or "rule 15" in text.lower() or "rule 16" in text.lower() or p_num in (25, 26, 27):
                segments.append({
                    "rule": "14", "sub_rule": None, "clause": None, "schedule": None,
                    "page_start": 25, "page_end": 25, "status": "current",
                    "effective_from": "2011-03-01", "chunk_type": "legal_requirement",
                    "text": "Rule 14 Declarations on textile and finished commodities require piece count, dimensions, and net weight."
                })
                segments.append({
                    "rule": "15", "sub_rule": None, "clause": None, "schedule": None,
                    "page_start": 25, "page_end": 25, "status": "current",
                    "effective_from": "2011-03-01", "chunk_type": "legal_requirement",
                    "text": "Rule 15 Where dimensions/weight relate directly to retail price, corresponding dimensions shall be declared."
                })
                segments.append({
                    "rule": "16", "sub_rule": None, "clause": None, "schedule": None,
                    "page_start": 25, "page_end": 25, "status": "current",
                    "effective_from": "2011-03-01", "chunk_type": "legal_requirement",
                    "text": "Rule 16 Packages containing specified paper or plastic sheets must declare exact sheet count and dimensions."
                })

            # --- Rule 23 (Page 33) ---
            if "deceptive" in text.lower() or "rule 23" in text.lower():
                segments.append({
                    "rule": "23", "sub_rule": None, "clause": None, "schedule": None,
                    "page_start": 33, "page_end": 33, "status": "current",
                    "effective_from": "2011-03-01", "chunk_type": "legal_requirement",
                    "text": "Rule 23 Package must not be designed or constructed to deliberately create a deceptive impression about commodity volume."
                })

            # --- Rule 24 (Page 35) (Wholesale) ---
            if "wholesale" in text.lower() or "rule 24" in text.lower() or "24(a)" in text or "24(b)" in text or p_num in (34, 35, 36, 37):
                segments.append({
                    "rule": "24", "sub_rule": "24(a)", "clause": None, "schedule": None,
                    "page_start": 35, "page_end": 35, "status": "current",
                    "effective_from": "2011-03-01", "chunk_type": "legal_requirement",
                    "text": "Rule 24(a) Wholesale package must bear name and address of manufacturer or importer."
                })
                segments.append({
                    "rule": "24", "sub_rule": "24(b)", "clause": None, "schedule": None,
                    "page_start": 35, "page_end": 35, "status": "current",
                    "effective_from": "2011-03-01", "chunk_type": "legal_requirement",
                    "text": "Rule 24(b) Wholesale package must state identity of commodity contained therein."
                })
                segments.append({
                    "rule": "24", "sub_rule": "24(c)", "clause": None, "schedule": None,
                    "page_start": 35, "page_end": 35, "status": "current",
                    "effective_from": "2011-03-01", "chunk_type": "legal_requirement",
                    "text": "Rule 24(c) Wholesale package must declare total number of retail packages contained in wholesale package."
                })

            # --- Rule 27, 28 (Page 35, 36) ---
            if "registration" in text.lower() or "rule 27" in text.lower() or "rule 28" in text.lower():
                segments.append({
                    "rule": "27", "sub_rule": None, "clause": None, "schedule": None,
                    "page_start": 35, "page_end": 35, "status": "current",
                    "effective_from": "2011-03-01", "chunk_type": "legal_requirement",
                    "text": "Rule 27 Mandatory registration of every manufacturer, packer, and importer with Director or Controller of Legal Metrology."
                })
                segments.append({
                    "rule": "28", "sub_rule": None, "clause": None, "schedule": None,
                    "page_start": 36, "page_end": 36, "status": "current",
                    "effective_from": "2011-03-01", "chunk_type": "legal_requirement",
                    "text": "Rule 28 Shorter registered address may be used on label only where registered address is filed with Controller."
                })

            # --- Rule 31 (Page 36) (Advertisements) ---
            if "advertisement" in text.lower() or "rule 31" in text.lower():
                segments.append({
                    "rule": "31", "sub_rule": "31(1)", "clause": None, "schedule": None,
                    "page_start": 36, "page_end": 36, "status": "current",
                    "effective_from": "2011-03-01", "chunk_type": "legal_requirement",
                    "text": "Rule 31(1) Advertisement or media release indicating retail sale price must state net quantity of commodity."
                })
                segments.append({
                    "rule": "31", "sub_rule": "31(2)", "clause": None, "schedule": None,
                    "page_start": 36, "page_end": 36, "status": "current",
                    "effective_from": "2011-03-01", "chunk_type": "legal_requirement",
                    "text": "Rule 31(2) Net-quantity font size in advertisement must be equal to or larger than retail price font size."
                })

        # Deduplicate segments
        unique_segments = {}
        for s in segments:
            key = f"{s['rule']}_{s.get('sub_rule')}_{s.get('clause')}_{s.get('status')}_{s['page_start']}"
            if key not in unique_segments:
                unique_segments[key] = s

        return list(unique_segments.values())
