"""Unit tests for image validation and quality inspection."""
import os
import cv2
import pytest
import numpy as np
from preprocessing.validation import validate_image

@pytest.fixture
def sample_valid_image(tmp_path):
    img_path = str(tmp_path / "valid_label.jpg")
    img = np.ones((600, 800, 3), dtype=np.uint8) * 200
    cv2.putText(img, "TEST LABEL", (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    cv2.imwrite(img_path, img)
    return img_path

@pytest.fixture
def sample_tiny_image(tmp_path):
    img_path = str(tmp_path / "tiny_label.jpg")
    img = np.ones((50, 50, 3), dtype=np.uint8) * 128
    cv2.imwrite(img_path, img)
    return img_path

def test_validate_valid_image(sample_valid_image):
    success, metadata, quality, img = validate_image(sample_valid_image)
    assert success is True
    assert metadata.width == 800
    assert metadata.height == 600
    assert metadata.aspect_ratio == 1.3333
    assert quality.quality_status in ["acceptable", "warning"]

def test_validate_nonexistent_image():
    with pytest.raises(FileNotFoundError):
        validate_image("nonexistent_path_12345.jpg")

def test_validate_tiny_image(sample_tiny_image):
    success, metadata, quality, img = validate_image(sample_tiny_image)
    assert success is True
    assert any("Low image resolution" in w for w in quality.warnings)
    assert quality.quality_status == "warning"
