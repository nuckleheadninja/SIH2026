"""
camera_utils.py — Utilities for fetching high-resolution frames from external IP / WiFi cameras

Supports:
- IP Webcam (Android) via /photoaf.jpg (Full-sensor photo with autofocus), /photo.jpg, /shot.jpg
- Flashlight / Torch control (/enabletorch, /disabletorch)
- DroidCam (Android / iOS) via /video, /mjpegfeed
- Generic RTSP / ONVIF / MJPEG network streams
- Direct HTTP snapshots
"""

import io
import socket
from urllib.parse import urlparse
from typing import Dict, Any

import cv2
import httpx
from PIL import Image


def is_host_reachable(url: str, timeout: float = 2.0) -> bool:
    """
    Fast pre-flight check to verify if the camera IP and port are reachable
    via TCP before attempting long-blocking operations.
    """
    try:
        norm_url = url if "://" in url else f"http://{url}"
        parsed = urlparse(norm_url)
        host = parsed.hostname
        if not host:
            return False
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


def normalize_ip_cam_url(url: str) -> str:
    """Ensures URL has a proper scheme and stripped whitespace."""
    url = url.strip()
    if not url:
        return ""
    if not url.startswith(("http://", "https://", "rtsp://")):
        url = f"http://{url}"
    return url


def grab_opencv_frame(stream_url: str) -> bytes:
    """
    Captures a single frame from an RTSP, MJPEG, or live video stream using OpenCV.
    Flushes stream buffer to ensure the freshest frame is captured.
    """
    cap = cv2.VideoCapture(stream_url)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video stream at {stream_url}")
    try:
        ret, frame = False, None
        for _ in range(3):
            ret, frame = cap.read()
            if not ret:
                break
        if not ret or frame is None:
            raise RuntimeError(f"Failed to read a valid frame from {stream_url}")

        success, encoded = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
        if not success:
            raise RuntimeError("Failed to compress frame to JPEG.")
        return encoded.tobytes()
    finally:
        cap.release()


def set_camera_torch(url: str, enable: bool = True) -> bool:
    """Toggles the phone flashlight if the IP camera app supports it (e.g. IP Webcam)."""
    norm_url = normalize_ip_cam_url(url).rstrip("/")
    endpoint = f"{norm_url}/enabletorch" if enable else f"{norm_url}/disabletorch"
    try:
        resp = httpx.get(endpoint, timeout=3.0)
        return resp.status_code == 200
    except Exception:
        return False


def trigger_camera_autofocus(url: str) -> bool:
    """Triggers focus on phone camera if supported."""
    norm_url = normalize_ip_cam_url(url).rstrip("/")
    try:
        resp = httpx.get(f"{norm_url}/focus", timeout=3.0)
        return resp.status_code == 200
    except Exception:
        return False


def fetch_ip_camera_frame(url: str, autofocus: bool = True, timeout: float = 10.0) -> bytes:
    """
    Fetches a high-resolution frame from an IP camera.
    Prioritizes full-sensor still snapshots (/photoaf.jpg, /photo.jpg) over video streams
    because phone camera sensors capture at full resolution (e.g. 1080p, 12MP-48MP)
    which dramatically improves OCR accuracy for fine packaging text.
    """
    norm_url = normalize_ip_cam_url(url)
    if not norm_url:
        raise ValueError("Please provide a valid IP camera URL or IP:port.")

    # 1. Fast pre-flight reachability check
    if not is_host_reachable(norm_url, timeout=2.5):
        parsed = urlparse(norm_url)
        host = parsed.hostname or "the camera IP"
        port = parsed.port or 8080
        raise ConnectionError(
            f"Cannot reach camera at '{host}:{port}'.\n\n"
            "Troubleshooting Checklist:\n"
            "1. Ensure your phone and PC are connected to the SAME Wi-Fi network (or laptop connected to phone hotspot).\n"
            "2. Confirm the IP camera app is running and 'Start server' is active.\n"
            "3. Verify the IP and port displayed on your phone screen."
        )

    # 2. RTSP or explicit stream endpoints
    if norm_url.startswith("rtsp://") or any(ext in norm_url.lower() for ext in ["/video", "/mjpeg", "/mjpegfeed"]):
        return grab_opencv_frame(norm_url)

    # 3. Snapshot candidate selection
    if any(norm_url.lower().endswith(ext) for ext in [".jpg", ".jpeg"]):
        candidate_urls = [norm_url]
    else:
        base = norm_url.rstrip("/")
        candidate_urls = []
        if autofocus:
            # /photoaf.jpg triggers camera autofocus then snaps a high-res photo
            candidate_urls.append(f"{base}/photoaf.jpg")
        candidate_urls.append(f"{base}/photo.jpg")
        candidate_urls.append(f"{base}/shot.jpg")
        candidate_urls.append(f"{base}/video")

    client = httpx.Client(timeout=timeout, follow_redirects=True)
    last_err = None

    for target in candidate_urls:
        if "/video" in target:
            try:
                return grab_opencv_frame(target)
            except Exception as e:
                last_err = e
                continue

        try:
            resp = client.get(target)
            if resp.status_code == 200 and resp.content and len(resp.content) > 1000:
                # Verify that it is a valid, readable image
                img = Image.open(io.BytesIO(resp.content))
                img.verify()
                return resp.content
        except Exception as e:
            last_err = e
            continue

    # Fallback to OpenCV if HTTP snapshot endpoints didn't work
    try:
        return grab_opencv_frame(norm_url)
    except Exception as e:
        raise RuntimeError(
            f"Connected to camera at '{norm_url}', but could not capture a frame.\n"
            f"Details: {e or last_err}"
        )


def get_image_metadata(img_bytes: bytes) -> Dict[str, Any]:
    """Extracts resolution, megapixels, size, and OCR-readiness quality rating."""
    img = Image.open(io.BytesIO(img_bytes))
    w, h = img.size
    mp = round((w * h) / 1_000_000, 2)
    kb = round(len(img_bytes) / 1024, 1)

    if mp >= 4.0:
        quality_label = "Ultra High Res (4K / 4MP+) — Ideal for fine print"
        quality_color = "#27ae60"
    elif mp >= 1.5:
        quality_label = "Full HD (1080p) — Great clarity for food labels"
        quality_color = "#2980b9"
    elif mp >= 0.8:
        quality_label = "Standard HD (720p) — Moderate detail"
        quality_color = "#f39c12"
    else:
        quality_label = "Low Resolution (640x480) — Small fonts may be blurry"
        quality_color = "#e74c3c"

    return {
        "width": w,
        "height": h,
        "megapixels": mp,
        "size_kb": kb,
        "format": img.format or "JPEG",
        "quality_label": quality_label,
        "quality_color": quality_color,
    }
