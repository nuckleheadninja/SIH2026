"""Image loader and saver utilities."""
import os
import cv2
import numpy as np

def load_image(image_path: str) -> np.ndarray:
    """Reads image file into BGR numpy ndarray using OpenCV safely on Windows."""
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"File not found: {image_path}")
    img = cv2.imread(image_path)
    if img is None:
        try:
            stream = np.fromfile(image_path, dtype=np.uint8)
            img = cv2.imdecode(stream, cv2.IMREAD_COLOR)
        except Exception:
            img = None
    if img is None:
        raise ValueError(f"Unable to read or decode image file: {image_path}")
    return img

def save_image(image: np.ndarray, output_path: str) -> str:
    """Saves image ndarray to output_path, creating directories if needed."""
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    ext = os.path.splitext(output_path)[1]
    success, buf = cv2.imencode(ext if ext else '.jpg', image)
    if success:
        buf.tofile(output_path)
    else:
        success = cv2.imwrite(output_path, image)
        if not success:
            raise IOError(f"Failed to write image to: {output_path}")
    return output_path
