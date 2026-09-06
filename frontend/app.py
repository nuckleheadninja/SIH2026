"""
app.py — SurakshaScan Live Camera & IP Camera Frontend (Streamlit MVP)

Supports:
- 📱 WiFi / IP Camera (Phone - High Quality 1080p/4K capture via IP Webcam / DroidCam / RTSP)
- 📷 Built-in Laptop Webcam (st.camera_input)
- 📁 Image File Upload (JPG, PNG, WEBP)
"""

import hashlib
import io
import json
import os
import sys
import time
from pathlib import Path

import httpx
import streamlit as st
from PIL import Image

# ── Ensure frontend & root are on sys.path ──────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from camera_utils import (
    fetch_ip_camera_frame,
    get_image_metadata,
    is_host_reachable,
    set_camera_torch,
    trigger_camera_autofocus,
    normalize_ip_cam_url,
)

# ── Config ─────────────────────────────────────────────────────────────────────
API_BASE = "http://localhost:8000"
SCAN_ENDPOINT = f"{API_BASE}/scan/upload"

DEFAULT_IP_CAM_URL = "http://192.168.1.11:8080"

PRODUCT_CATEGORIES = [
    "Biscuits / Baked Goods",
    "Beverages",
    "Snacks / Namkeen",
    "Dairy Products",
    "Noodles / Pasta",
    "Confectionery / Candy",
    "Sauces / Condiments",
    "Packaged Water",
    "Breakfast Cereals",
    "Baby Food",
    "General Food",
]

SEVERITY_COLOR = {
    "critical": "🔴",
    "warning":  "🟡",
    "info":     "🔵",
}

# ── Page Setup ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SurakshaScan",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Header */
.header-band {
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
    padding: 1.5rem 2rem;
    border-radius: 12px;
    margin-bottom: 1.5rem;
    text-align: center;
}
.header-band h1 {
    color: #fff;
    font-size: 2rem;
    font-weight: 700;
    margin: 0;
    letter-spacing: -0.5px;
}
.header-band p {
    color: #a0c4d8;
    font-size: 0.9rem;
    margin: 0.3rem 0 0;
}

/* Status Pill */
.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font-size: 0.85rem;
    font-weight: 500;
    padding: 0.35rem 0.8rem;
    border-radius: 20px;
    background: #172433;
    border: 1px solid #293d52;
    color: #b0c9e0;
    margin-bottom: 0.8rem;
}
.dot-online {
    width: 9px;
    height: 9px;
    border-radius: 50%;
    background: #2ecc71;
    box-shadow: 0 0 8px #2ecc71;
}
.dot-offline {
    width: 9px;
    height: 9px;
    border-radius: 50%;
    background: #e74c3c;
}

/* Resolution Badge */
.resolution-badge {
    display: inline-block;
    padding: 0.4rem 0.9rem;
    border-radius: 8px;
    font-size: 0.83rem;
    font-weight: 600;
    margin: 0.4rem 0 0.8rem 0;
    border: 1px solid rgba(255,255,255,0.15);
}

