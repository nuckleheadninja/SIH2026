"""Unit tests for preprocessing operations and pipeline."""
import cv2
import numpy as np
from preprocessing.resize import resize_image
from preprocessing.enhancement import apply_clahe, apply_denoise, apply_sharpening
from preprocessing.pipeline import PreprocessingPipeline
from models.image_schema import QualityReport

def test_resize_image():
    img = np.zeros((2000, 3000, 3), dtype=np.uint8)
    resized, scale = resize_image(img, target_long_side=1500)
    assert scale == 0.5
    assert resized.shape[1] == 1500
    assert resized.shape[0] == 1000

def test_enhancement_functions():
    img = np.ones((200, 200, 3), dtype=np.uint8) * 100
    clahe_img = apply_clahe(img)
    assert clahe_img.shape == img.shape

    denoised_img = apply_denoise(img)
    assert denoised_img.shape == img.shape

    sharpened_img = apply_sharpening(img)
    assert sharpened_img.shape == img.shape

def test_preprocessing_pipeline_auto():
    img = np.ones((500, 500, 3), dtype=np.uint8) * 128
    quality = QualityReport(
        width=500,
        height=500,
        blur_score=150.0,
        brightness=128.0,
        contrast=20.0,  # Low contrast trigger
        quality_status="warning",
        warnings=["Low contrast"]
    )
    pipeline = PreprocessingPipeline({"preprocessing": {"profile": "auto"}})
    proc_img, profile_used, ops = pipeline.process(img, quality)

    assert profile_used == "low_contrast"
    assert "clahe" in ops
    assert "sharpening" in ops
