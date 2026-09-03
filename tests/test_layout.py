"""Unit tests for layout geometry, relative coordinate math, and region classification."""
from layout.region import classify_region, compute_relative_coordinates
from layout.geometry import compute_geometry, compute_orientation

def test_region_classification():
    # Top-Left test
    assert classify_region(0.1, 0.1) == "top-left"

    # Bottom-Right test
    assert classify_region(0.9, 0.9) == "bottom-right"

    # Center test
    assert classify_region(0.5, 0.5) == "center"

    # Top-Center test
    assert classify_region(0.5, 0.1) == "top-center"

    # Bottom-Left test
    assert classify_region(0.1, 0.9) == "bottom-left"

def test_compute_relative_coordinates():
    rel_x, rel_y = compute_relative_coordinates(1550, 880, 1920, 1080)
    assert rel_x == pytest.approx(0.8073, abs=0.001)
    assert rel_y == pytest.approx(0.8148, abs=0.001)

import pytest

def test_compute_geometry():
    bbox = [1400, 850, 1700, 910]
    geom = compute_geometry(bbox)

    assert geom.x1 == 1400
    assert geom.y1 == 850
    assert geom.x2 == 1700
    assert geom.y2 == 910
    assert geom.width_px == 300
    assert geom.height_px == 60
    assert geom.center_x == 1550
    assert geom.center_y == 880
    assert geom.center == [1550, 880]
    assert geom.area == 18000
    assert geom.aspect_ratio == 5.0

def test_compute_orientation():
    polygon = [[100, 100], [300, 100], [300, 150], [100, 150]]
    orient = compute_orientation(polygon)
    assert orient.angle_degrees == 0.0
    assert orient.category == "horizontal"
