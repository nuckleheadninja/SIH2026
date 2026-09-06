"""
report_generator.py — Statutory Field Inspection PDF Report Generator.

Generates official, print-ready PDF compliance reports for:
- Food Safety Officers (FSO) under FSS Act, 2006
- Legal Metrology Inspectors under Legal Metrology Act, 2009 & PCR, 2011

Features:
- Official Government of India & FSSAI statutory layout
- Multi-panel provenance tracking
- Rule 6 Mandatory Declarations Audit Table
- Rule 9 Numeral Font Height Audit
- Itemized Violations with Statutory Sections & Compoundable Penalties
- Officer Signature & Panchnama Certification block
"""

from __future__ import annotations

import io
from datetime import datetime
from typing import Any

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
    HRFlowable,
)


def generate_pdf_report(
    scan_result: dict[str, Any],
    product_category: str = "General Food",
    officer_name: str = "Authorized Inspecting Officer",
    officer_designation: str = "Food Safety Officer / Inspector (Legal Metrology)",
    station: str = "Central Enforcement Division",
) -> bytes:
    """
    Generate an official Statutory Inspection PDF report from a SurakshaScan scan result.
    Returns bytes of the compiled PDF.
    """
    buffer = io.BytesIO()

    # Document geometry: A4 with 12mm margins for print readiness
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
    )

    # Styles
    styles = getSampleStyleSheet()

    # Custom styles
    header_title_style = ParagraphStyle(
        "GovHeaderTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=14,
        alignment=1,  # Center
        textColor=colors.HexColor("#0f2027"),
    )

    header_sub_style = ParagraphStyle(
        "GovHeaderSub",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        alignment=1,  # Center
        textColor=colors.HexColor("#334e68"),
    )

    doc_title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        alignment=1,  # Center
        textColor=colors.HexColor("#102a43"),
    )

    section_heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=12,
        textColor=colors.HexColor("#102a43"),
        spaceAfter=3,
    )

    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#243b53"),
    )

    body_bold_style = ParagraphStyle(
        "ReportBodyBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#102a43"),
    )

    cell_style = ParagraphStyle(
        "ReportCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#243b53"),
    )

    cell_bold_style = ParagraphStyle(
        "ReportCellBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#102a43"),
    )

    cell_pass_style = ParagraphStyle(
        "ReportCellPass",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#1b7936"),
    )

    cell_fail_style = ParagraphStyle(
        "ReportCellFail",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#ba2525"),
    )

    legal_cite_style = ParagraphStyle(
        "LegalCite",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#486581"),
    )

    story = []

    # ── 1. Official Header Banner ──────────────────────────────────────────────
    header_text = """
    <b>GOVERNMENT OF INDIA</b><br/>
    MINISTRY OF CONSUMER AFFAIRS, FOOD & PUBLIC DISTRIBUTION · DEPARTMENT OF CONSUMER AFFAIRS<br/>
    LEGAL METROLOGY DIVISION & FOOD SAFETY AND STANDARDS AUTHORITY OF INDIA (FSSAI)
    """
    story.append(Paragraph(header_text, header_title_style))
    story.append(Spacer(1, 2 * mm))

    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#102a43"), spaceAfter=3))

    doc_subtitle = """
    <b>STATUTORY FIELD INSPECTION & COMPLIANCE VERIFICATION REPORT</b><br/>
    <font size="7.5" color="#486581">Enforcement under Legal Metrology (Packaged Commodities) Rules, 2011 & FSS (Labelling & Display) Regulations, 2020</font>
    """
    story.append(Paragraph(doc_subtitle, doc_title_style))
    story.append(Spacer(1, 3 * mm))

    # ── 2. Inspection Metadata Box ─────────────────────────────────────────────
    scan_id = scan_result.get("scan_id", "REF-N/A")
    timestamp = datetime.now().strftime("%d-%b-%Y %H:%M:%S IST")
    compliance = scan_result.get("compliance", {})
    is_compliant = compliance.get("is_compliant", False)
    issues = compliance.get("issues", [])
    extracted = scan_result.get("extracted_data", {})
    missing = scan_result.get("missing_mandatory_fields", [])
    panels_count = scan_result.get("panels_processed", 1)

    verdict_text = (
        "<font color='#1b7936'><b>PASS — COMPLIANT (CLEARED FOR RETAIL)</b></font>"
        if is_compliant
        else f"<font color='#ba2525'><b>NON-COMPLIANT — ACTION REQUIRED ({len(issues)} VIOLATIONS)</b></font>"
    )

    meta_data = [
        [
            Paragraph("<b>Inspection Reference ID:</b>", cell_bold_style),
            Paragraph(f"<code>{scan_id}</code>", cell_style),
            Paragraph("<b>Inspection Date/Time:</b>", cell_bold_style),
            Paragraph(timestamp, cell_style),
        ],
        [
            Paragraph("<b>Commodity Category:</b>", cell_bold_style),
            Paragraph(product_category, cell_style),
            Paragraph("<b>Panels Audited:</b>", cell_bold_style),
            Paragraph(f"{panels_count} Packaging Panel(s)", cell_style),
        ],
        [
            Paragraph("<b>Inspection Verdict:</b>", cell_bold_style),
            Paragraph(verdict_text, cell_style),
            Paragraph("<b>Violations Count:</b>", cell_bold_style),
            Paragraph(f"<b>{len(issues)}</b> item(s) noted", cell_style),
        ],
    ]

    meta_table = Table(meta_data, colWidths=[38 * mm, 52 * mm, 40 * mm, 56 * mm])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0f4f8")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#bcccdc")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d9e2ec")),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 4 * mm))

    # ── 3. Mandatory Declarations Audit Table (Rule 6 & FSSAI) ─────────────────
    story.append(Paragraph("<b>1. STATUTORY MANDATORY DECLARATIONS AUDIT (Rule 6 PCR, 2011 & FSSAI Regs)</b>", section_heading_style))

    field_map = [
        ("mrp", "Maximum Retail Price (MRP)", "Rule 6(1)(a)", lambda v: f"Rs. {v}" if v else "—"),
        ("net_quantity", "Net Quantity", "Rule 6(1)(b)", lambda v: v.get("raw", "—") if isinstance(v, dict) else (str(v) if v else "—")),
        ("mfg_date", "Date of Mfg / Pkg", "Rule 6(1)(e)", lambda v: str(v) if v else "—"),
        ("expiry_date", "Best Before / Expiry Date", "Rule 6(1)(f)", lambda v: str(v) if v else "—"),
        ("fssai_license", "FSSAI 14-Digit License", "FSS Act Sec 31", lambda v: str(v) if v else "—"),
        ("ingredients", "Ingredients List", "FSSAI Reg 5(2)", lambda v: f"{len(v)} ingredients listed" if isinstance(v, list) and v else ("Declared" if v else "—")),
        ("manufacturer", "Manufacturer / Packer", "Rule 6(1)(d)", lambda v: (str(v)[:45] + "...") if v and len(str(v)) > 45 else (str(v) if v else "—")),
        ("country_of_origin", "Country of Origin", "Rule 6(1)(n)", lambda v: str(v) if v else "—"),
        ("consumer_care", "Consumer Helpline / Care", "Rule 6(1)(h)", lambda v: (str(v)[:45] + "...") if v and len(str(v)) > 45 else (str(v) if v else "—")),
        ("allergens", "Allergen Disclosures", "FSSAI Reg 5(3)", lambda v: (", ".join(v) if isinstance(v, list) and v else (str(v) if v else "No specific allergen declared"))),
    ]

    meta_fields = extracted.get("_field_metadata", {})

    table_rows = [
        [
            Paragraph("<b>Mandatory Declaration</b>", cell_bold_style),
            Paragraph("<b>Statutory Rule</b>", cell_bold_style),
            Paragraph("<b>Detected Value on Package</b>", cell_bold_style),
            Paragraph("<b>Provenance</b>", cell_bold_style),
            Paragraph("<b>Audit Status</b>", cell_bold_style),
        ]
    ]

    for key, label, statutory_rule, fmt in field_map:
        val = extracted.get(key)
        provenance = "Panel 1"
        if key in meta_fields and meta_fields[key]:
            provenance = meta_fields[key].get("panel_name", "Panel 1")
            # Simplify panel string for tight table
            if "(" in provenance:
                provenance = provenance.split("(")[0].strip()

        if val:
            status_p = Paragraph("<font color='#1b7936'><b>DECLARED (OK)</b></font>", cell_pass_style)
            val_p = Paragraph(fmt(val), cell_style)
        else:
            is_mandatory_omission = key in missing
            if is_mandatory_omission:
                status_p = Paragraph("<font color='#ba2525'><b>NOT DECLARED [VIOLATION]</b></font>", cell_fail_style)
                val_p = Paragraph("<font color='#ba2525'><i>Missing / Not Legible</i></font>", cell_style)
            else:
                status_p = Paragraph("<font color='#627d98'>N/A / Voluntary</font>", cell_style)
                val_p = Paragraph("<i>Not Detected</i>", cell_style)

        table_rows.append([
            Paragraph(label, cell_bold_style),
            Paragraph(statutory_rule, legal_cite_style),
            val_p,
            Paragraph(provenance, cell_style),
            status_p,
        ])

    decl_table = Table(
        table_rows,
        colWidths=[42 * mm, 24 * mm, 62 * mm, 22 * mm, 36 * mm],
        repeatRows=1,
    )
    decl_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#243b53")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d9e2ec")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#bcccdc")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(decl_table)
    story.append(Spacer(1, 3.5 * mm))

    # ── 4. Legal Metrology Rule 9 Numeral Height Audit ────────────────────────
    font_compliance = extracted.get("font_compliance", {})
    if font_compliance and font_compliance.get("status") in ("PASS", "FAIL"):
        story.append(Paragraph("<b>2. RULE 9 NUMERAL & LETTER HEIGHT AUDIT (Principal Display Panel)</b>", section_heading_style))

        is_font_pass = font_compliance.get("is_compliant", True)
        est_mm = font_compliance.get("est_height_mm", 0)
        req_mm = font_compliance.get("required_min_mm", 0)
        pdp_ratio = font_compliance.get("font_ratio_pdp_pct", 0)
        net_qty_val = font_compliance.get("net_quantity_val", "—")
        net_qty_unit = font_compliance.get("unit", "")

        font_audit_rows = [
            [
                Paragraph("<b>Principal Display Panel (PDP)</b>", cell_bold_style),
                Paragraph(f"Declared: {net_qty_val} {net_qty_unit}", cell_style),
                Paragraph("<b>PDP Font Ratio:</b>", cell_bold_style),
                Paragraph(f"{pdp_ratio}% of label height", cell_style),
            ],
            [
                Paragraph("<b>Estimated Font Height:</b>", cell_bold_style),
                Paragraph(f"<b>{est_mm} mm</b>", cell_style),
                Paragraph("<b>Statutory Minimum (Table 1):</b>", cell_bold_style),
                Paragraph(f"<b>{req_mm} mm</b>", cell_style),
            ],
            [
                Paragraph("<b>Compliance Finding:</b>", cell_bold_style),
                Paragraph(
                    "<font color='#1b7936'><b>COMPLIANT (Satisfies Rule 9(1) Table 1 Minimum)</b></font>"
                    if is_font_pass
                    else f"<font color='#ba2525'><b>SUB-STANDARD DEFICIT ({est_mm} mm < {req_mm} mm Statutory Min)</b></font>",
                    cell_style,
                ),
                Paragraph("<b>Governing Regulation:</b>", cell_bold_style),
                Paragraph("Legal Metrology (PC) Rules, 2011 — Rule 9(1)", legal_cite_style),
            ],
        ]

        font_table = Table(font_audit_rows, colWidths=[45 * mm, 45 * mm, 45 * mm, 51 * mm])
        font_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0f4f8")),
            ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#bcccdc")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d9e2ec")),
            ("TOPPADDING", (0, 0), (-1, -1), 2.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(font_table)
        story.append(Spacer(1, 3.5 * mm))

    # ── 5. Statutory Violations, Compoundable Penalties & Directives ───────────
    if issues:
        story.append(Paragraph("<b>3. STATUTORY NON-COMPLIANCE FINDINGS & COMPOUNDABLE PENALTIES</b>", section_heading_style))

        issue_rows = [
            [
                Paragraph("<b>#</b>", cell_bold_style),
                Paragraph("<b>Defect / Statutory Violation</b>", cell_bold_style),
                Paragraph("<b>Enforcement Action / Legal Penalty Provision</b>", cell_bold_style),
            ]
        ]

        for idx, iss in enumerate(issues, 1):
            title = iss.get("title") or iss.get("detail", f"Defect #{idx}")
            detail = iss.get("detail", "")
            action = iss.get("officer_action") or iss.get("recommendation", "Direct manufacturer to rectify.")
            reg = iss.get("regulation_id", "Legal Metrology Act, 2009 / FSSAI Regulations")
            penalty = iss.get("penalty_provision", "")

            obs_html = f"""
            <b>{title}</b><br/>
            <font size="7" color="#334e68"><b>Observation:</b> {detail}</font><br/>
            <font size="6.5" color="#486581"><b>Statutory Section:</b> {reg}</font>
            """

            penalty_html = f"""
            <font size="7" color="#102a43"><b>Officer Action:</b> {action}</font><br/>
            <font size="6.5" color="#ba2525"><b>Statutory Penalty:</b> {penalty}</font>
            """ if penalty else f'<font size="7" color="#102a43"><b>Officer Action:</b> {action}</font>'

            issue_rows.append([
                Paragraph(str(idx), cell_bold_style),
                Paragraph(obs_html, cell_style),
                Paragraph(penalty_html, cell_style),
            ])

        issue_table = Table(issue_rows, colWidths=[8 * mm, 88 * mm, 90 * mm], repeatRows=1)
        issue_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#ba2525")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#ba2525")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#f8d7da")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#fff5f5"), colors.white]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(issue_table)
        story.append(Spacer(1, 3.5 * mm))
    else:
        story.append(Paragraph("<b>3. STATUTORY NON-COMPLIANCE FINDINGS</b>", section_heading_style))
        story.append(Paragraph(
            "<font color='#1b7936'><b>No statutory label violations detected. The packaging conforms to all evaluated provisions of Legal Metrology (Packaged Commodities) Rules, 2011 and FSSAI (Labelling and Display) Regulations, 2020.</b></font>",
            body_style,
        ))
        story.append(Spacer(1, 3.5 * mm))

    # ── 6. Panchnama / Officer Certification & Signature ───────────────────────
    cert_block = []
    cert_block.append(Paragraph("<b>4. STATUTORY CERTIFICATION & INSPECTING OFFICER SIGN-OFF</b>", section_heading_style))
    cert_text = """
    <i>I hereby certify that the digital inspection and computer-assisted compliance verification of the pre-packaged commodity identified above was conducted in accordance with the statutory standards prescribed under the <b>Legal Metrology Act, 2009</b>, the <b>Legal Metrology (Packaged Commodities) Rules, 2011</b>, and the <b>Food Safety and Standards Act, 2006</b>. The findings recorded herein represent true optical character and legal metadata extractions from the submitted sample.</i>
    """
    cert_block.append(Paragraph(cert_text, body_style))
    cert_block.append(Spacer(1, 3 * mm))

    sig_data = [
        [
            Paragraph("<b>Inspection Station / Division:</b><br/>" + station, cell_style),
            Paragraph("<b>Inspecting Officer Name:</b><br/>" + officer_name, cell_style),
        ],
        [
            Paragraph("<b>Inspection Date & Seal:</b><br/>" + datetime.now().strftime("%d-%b-%Y") + " [OFFICIAL SEAL]", cell_style),
            Paragraph("<b>Designation & Signature:</b><br/>" + officer_designation + "<br/><br/>_____________________________________", cell_style),
        ],
    ]
    sig_table = Table(sig_data, colWidths=[93 * mm, 93 * mm])
    sig_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#cbd5e1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    cert_block.append(sig_table)

    story.append(KeepTogether(cert_block))

    # Build document
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
