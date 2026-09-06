import cv2
import numpy as np
from pathlib import Path
from typing import Union


class PackagingPreprocessor:
    """
    Advanced computer vision preprocessing tailored for consumer packaging:
    - Specular anti-glare reflection mitigation via LAB CLAHE + threshold inpainting
    - Wrinkle and fold suppression using edge-preserving bilateral filtering
    - Cylindrical surface unrolling/dewarping for cans and bottles
    """

    @staticmethod
    def anti_glare_clahe(img: np.ndarray, clip_limit: float = 2.5, tile_grid: tuple = (8, 8)) -> np.ndarray:
        """
        Suppresses bright light reflections (specular highlights) using LAB color space
        and CLAHE on the luminance channel, combined with highlight inpainting.
        """
        if img is None or img.size == 0:
            return img

        # 1. Specular highlight inpainting (only if significant highlights exist)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
        _, highlight_mask = cv2.threshold(gray, 248, 255, cv2.THRESH_BINARY)
        nonzero = cv2.countNonZero(highlight_mask)

        if 50 < nonzero < (img.shape[0] * img.shape[1] * 0.10):
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            dilated_mask = cv2.dilate(highlight_mask, kernel, iterations=1)
            inpainted = cv2.inpaint(img, dilated_mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)
        else:
            inpainted = img

        # 2. LAB CLAHE contrast enhancement
        if len(inpainted.shape) == 3:
            lab = cv2.cvtColor(inpainted, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid)
            cl = clahe.apply(l)
            enhanced_lab = cv2.merge((cl, a, b))
            return cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
        else:
            clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid)
            return clahe.apply(inpainted)

    @staticmethod
    def dewrinkle_bilateral(img: np.ndarray, d: int = 5, sigma_color: float = 40.0, sigma_space: float = 40.0) -> np.ndarray:
        """
        Smoothes plastic pouch crinkles and foil micro-shadows while preserving crisp text edges.
        """
        if img is None or img.size == 0:
            return img
        return cv2.bilateralFilter(img, d, sigma_color, sigma_space)

    @staticmethod
    def cylindrical_dewarp(img: np.ndarray, radius_factor: float = 2.0) -> np.ndarray:
        """
        Unrolls text distorted across curved cylindrical surfaces (cans, plastic jars, bottles).
        """
        if img is None or img.size == 0:
            return img

        h, w = img.shape[:2]
        r = w * radius_factor
        map_x = np.zeros((h, w), dtype=np.float32)
        map_y = np.zeros((h, w), dtype=np.float32)

        cx = w / 2.0
        for x in range(w):
            dx = (x - cx) / r
            if abs(dx) > 1.0:
                dx = np.sign(dx)
            orig_x = cx + r * np.arcsin(dx)
            map_x[:, x] = np.clip(orig_x, 0, w - 1)

        for y in range(h):
            map_y[y, :] = y

        return cv2.remap(img, map_x, map_y, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

    @classmethod
    def preprocess_image(
        cls,
        image_input: Union[str, Path, bytes, np.ndarray],
        apply_anti_glare: bool = True,
        apply_dewrinkle: bool = True,
        apply_dewarp: bool = False
    ) -> np.ndarray:
        """
        Full packaging preprocessing pipeline. Accepts file path, raw bytes, or numpy array.
        Returns processed BGR image array.
        """
        if isinstance(image_input, (str, Path)):
            img = cv2.imread(str(image_input))
            if img is None:
                raise ValueError(f"Could not load image from path: {image_input}")
        elif isinstance(image_input, bytes):
            nparr = np.frombuffer(image_input, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                raise ValueError("Could not decode image from provided bytes.")
        elif isinstance(image_input, np.ndarray):
            img = image_input.copy()
        else:
            raise TypeError(f"Unsupported image input type: {type(image_input)}")

        # Sequential preprocessing
        if apply_dewarp:
            img = cls.cylindrical_dewarp(img)
        if apply_anti_glare:
            img = cls.anti_glare_clahe(img)
        if apply_dewrinkle:
            img = cls.dewrinkle_bilateral(img)

        return img
