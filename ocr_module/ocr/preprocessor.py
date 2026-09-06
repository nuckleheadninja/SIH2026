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

    @staticmethod
    def enhance_dot_matrix(img: np.ndarray) -> np.ndarray:
        """
        Connects disjoint ink dots in continuous-inkjet (CIJ) or dot-matrix printed
        date and batch stamps (e.g. on crimped pouch seals, bottle caps, or can rims).
        Uses directional horizontal dilation to bridge ink dot gaps into cohesive strokes.
        """
        if img is None or img.size == 0:
            return img
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 1))
        return cv2.dilate(img, kernel, iterations=1)

    @staticmethod
    def auto_orient_packaging(img: np.ndarray) -> np.ndarray:
        """
        Arbitrates the upright orientation of a food package capture.
        Mobile phone photos frequently capture pouches and sachets in landscape
        (rotated 90° or 270°), causing horizontal text detectors to miss lines.
        Uses a fast thumbnail probe to detect and correct orientation.
        """
        if img is None or img.size == 0:
            return img

        _run_ocr = None
        try:
            from modules.ocr_engine import _run_paddle as _run_ocr
        except ImportError:
            try:
                from ocr_module.ocr.text_detector import TextDetector
                _td = TextDetector()
                _td._init_engines()
                if _td._paddle_ocr:
                    from modules.ocr_engine import _run_paddle
                    _run_ocr = _run_paddle
            except Exception:
                pass

        if _run_ocr is None:
            return img

        h, w = img.shape[:2]
        scale = 480.0 / max(h, w)
        probe = cv2.resize(img, (max(1, int(round(w * scale))), max(1, int(round(h * scale)))))

        kw_set = {
            "mrp", "rs", "inr", "net", "wt", "weight", "qty", "fssai", "lic",
            "mfd", "mfg", "exp", "batch", "ingredients", "nutrition", "india",
            "consumer", "use by", "best before", "product"
        }

        def _score(dets):
            if not dets:
                return 0, 0, 0.0
            full = " ".join(d.get("text", "").lower() for d in dets)
            kw = sum(1 for k in kw_set if k in full)
            hc = sum(1 for d in dets if d.get("confidence", 0.0) >= 0.70)
            avg = float(np.mean([d.get("confidence", 0.0) for d in dets]))
            return kw, hc, (kw * 10.0) + (hc * 1.0) + (avg * 5.0)

        # 1. Probe 0°
        d0 = _run_ocr(probe)
        kw0, hc0, sc0 = _score(d0)
        if kw0 >= 4 and hc0 >= 10:
            return img

        # 2. Probe 90° CW
        probe_90 = cv2.rotate(probe, cv2.ROTATE_90_CLOCKWISE)
        d90 = _run_ocr(probe_90)
        kw90, hc90, sc90 = _score(d90)
        if sc90 > sc0 * 1.3 and sc90 > 15:
            return cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)

        # 3. Probe 270° CW
        probe_270 = cv2.rotate(probe, cv2.ROTATE_90_COUNTERCLOCKWISE)
        d270 = _run_ocr(probe_270)
        kw270, hc270, sc270 = _score(d270)
        if sc270 > sc0 * 1.3 and sc270 > sc90 and sc270 > 15:
            return cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)

        # 4. Probe 180°
        if sc0 < 10:
            probe_180 = cv2.rotate(probe, cv2.ROTATE_180)
            d180 = _run_ocr(probe_180)
            kw180, hc180, sc180 = _score(d180)
            if sc180 > sc0 * 1.4 and sc180 > 15:
                return cv2.rotate(img, cv2.ROTATE_180)

        return img

    @classmethod
    def preprocess_image(
        cls,
        image_input: Union[str, Path, bytes, np.ndarray],
        apply_anti_glare: bool = True,
        apply_dewrinkle: bool = True,
        apply_dot_matrix_enhancement: bool = True,
        apply_dewarp: bool = False,
        apply_auto_orient: bool = True,
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
        if apply_auto_orient:
            img = cls.auto_orient_packaging(img)
        if apply_dewarp:
            img = cls.cylindrical_dewarp(img)
        if apply_anti_glare:
            img = cls.anti_glare_clahe(img)
        if apply_dewrinkle:
            img = cls.dewrinkle_bilateral(img)
        if apply_dot_matrix_enhancement:
            img = cls.enhance_dot_matrix(img)

        return img
