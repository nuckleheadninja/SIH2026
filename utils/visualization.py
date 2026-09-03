"""OCR overlay visualization renderer supporting polygon bounding boxes, confidence %, and spatial region tags."""
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from typing import List, Dict, Any
from models.ocr_schema import OCRBlockModel


def draw_ocr_visualization(image: np.ndarray, blocks: List[OCRBlockModel], config: Dict[str, Any] = None) -> np.ndarray:
    """
    Renders bounding polygons, block ID, raw text, confidence score %, and spatial region labels onto a copy of the image.
    Uses PIL for robust unicode/Hindi character rendering.
    Returns annotated BGR numpy ndarray.
    """
    vis_img = image.copy()
    height, width = vis_img.shape[:2]

    # Convert BGR OpenCV image to PIL Image for high-quality text overlay
    pil_img = Image.fromarray(cv2.cvtColor(vis_img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_img)

    # Use default PIL font or fallback
    try:
        font = ImageFont.truetype("arial.ttf", size=max(12, int(height * 0.018)))
    except IOError:
        font = ImageFont.load_default()

    # Draw 3x3 Grid Guidelines softly for layout visualization
    draw_grid = True
    if draw_grid:
        grid_color = (200, 200, 200, 100)
        draw.line([(int(width * 0.3333), 0), (int(width * 0.3333), height)], fill="gray", width=1)
        draw.line([(int(width * 0.6666), 0), (int(width * 0.6666), height)], fill="gray", width=1)
        draw.line([(0, int(height * 0.3333)), (width, int(height * 0.3333))], fill="gray", width=1)
        draw.line([(0, int(height * 0.6666)), (width, int(height * 0.6666))], fill="gray", width=1)

    for block in blocks:
        # Extract polygon points
        poly_pts = [(pt[0], pt[1]) for pt in block.polygon]

        # Select color based on confidence level
        if block.confidence_level == "high":
            color = (0, 200, 0)      # Green
        elif block.confidence_level == "medium":
            color = (255, 165, 0)    # Orange
        else:
            color = (220, 20, 60)    # Red

        # Draw polygon outline
        draw.polygon(poly_pts, outline=color, width=2)

        # Label content
        conf_pct = int(round(block.confidence * 100))
        label_text = f"[{block.layout.region}] {block.id}: {block.raw_text} ({conf_pct}%)"

        # Text position (top-left of bounding box)
        x1, y1 = block.bbox[0], block.bbox[1]
        text_y = max(0, y1 - 20)

        # Draw text background box
        bbox_text = draw.textbbox((x1, text_y), label_text, font=font)
        draw.rectangle(bbox_text, fill=(0, 0, 0, 180))
        draw.text((x1, text_y), label_text, fill=(255, 255, 255), font=font)

    # Convert back to OpenCV BGR image
    annotated_bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    return annotated_bgr
