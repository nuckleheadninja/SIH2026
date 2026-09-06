"""
app.py — SurakshaScan Live Camera & IP Camera Frontend (Streamlit MVP)

Supports:
- 📱 WiFi / IP Camera (Phone - High Quality 1080p/4K capture via IP Webcam / DroidCam / RTSP)
- 📷 Built-in Laptop Webcam (st.camera_input)
- 📁 Image File Upload (JPG, PNG, WEBP)
"""

import base64
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
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
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

if "staged_panels" not in st.session_state:
    st.session_state["staged_panels"] = []

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

            col_cam_act1, col_cam_act2 = st.columns(2)
            with col_cam_act1:
                if st.button("➕ Add to Multi-Panel Audit", use_container_width=True):
                    p_num = len(st.session_state["staged_panels"]) + 1
                    st.session_state["staged_panels"].append({
                        "bytes": active_bytes,
                        "name": f"ip_camera_panel_{p_num}.jpg",
                        "source": f"IP Camera (Panel {p_num})",
                    })
                    st.session_state["captured_image_bytes"] = None
                    st.toast(f"✅ Staged as Panel {p_num}!")
                    st.rerun()
            with col_cam_act2:
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
            if st.button("➕ Add to Multi-Panel Audit", key="add_webcam_panel", use_container_width=True):
                p_num = len(st.session_state["staged_panels"]) + 1
                st.session_state["staged_panels"].append({
                    "bytes": active_bytes,
                    "name": f"webcam_panel_{p_num}.jpg",
                    "source": f"Webcam (Panel {p_num})",
                })
                st.toast(f"✅ Staged as Panel {p_num}!")
                st.rerun()

    # ── Option 3: Upload Image Files ───────────────────────────────────────────
    elif source_mode == "📁 Upload Image File":
        st.markdown("---")
        st.markdown("**Upload one or multiple photos of packaging panels (Front, Back, Side, Crimp, etc.):**")
        uploaded_files = st.file_uploader(
            "Choose packaging label photos (Multi-panel supported)",
            type=["jpg", "jpeg", "png", "webp"],
            accept_multiple_files=True,
            key="file_uploader_cam",
            help="Select multiple photos to analyze front, back, and side panels together in one consolidated compliance report!",
        )

    # ── Staged Panels Consolidation ────────────────────────────────────────────
    active_panels: list[dict] = []
    if source_mode == "📁 Upload Image File":
        if uploaded_files:
            active_panels = [
                {"bytes": uf.getvalue(), "name": uf.name, "source": f"Uploaded: {uf.name}"}
                for uf in uploaded_files
            ]
            st.markdown(f"**📸 {len(uploaded_files)} Panel Image{'s' if len(uploaded_files) > 1 else ''} Ready for Consolidated Audit:**")
            cols = st.columns(min(len(uploaded_files), 3))
            for i, uf in enumerate(uploaded_files):
                with cols[i % min(len(uploaded_files), 3)]:
                    meta = get_image_metadata(uf.getvalue())
                    st.caption(f"**Panel {i+1}**: `{uf.name[:18]}`")
                    st.image(uf.getvalue(), use_container_width=True)
                    st.markdown(
                        f'<div class="resolution-badge" style="background: {meta["quality_color"]}22; color: {meta["quality_color"]}; font-size: 0.73rem; margin: 0 0 0.4rem 0;">'
                        f'{meta["width"]}×{meta["height"]} ({meta["size_kb"]} KB)'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
    else:
        # Camera / Webcam staged panels
        if st.session_state["staged_panels"]:
            active_panels = st.session_state["staged_panels"]
            st.markdown(f"**📸 {len(active_panels)} Staged Panels in Session:**")
            cols = st.columns(min(len(active_panels), 3))
            for i, p in enumerate(active_panels):
                with cols[i % min(len(active_panels), 3)]:
                    st.caption(f"**Panel {i+1}**")
                    st.image(p["bytes"], use_container_width=True)
            if st.button("🗑️ Reset All Staged Panels", use_container_width=True):
                st.session_state["staged_panels"] = []
                st.session_state["last_scan_result"] = None
                st.session_state["last_scan_hash"] = None
                st.rerun()
        elif active_bytes:
            active_panels = [{"bytes": active_bytes, "name": "camera_capture.jpg", "source": active_source}]


# ═══════════════════════════════════════════════════════════════════════════════
# COLUMN 2: COMPLIANCE ANALYSIS & RESULTS
# ═══════════════════════════════════════════════════════════════════════════════
with col_results:
    st.markdown("### 📋 Compliance Audit Report")

    if not active_panels:
        st.markdown("""
        <div class="placeholder-card">
            <h4>No Packaging Images Provided</h4>
            <p>Select your camera input or file upload on the left to capture or upload packaging panel photos.</p>
            <p style="font-size: 0.85rem; color: #6482a0; margin-top: 1rem;">
                💡 <b>Multi-Panel Support:</b> You can upload or capture <b>multiple photos</b> (Front PDP, Back Ingredients, Side MRP) to analyze all mandatory statutory declarations across the entire product in one consolidated audit!
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    # Compute a cache hash based on all panel bytes + selected category + options
    combined_bytes = b"".join(p["bytes"] for p in active_panels)
    opt_str = f"{category}_{is_curved}_{use_hindi}_{len(active_panels)}"
    img_hash = hashlib.md5(combined_bytes + opt_str.encode()).hexdigest()

    # Check if we need to call the backend API
    need_scan = (
        st.session_state["last_scan_result"] is None
        or st.session_state["last_scan_hash"] != img_hash
    )

    col_hdr, col_rescan = st.columns([2, 1])
    with col_hdr:
        src_label = f"{len(active_panels)} Panel{'s' if len(active_panels) > 1 else ''} ({active_panels[0]['name']}{f' + {len(active_panels)-1} more' if len(active_panels) > 1 else ''})"
        st.caption(f"Source: **{src_label}**")
    with col_rescan:
        if st.button("🔄 Re-Analyze", use_container_width=True):
            need_scan = True

    if need_scan:
        panel_label = f"{len(active_panels)} packaging panels" if len(active_panels) > 1 else "packaging label"
        with st.spinner(f"🔍 Running OCR + NER Compliance Pipeline across {panel_label}…"):
            try:
                category_clean = category.split(" / ")[0].strip()
                files_payload = [
                    ("files", (p["name"], p["bytes"], "image/jpeg"))
                    for p in active_panels
                ]
                response = httpx.post(
                    SCAN_ENDPOINT,
                    files=files_payload,
                    data={
                        "product_category": category_clean,
                        "is_curved": "true" if is_curved else "false",
                        "use_hindi": "true" if use_hindi else "false",
                    },
                    timeout=180.0,
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
    panels_count = result.get("panels_processed", 1)

    if panels_count > 1:
        st.markdown(
            f'<div class="status-pill" style="background: #172a3a; border-color: #274b6b; color: #72b9f3; margin-bottom: 0.8rem;">'
            f'<span class="dot-online"></span> <b>Multi-Panel Audit Consolidated:</b> {panels_count} packaging panels evaluated together'
            f'</div>',
            unsafe_allow_html=True,
        )

    if is_compliant:
        st.markdown('<div class="badge-pass">✅ &nbsp; STATUTORY DECLARATIONS VERIFIED CLEAR</div>', unsafe_allow_html=True)
    else:
        n = len(issues)
        st.markdown(
            f'<div class="badge-fail">🚨 &nbsp; ENFORCEMENT ACTION REQUIRED &nbsp;·&nbsp; {n} NON-COMPLIANCE ITEM{"S" if n != 1 else ""}</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Officer Executive Briefing ────────────────────────────────────────────
    st.markdown("### 📋 Official Inspection Briefing")
    bcol1, bcol2, bcol3, bcol4 = st.columns(4)
    bcol1.metric("Inspection Status", "PASS" if is_compliant else "ACTION REQUIRED", delta="Clear" if is_compliant else f"{len(issues)} Issues", delta_color="normal" if is_compliant else "inverse")
    bcol2.metric("Mandatory Fields", f"{10 - len(missing)} / 10", delta=f"-{len(missing)} Missing" if missing else "Complete", delta_color="normal" if not missing else "inverse")
    
    font_compliance = extracted.get("font_compliance", {})
    font_status = font_compliance.get("status", "N/A")
    bcol3.metric("Rule 9 Font Height", "COMPLIANT" if font_status == "PASS" else ("SUB-STANDARD" if font_status == "FAIL" else "N/A"), delta="OK" if font_status == "PASS" else ("Deficit" if font_status == "FAIL" else None), delta_color="normal" if font_status == "PASS" else "inverse")
    bcol4.metric("Panels Audited", f"{panels_count} panel{'s' if panels_count != 1 else ''}", delta=f"{len(extracted.get('additives', []))} additives" if extracted.get('additives') else None)

    # ── Officer Action Cards & Violations ──────────────────────────────────────
    if issues:
        st.markdown("#### 🚨 Statutory Non-Compliance & Recommended Officer Actions")
        for i, issue in enumerate(issues, 1):
            sev = issue.get("severity", "warning")
            icon = "🔴" if sev == "critical" else "🟡" if sev == "warning" else "🔵"
            css_class = "issue-card" + (" warning" if sev == "warning" else " info" if sev == "info" else "")
            
            title = issue.get("title") or issue.get("detail", f"Statutory Non-Compliance #{i}")
            detail = issue.get("detail", "")
            action = issue.get("officer_action") or issue.get("recommendation", "Direct manufacturer to rectify declaration.")
            regulation = issue.get("regulation_id", "Legal Metrology Act, 2009 / FSSAI Regulations")
            penalty = issue.get("penalty_provision", "")

            penalty_html = f"""
            <div style="background: rgba(239, 83, 80, 0.12); border-left: 3px solid #ef5350; padding: 6px 10px; border-radius: 4px; margin-top: 8px;">
                <span style="color: #ff8a80; font-size: 0.85rem; font-weight: 600;">⚖️ Compoundable Penalty / Legal Provision:</span><br>
                <span style="color: #ffebee; font-size: 0.82rem;">{penalty}</span>
            </div>
            """ if penalty else ""

            st.markdown(
                f"""
                <div class="{css_class}" style="margin-bottom: 1rem; padding: 1rem 1.2rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;">
                        <span style="font-size: 1.05rem; font-weight: 700; color: #ffffff;">{icon} {title}</span>
                        <span style="font-size: 0.75rem; text-transform: uppercase; padding: 2px 8px; border-radius: 4px; background: rgba(255,255,255,0.1); color: #b0c9e0;">{sev}</span>
                    </div>
                    <div style="font-size: 0.92rem; color: #d1e2f2; margin-bottom: 0.5rem; line-height: 1.4;">
                        <strong>Observation:</strong> {detail}
                    </div>
                    <div style="background: rgba(46, 204, 113, 0.12); border-left: 3px solid #2ecc71; padding: 6px 10px; border-radius: 4px; margin-top: 6px;">
                        <span style="color: #2ecc71; font-size: 0.85rem; font-weight: 600;">👮 Recommended Officer Action:</span><br>
                        <span style="color: #e8f8f0; font-size: 0.88rem;">{action}</span>
                    </div>
                    <div style="margin-top: 8px; font-size: 0.8rem; color: #90caf9;">
                        📜 <strong>Statutory Authority:</strong> <code>{regulation}</code>
                    </div>
                    {penalty_html}
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.success("✅ **All statutory declarations are verified and compliant with Legal Metrology (Packaged Commodities) Rules, 2011 and FSSAI Packaging Regulations.**")

    # ── Extracted Label Declarations (Officer Field Checklist) ─────────────────
    with st.expander("🔍 Verified Label Declarations (Official Field Record)", expanded=False):
        field_map = {
            "mrp":               ("Maximum Retail Price (MRP)", lambda v: f"₹ {v}"),
            "net_quantity":      ("Net Quantity",               lambda v: v.get("raw", "—") if v else "—"),
            "mfg_date":          ("Date of Manufacture",        lambda v: v),
            "expiry_date":       ("Best Before / Expiry",       lambda v: v),
            "fssai_license":     ("FSSAI 14-Digit License",     lambda v: v),
            "ingredients":       ("Ingredients List",           lambda v: f"{len(v)} ingredients identified" if isinstance(v, list) and v else ("Declared" if v else "Missing")),
            "manufacturer":      ("Manufacturer / Packer",      lambda v: v),
            "country_of_origin": ("Country of Origin",          lambda v: v),
            "consumer_care":     ("Consumer Care Helpline",     lambda v: v),
            "allergens":         ("Allergen Warning",           lambda v: ", ".join(v) if isinstance(v, list) else v),
        }

        meta_fields = extracted.get("_field_metadata", {})
        for key, (label, fmt) in field_map.items():
            val = extracted.get(key)
            panel_badge = ""
            if panels_count > 1 and key in meta_fields and meta_fields[key]:
                pname = meta_fields[key].get("panel_name")
                if pname:
                    panel_badge = f' &nbsp;<span style="font-size: 0.72rem; background: #22374e; color: #8ec8f6; padding: 2px 7px; border-radius: 4px; font-weight: 500;">📍 {pname}</span>'

            if val:
                formatted = fmt(val)
                st.markdown(
                    f'<div class="field-card">'
                    f'<span class="field-label">{label}{panel_badge}</span>'
                    f'<span class="field-value">✅ &nbsp; {formatted}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            else:
                missing_flag = " ⚠️ MANDATORY OMISSION" if key in missing else ""
                st.markdown(
                    f'<div class="field-card">'
                    f'<span class="field-label">{label}</span>'
                    f'<span class="field-missing">❌ &nbsp; Not Declared on Package{missing_flag}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    # ── Rule 9 Font Height Verification ───────────────────────────────────────
    if font_compliance and font_compliance.get("status") in ("PASS", "FAIL"):
        is_font_pass = font_compliance.get("is_compliant", True)
        font_status_badge = "✅ COMPLIANT" if is_font_pass else "❌ SUB-STANDARD (RULE 9 DEFICIT)"
        est_mm = font_compliance.get("est_height_mm", 0)
        req_mm = font_compliance.get("required_min_mm", 0)
        ratio_pct = font_compliance.get("font_ratio_pdp_pct", 0)

        with st.expander(f"📏 Rule 9 Numeral Height Audit — {font_status_badge}", expanded=not is_font_pass):
            fc1, fc2, fc3 = st.columns(3)
            fc1.metric("Measured Height (Est.)", f"{est_mm} mm", delta=f"{est_mm - req_mm:+.1f} mm vs statutory min")
            fc2.metric("Statutory Min (Rule 9 Table 1)", f"{req_mm} mm")
            fc3.metric("Principal Display Panel Ratio", f"{ratio_pct}%")
            if not is_font_pass:
                st.error(
                    f"⚠️ **Statutory Violation**: Numeral height (~{est_mm} mm) falls below Legal Metrology Rule 9 Table 1 "
                    f"minimum of {req_mm} mm for net quantity {font_compliance.get('net_quantity_val')} {font_compliance.get('unit')}."
                )
            else:
                st.success(f"Numeral height satisfies Legal Metrology Rule 9(1) Table 1 (Statutory minimum: {req_mm} mm).")

    # ── Ingredients & Additives ───────────────────────────────────────────────
    ingredients = extracted.get("ingredients", [])
    additives = extracted.get("additives", [])
    allergens = extracted.get("allergens", [])

    with st.expander(f"🧪 Food Composition & Additives ({len(ingredients)} ingredients, {len(additives)} additives)", expanded=False):
        if ingredients:
            st.markdown("##### 🥗 Ingredients Declared:")
            for i, ing in enumerate(ingredients, 1):
                st.markdown(f"**{i}.** {ing}")
        else:
            st.info("No ingredient list detected on this package.")

        if allergens:
            st.warning("⚠️ **Allergens Declared:** " + ", ".join(allergens))

        if additives:
            st.markdown("##### ⚗️ Additives & INS Numbers:")
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

    # ── Generate Official Field Inspection Report ─────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    report_lines = [
        "=" * 65,
        "   GOVERNMENT OF INDIA — STATUTORY FIELD INSPECTION REPORT",
        "     Legal Metrology & Food Safety Compliance Enforcement",
        "=" * 65,
        f"Inspection Scan ID : {result.get('scan_id', 'N/A')}",
        f"Commodity Category : {category}",
        f"Inspection Verdict : {'PASS (COMPLIANT)' if is_compliant else 'NON-COMPLIANT (ACTION REQUIRED)'}",
        f"Violations Count   : {len(issues)}",
        "-" * 65,
        "1. SUMMARY OF MANDATORY DECLARATIONS:",
    ]
    for key, (label, fmt) in field_map.items():
        v = extracted.get(key)
        val_str = fmt(v) if v else "NOT DECLARED [VIOLATION]"
        report_lines.append(f"  - {label:<30}: {val_str}")
    
    if font_compliance:
        report_lines.append("-" * 65)
        report_lines.append("2. RULE 9 NUMERAL HEIGHT AUDIT:")
        report_lines.append(f"  - Status                  : {font_compliance.get('status')}")
        report_lines.append(f"  - Measured Height (Est.)   : {font_compliance.get('est_height_mm')} mm")
        report_lines.append(f"  - Statutory Requirement   : {font_compliance.get('required_min_mm')} mm")

    if issues:
        report_lines.append("-" * 65)
        report_lines.append("3. STATUTORY VIOLATIONS & RECOMMENDED OFFICER ACTIONS:")
        for idx, iss in enumerate(issues, 1):
            report_lines.append(f"\n[Item {idx}] {iss.get('title', 'Violation')}")
            report_lines.append(f"  Observation       : {iss.get('detail', '')}")
            report_lines.append(f"  Officer Action    : {iss.get('officer_action', iss.get('recommendation', ''))}")
            report_lines.append(f"  Statutory Section : {iss.get('regulation_id', '')}")
            if iss.get("penalty_provision"):
                report_lines.append(f"  Penalty Clause    : {iss.get('penalty_provision')}")

    report_lines.extend([
        "\n" + "=" * 65,
        "Inspecting Officer Signature: _______________________",
        "Designation                : Food Safety Officer / Inspector (Legal Metrology)",
        "=" * 65,
    ])
    full_report_text = "\n".join(report_lines)

    # ── Official Report Actions (Direct Browser Download & Inline Preview) ───
    st.markdown("#### 📄 Official Statutory Field Inspection Report")
    
    try:
        from modules.report_generator import generate_pdf_report
        pdf_bytes = generate_pdf_report(
            scan_result=result,
            product_category=category,
        )
        b64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
        scan_id_short = result.get("scan_id", "scan")[:8]
        filename_pdf = f"SurakshaScan_Report_{scan_id_short}.pdf"

        # Direct Browser Download via Data URI (bypasses IDM network hooks)
        btn_cols = st.columns([1.5, 1.2, 1])
        with btn_cols[0]:
            st.markdown(
                f"""
                <a href="data:application/pdf;base64,{b64_pdf}" download="{filename_pdf}" style="
                    display: block;
                    width: 100%;
                    text-align: center;
                    background: linear-gradient(135deg, #1e88e5, #1565c0);
                    color: #ffffff !important;
                    font-weight: 600;
                    font-size: 0.88rem;
                    padding: 0.6rem 0.8rem;
                    border-radius: 8px;
                    text-decoration: none !important;
                    box-shadow: 0 2px 8px rgba(21,101,192,0.35);
                    cursor: pointer;
                ">
                    📥 Direct Browser Download
                </a>
                """,
                unsafe_allow_html=True,
            )
        with btn_cols[1]:
            st.markdown(
                f"""
                <a href="data:application/pdf;base64,{b64_pdf}" target="_blank" style="
                    display: block;
                    width: 100%;
                    text-align: center;
                    background: #22374e;
                    color: #90caf9 !important;
                    font-weight: 600;
                    font-size: 0.88rem;
                    padding: 0.6rem 0.8rem;
                    border-radius: 8px;
                    text-decoration: none !important;
                    border: 1px solid #355373;
                    cursor: pointer;
                ">
                    🖨️ Open / Print in New Tab
                </a>
                """,
                unsafe_allow_html=True,
            )
        with btn_cols[2]:
            st.download_button(
                label="📄 Plain Text (.txt)",
                data=full_report_text,
                file_name=f"Inspection_Report_{scan_id_short}.txt",
                mime="text/plain",
                use_container_width=True,
            )

        # Embedded Interactive PDF Viewer
        with st.expander("👁️ Preview Statutory Inspection Report (Interactive In-App Viewer)", expanded=True):
            st.markdown(
                f"""
                <iframe src="data:application/pdf;base64,{b64_pdf}#toolbar=1" width="100%" height="560" type="application/pdf" style="border: 1px solid #2e3d50; border-radius: 8px; background: white;">
                    <p>Your browser does not support inline PDFs. Use the Direct Browser Download button above.</p>
                </iframe>
                """,
                unsafe_allow_html=True,
            )

    except Exception as ex:
        st.warning(f"Could not generate PDF: {ex}")
        st.download_button(
            label="📄 Download Text Summary (.txt)",
            data=full_report_text,
            file_name=f"Inspection_Report_{result.get('scan_id', 'scan')[:8]}.txt",
            mime="text/plain",
            use_container_width=True,
        )

    # ── Digital Panchnama Archive / RAG Dossier ───────────────────────────────
    rag_payload = result.get("rag_payload")
    if rag_payload:
        with st.expander("📂 Statutory Evidence Dossier (Digital Panchnama Archive)", expanded=False):
            st.markdown("*Normalized JSON evidence compiled for regulatory enforcement:*")
            st.json(rag_payload)

    # ── Debug / Raw Response ──────────────────────────────────────────────────
    with st.expander("🛠️ Raw Inspection JSON (Officer / Debug View)"):
        st.json(result)

    # ── Scan Footer Metadata ──────────────────────────────────────────────────
    st.caption(
        f"Scan ID: `{result.get('scan_id', '—')}`  |  "
        f"Detections: {result.get('ocr_detections_count', 0)}  |  "
        f"Category: {category}"
    )