/* Verdict badges */
.badge-pass {
    background: linear-gradient(135deg, #00b09b, #96c93d);
    color: white;
    font-size: 1.5rem;
    font-weight: 700;
    padding: 1rem 1.8rem;
    border-radius: 12px;
    text-align: center;
    letter-spacing: 1.5px;
    box-shadow: 0 4px 20px rgba(0,176,155,0.4);
}
.badge-fail {
    background: linear-gradient(135deg, #c0392b, #e74c3c);
    color: white;
    font-size: 1.5rem;
    font-weight: 700;
    padding: 1rem 1.8rem;
    border-radius: 12px;
    text-align: center;
    letter-spacing: 1.5px;
    box-shadow: 0 4px 20px rgba(231,76,60,0.4);
}

/* Field cards */
.field-card {
    background: #1e2a38;
    border: 1px solid #2e3d50;
    border-radius: 10px;
    padding: 0.75rem 1rem;
    margin-bottom: 0.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.field-label {
    color: #7f9ab5;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.field-value {
    color: #e8f4f8;
    font-size: 0.95rem;
    font-weight: 500;
}
.field-missing {
    color: #e74c3c;
    font-size: 0.85rem;
    font-style: italic;
}

/* Issue cards */
.issue-card {
    border-left: 4px solid #e74c3c;
    background: #1e2a38;
    border-radius: 0 8px 8px 0;
    padding: 0.8rem 1rem;
    margin-bottom: 0.6rem;
}
.issue-card.warning { border-left-color: #f39c12; }
.issue-card.info    { border-left-color: #3498db; }
.issue-regulation {
    color: #7f9ab5;
    font-size: 0.75rem;
    margin-top: 0.3rem;
    font-family: monospace;
}

/* Placeholder card */
.placeholder-card {
    background: #172433;
    border: 1px dashed #2d455e;
    border-radius: 12px;
    padding: 2.5rem 1.5rem;
    text-align: center;
    color: #8da4be;
}
.placeholder-card h4 {
    color: #d1e2f2;
    margin-bottom: 0.5rem;
}
</style>
""", unsafe_allow_html=True)

# ── Session State Initialization ───────────────────────────────────────────────
if "ip_camera_url" not in st.session_state:
    st.session_state["ip_camera_url"] = DEFAULT_IP_CAM_URL

if "captured_image_bytes" not in st.session_state:
    st.session_state["captured_image_bytes"] = None

if "captured_source_info" not in st.session_state:
    st.session_state["captured_source_info"] = None

if "torch_active" not in st.session_state:
    st.session_state["torch_active"] = False

if "last_scan_result" not in st.session_state:
    st.session_state["last_scan_result"] = None

if "last_scan_hash" not in st.session_state:
    st.session_state["last_scan_hash"] = None

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="header-band">
    <h1>🛡️ SurakshaScan</h1>
    <p>AI-Powered Legal Metrology &amp; Food Safety Compliance Checker &nbsp;|&nbsp; SIH 26034</p>
</div>
""", unsafe_allow_html=True)

# ── Layout ─────────────────────────────────────────────────────────────────────
col_cam, col_results = st.columns([1, 1], gap="large")

# ═══════════════════════════════════════════════════════════════════════════════
# COLUMN 1: CAMERA & CAPTURE SOURCE
# ═══════════════════════════════════════════════════════════════════════════════
with col_cam:
    st.markdown("### 📷 Label Capture Source")

    category = st.selectbox(
        "Product Category",
        PRODUCT_CATEGORIES,
        index=0,
        help="Select the product type for category-specific additive and compliance checks.",
    )

    col_opt1, col_opt2 = st.columns(2)
    with col_opt1:
        is_curved = st.checkbox("🥫 Curved Bottle / Can", help="Unroll text compressed along the curved edges of cylindrical bottles/cans")
    with col_opt2:
        use_hindi = st.checkbox("🇮🇳 Bilingual (Hindi)", help="Enable Devanagari Hindi OCR engine")

    source_mode = st.radio(
        "Select Camera Input:",
        [
            "📱 WiFi IP Camera (Phone - High Quality)",
            "💻 Built-in Laptop Webcam",
            "📁 Upload Image File",
        ],
        horizontal=False,
    )

    active_bytes = None
    active_source = None

    # ── Option 1: WiFi IP Camera ───────────────────────────────────────────────
    if source_mode == "📱 WiFi IP Camera (Phone - High Quality)":
        st.markdown("---")
        
        ip_url_input = st.text_input(
            "Phone / IP Camera URL:",
            value=st.session_state["ip_camera_url"],
            placeholder="http://192.168.1.11:8080",
            help="Enter the IP address & port shown in your IP camera app (e.g. IP Webcam on Android).",
        )
        st.session_state["ip_camera_url"] = ip_url_input

        # Live reachability ping
        reachable = is_host_reachable(ip_url_input, timeout=1.8)
        if reachable:
            st.markdown(
                f'<div class="status-pill"><span class="dot-online"></span> Camera Online: <code>{ip_url_input}</code></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="status-pill"><span class="dot-offline"></span> Camera Offline or Unreachable</div>',
                unsafe_allow_html=True,
            )

        col_af, col_torch = st.columns([1.5, 1])
        with col_af:
            use_autofocus = st.checkbox(
                "Trigger auto-focus before photo",
                value=True,
                help="Uses /photoaf.jpg to auto-focus phone lens for ultra-sharp ingredient and FSSAI text.",
            )
        with col_torch:
            torch_btn_label = "💡 Torch: OFF" if not st.session_state["torch_active"] else "🔦 Torch: ON"
            if st.button(torch_btn_label, use_container_width=True):
                new_state = not st.session_state["torch_active"]
                if set_camera_torch(ip_url_input, enable=new_state):
                    st.session_state["torch_active"] = new_state
                    st.toast(f"Torch switched {'ON' if new_state else 'OFF'}")
                else:
                    st.warning("Torch control not supported or camera offline.")

        # Capture & Focus Buttons
        col_btn1, col_btn2 = st.columns([2, 1])
        with col_btn1:
            capture_clicked = st.button("📸 Capture High-Res Frame", type="primary", use_container_width=True)
        with col_btn2:
            focus_clicked = st.button("🎯 Focus Lens", use_container_width=True)

        if focus_clicked:
            with st.spinner("Focusing lens..."):
                if trigger_camera_autofocus(ip_url_input):
                    st.success("Lens focused!")
                else:
                    st.warning("Focus trigger failed.")

        if capture_clicked:
            with st.spinner("Capturing high-resolution photo from phone camera…"):
                try:
                    frame = fetch_ip_camera_frame(ip_url_input, autofocus=use_autofocus, timeout=8.0)
                    st.session_state["captured_image_bytes"] = frame
                    st.session_state["captured_source_info"] = f"IP Camera ({ip_url_input})"
                    st.success("High-res frame captured!")
                except Exception as e:
                    st.error(f"❌ Capture failed: {e}")

        # Show captured IP frame if available
        if st.session_state["captured_image_bytes"]:
            active_bytes = st.session_state["captured_image_bytes"]
            active_source = st.session_state["captured_source_info"]

            meta = get_image_metadata(active_bytes)
            st.markdown(
                f'<div class="resolution-badge" style="background: {meta["quality_color"]}22; color: {meta["quality_color"]}; border-color: {meta["quality_color"]}55;">'
                f'Resolution: <b>{meta["width"]} × {meta["height"]}</b> ({meta["megapixels"]} MP, {meta["size_kb"]} KB) &nbsp;•&nbsp; {meta["quality_label"]}'
                f'</div>',
                unsafe_allow_html=True,
            )

            st.image(active_bytes, caption="Captured Food Label", use_container_width=True)

            if st.button("🗑️ Clear / Retake Photo", use_container_width=True):
                st.session_state["captured_image_bytes"] = None
                st.session_state["captured_source_info"] = None
                st.session_state["last_scan_result"] = None
                st.session_state["last_scan_hash"] = None
                st.rerun()

        # Instructions accordion
        with st.expander("📖 Setup Guide: How to connect your Phone Camera"):
            st.markdown("""
            **Android (Fastest & Best Quality — 1080p/4K):**
            1. Install free app **IP Webcam** (by Pavel Khlebovich) from Google Play Store.
            2. Open the app, scroll to the bottom, and tap **"Start server"**.
            3. Note the IP address shown at the bottom of the phone screen (e.g. `http://192.168.1.11:8080`).
            4. Enter this address in the input field above and tap **"Capture High-Res Frame"**!
            
            **iOS (iPhone / iPad):**
            1. Install **DroidCam** or **IP Camera Lite** from App Store.
            2. Start the camera server and use the WiFi URL shown in the app.
            
            **No shared Wi-Fi?**
            - Turn on your phone's **Mobile Hotspot**, connect your PC to it, and use the hotspot IP shown in the app!
            """)

    # ── Option 2: Built-in Webcam ──────────────────────────────────────────────
    elif source_mode == "💻 Built-in Laptop Webcam":
        st.markdown("---")
        st.markdown("**Hold the food label in front of your webcam and click 'Take Photo'.**")
        webcam_file = st.camera_input("Point webcam at label", key="webcam_cam")
        if webcam_file:
            active_bytes = webcam_file.getvalue()
            active_source = "Built-in Webcam"
            meta = get_image_metadata(active_bytes)
            st.caption(f"Webcam frame: {meta['width']}×{meta['height']} ({meta['size_kb']} KB)")

    # ── Option 3: Upload Image File ────────────────────────────────────────────
    elif source_mode == "📁 Upload Image File":
        st.markdown("---")
        uploaded_file = st.file_uploader(
            "Choose a product label photo",
            type=["jpg", "jpeg", "png", "webp"],
            key="file_uploader_cam",
        )
        if uploaded_file:
            active_bytes = uploaded_file.getvalue()
            active_source = f"Uploaded: {uploaded_file.name}"
            meta = get_image_metadata(active_bytes)
            st.markdown(
                f'<div class="resolution-badge" style="background: {meta["quality_color"]}22; color: {meta["quality_color"]}; border-color: {meta["quality_color"]}55;">'
                f'Resolution: <b>{meta["width"]} × {meta["height"]}</b> ({meta["megapixels"]} MP, {meta["size_kb"]} KB)'
                f'</div>',
                unsafe_allow_html=True,
            )
            st.image(active_bytes, caption=uploaded_file.name, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# COLUMN 2: COMPLIANCE ANALYSIS & RESULTS
# ═══════════════════════════════════════════════════════════════════════════════
with col_results:
    st.markdown("### 📋 Compliance Audit Report")

    if not active_bytes:
        st.markdown("""
        <div class="placeholder-card">
            <h4>No Label Image Captured</h4>
            <p>Select your camera input on the left to capture or upload a packaged food product label.</p>
            <p style="font-size: 0.85rem; color: #6482a0; margin-top: 1rem;">
                💡 <b>Tip:</b> Using your phone's <b>WiFi IP Camera</b> provides full sensor resolution (1080p+)
                which dramatically improves OCR accuracy on fine-print ingredient lists and FSSAI numbers!
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    # Compute a cache hash based on image bytes + selected category + options
    opt_str = f"{category}_{is_curved}_{use_hindi}"
    img_hash = hashlib.md5(active_bytes + opt_str.encode()).hexdigest()
    
    # Check if we need to call the backend API
    need_scan = (
        st.session_state["last_scan_result"] is None
        or st.session_state["last_scan_hash"] != img_hash
    )

    col_hdr, col_rescan = st.columns([2, 1])
    with col_hdr:
        st.caption(f"Source: **{active_source or 'Image'}**")
    with col_rescan:
        if st.button("🔄 Re-Analyze", use_container_width=True):
            need_scan = True

    if need_scan:
        with st.spinner("🔍 Running OCR + NER Compliance Pipeline… (analyzing labels, dates, additives)"):
            try:
                category_clean = category.split(" / ")[0].strip()
                response = httpx.post(
                    SCAN_ENDPOINT,
                    files={"file": ("label.jpg", active_bytes, "image/jpeg")},
                    data={
                        "product_category": category_clean,
                        "is_curved": "true" if is_curved else "false",
                        "use_hindi": "true" if use_hindi else "false",
                    },
                    timeout=120.0,
                )
                response.raise_for_status()
                result = response.json()
                st.session_state["last_scan_result"] = result
                st.session_state["last_scan_hash"] = img_hash
            except httpx.ConnectError:
                st.error(
                    "❌ Cannot connect to backend at `localhost:8000`.\n\n"
                    "Make sure the backend server is running: `uvicorn main:app --reload --port 8000`"
                )
                st.stop()
            except Exception as e:
                st.error(f"❌ Scan failed: {e}")
                st.stop()
    else:
        result = st.session_state["last_scan_result"]

    # ── Display Verdict ────────────────────────────────────────────────────────
    compliance = result.get("compliance", {})
    is_compliant = compliance.get("is_compliant", False)
    issues = compliance.get("issues", [])
    extracted = result.get("extracted_data", {})
    missing = result.get("missing_mandatory_fields", [])

    if is_compliant:
        st.markdown('<div class="badge-pass">✅ &nbsp; COMPLIANT</div>', unsafe_allow_html=True)
    else:
        n = len(issues)
        st.markdown(
            f'<div class="badge-fail">❌ &nbsp; NON-COMPLIANT &nbsp;·&nbsp; {n} violation{"s" if n != 1 else ""}</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Extracted Label Fields ────────────────────────────────────────────────
    with st.expander("🔍 Extracted Declarations (Legal Metrology & FSSAI)", expanded=True):
        field_map = {
            "mrp":               ("MRP",               lambda v: f"₹ {v}"),
            "net_quantity":      ("Net Quantity",      lambda v: v.get("raw", "—") if v else "—"),
            "mfg_date":          ("Mfg Date",          lambda v: v),
            "expiry_date":       ("Best Before",       lambda v: v),
            "fssai_license":     ("FSSAI License",     lambda v: v),
            "ingredients":       ("Ingredients",       lambda v: f"{len(v)} detected" if isinstance(v, list) and v else ("Detected" if v else "Not detected")),
            "manufacturer":      ("Manufacturer",      lambda v: v),
            "country_of_origin": ("Country of Origin", lambda v: v),
            "consumer_care":     ("Customer Care",     lambda v: v),
            "allergens":         ("Allergens",         lambda v: ", ".join(v) if isinstance(v, list) else v),
        }

        for key, (label, fmt) in field_map.items():
            val = extracted.get(key)
            if val:
                formatted = fmt(val)
                st.markdown(
                    f'<div class="field-card">'
                    f'<span class="field-label">{label}</span>'
                    f'<span class="field-value">{formatted}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            else:
                missing_flag = " ⚠️ MANDATORY" if key in missing else ""
                st.markdown(
                    f'<div class="field-card">'
                    f'<span class="field-label">{label}</span>'
                    f'<span class="field-missing">Not detected{missing_flag}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    # ── Ingredients & Additives ───────────────────────────────────────────────
    ingredients = extracted.get("ingredients", [])
    additives = extracted.get("additives", [])
    allergens = extracted.get("allergens", [])

    if ingredients:
        with st.expander(f"🧪 Cleaned Ingredients ({len(ingredients)} detected)", expanded=True):
            for i, ing in enumerate(ingredients, 1):
                st.markdown(f"**{i}.** {ing}")
    else:
        with st.expander("🧪 Cleaned Ingredients (0 detected)", expanded=False):
            st.info("No ingredient list detected on this package.")

    if allergens:
        with st.expander(f"⚠️ Allergen Declarations ({len(allergens)} items)", expanded=True):
            st.warning("Allergens detected: " + ", ".join(allergens))

    if additives:
        with st.expander(f"⚗️ Additives / INS Codes ({len(additives)} detected)", expanded=True):
            for a in additives:
                if isinstance(a, dict):
                    code = a.get("code", "INS")
                    name = a.get("name", "")
                    if name:
                        st.markdown(f"- **{code}** — {name}")
                    else:
                        st.markdown(f"- **{code}**")
                else:
                    st.markdown(f"- **{a}**")
    else:
        with st.expander("⚗️ Additives / INS Codes (0 detected)", expanded=False):
            st.info("No additives or INS codes detected.")

    # ── Violations & Compliance Issues ────────────────────────────────────────
    if issues:
        st.markdown("#### ⚠️ Compliance Issues & Violations")
        for issue in issues:
            sev = issue.get("severity", "warning")
            icon = SEVERITY_COLOR.get(sev, "🟡")
            css_class = "issue-card" + (" warning" if sev == "warning" else " info" if sev == "info" else "")
            st.markdown(
                f'<div class="{css_class}">'
                f'<strong>{icon} {issue.get("detail", "")}</strong><br>'
                f'<em>💡 {issue.get("recommendation", "")}</em>'
                f'<div class="issue-regulation">📜 {issue.get("regulation_id", "")}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
    elif not is_compliant:
        st.info("Mandatory declarations missing.")

    # ── RAG Contract Payload ──────────────────────────────────────────────────
    rag_payload = result.get("rag_payload")
    if rag_payload:
        with st.expander("📦 RAG Contract Payload (Shared JSON Schema)", expanded=False):
            st.markdown("*Canonical JSON generated for `legal_metrology_rag` & `compliance_engine`:*")
            st.json(rag_payload)
            import json as _json
            st.download_button(
                label="📥 Download RAG Payload (.json)",
                data=_json.dumps(rag_payload, indent=2),
                file_name=f"rag_payload_{result.get('scan_id', 'scan')[:8]}.json",
                mime="application/json",
                use_container_width=True,
            )

    # ── Debug / Raw Response ──────────────────────────────────────────────────
    with st.expander("🛠️ Raw Inspection JSON (Officer / Debug View)"):
        st.json(result)

    # ── Scan Footer Metadata ──────────────────────────────────────────────────
    st.caption(
        f"Scan ID: `{result.get('scan_id', '—')}`  |  "
        f"Detections: {result.get('ocr_detections_count', 0)}  |  "
        f"Category: {category}"
    )
