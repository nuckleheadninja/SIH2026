"""Synthetic product label generator for testing the OCR + Layout Analysis pipeline."""
import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def generate_sample_label(output_path: str = "input/product_001.jpg", width: int = 1200, height: int = 800) -> str:
    """Generates a realistic synthetic packaged food label image."""
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    # Create background container/card
    img = Image.new("RGB", (width, height), color=(245, 247, 250))
    draw = ImageDraw.Draw(img)

    # Outer product package border
    draw.rectangle([50, 40, width - 50, height - 40], outline=(40, 60, 90), width=4)
    draw.rectangle([60, 50, width - 60, height - 60], fill=(255, 255, 255), outline=(200, 200, 200), width=2)

    try:
        title_font = ImageFont.truetype("arial.ttf", 36)
        body_font = ImageFont.truetype("arial.ttf", 24)
        small_font = ImageFont.truetype("arial.ttf", 18)
    except IOError:
        title_font = body_font = small_font = ImageFont.load_default()

    # Product Title (Top-Center)
    draw.text((width // 2 - 180, 80), "ORGANIC OAT CRUNCH", fill=(20, 80, 160), font=title_font)
    draw.text((width // 2 - 120, 130), "WHOLE GRAIN CEREAL", fill=(80, 80, 80), font=body_font)

    # Ingredients (Middle-Left)
    draw.text((90, 220), "INGREDIENTS:", fill=(0, 0, 0), font=body_font)
    draw.text((90, 255), "Rolled Oats (65%), Honey, Almonds, Rice Crispies,", fill=(50, 50, 50), font=small_font)
    draw.text((90, 280), "Vegetable Oil, Natural Vanilla Flavor.", fill=(50, 50, 50), font=small_font)

    # Nutrition Table Box (Middle-Right)
    draw.rectangle([width - 450, 210, width - 90, 450], outline=(0, 0, 0), width=2)
    draw.text((width - 430, 220), "NUTRITIONAL INFORMATION", fill=(0, 0, 0), font=body_font)
    draw.text((width - 430, 260), "Energy: 450 kcal", fill=(30, 30, 30), font=small_font)
    draw.text((width - 430, 290), "Total Fat: 14.5 g", fill=(30, 30, 30), font=small_font)
    draw.text((width - 430, 320), "Protein: 10.2 g", fill=(30, 30, 30), font=small_font)
    draw.text((width - 430, 350), "Total Sugars: 12.0 g", fill=(30, 30, 30), font=small_font)
    draw.text((width - 430, 380), "Sodium: 180 mg", fill=(30, 30, 30), font=small_font)

    # Legal Metrology Declarations (Bottom-Left & Bottom-Right)
    draw.text((90, 500), "MFG DATE: 10/2025", fill=(0, 0, 0), font=body_font)
    draw.text((90, 540), "BATCH NO: B2025-OAT-99", fill=(0, 0, 0), font=body_font)
    draw.text((90, 580), "Lic. No. 10015022003841", fill=(0, 0, 0), font=body_font)
    draw.text((90, 620), "Manufactured by: ABC Foods Pvt Ltd, Mumbai - 400001", fill=(60, 60, 60), font=small_font)

    # Net Quantity & MRP (Bottom-Right)
    draw.text((width - 450, 500), "Net Qty: 500 g", fill=(0, 0, 0), font=body_font)
    draw.text((width - 450, 550), "M.R.P. RS 120.00", fill=(0, 0, 0), font=title_font)
    draw.text((width - 450, 600), "(Incl. of all taxes)", fill=(80, 80, 80), font=small_font)

    # Save image
    cv2_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    cv2.imwrite(output_path, cv2_img)
    return output_path

if __name__ == "__main__":
    path = generate_sample_label()
    print(f"Generated sample label image at: {path}")
