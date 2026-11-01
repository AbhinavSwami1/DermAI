from io import BytesIO

import numpy as np
import pytest
from PIL import Image

from app.services.image_quality_service import (
    ImageQualityError,
    assess_image_quality,
)


def make_image(array, image_format="PNG"):
    buffer = BytesIO()
    Image.fromarray(array).save(buffer, format=image_format)
    return buffer.getvalue()


def test_sharp_image_returns_valid_metrics():
    rng = np.random.default_rng(42)
    image = rng.integers(0, 256, (256, 256), dtype=np.uint8)

    result = assess_image_quality(make_image(image))

    assert result["width"] == 256
    assert result["height"] == 256
    assert result["blur_score"] >= 0
    assert 0 <= result["brightness_mean"] <= 255
    assert 0 <= result["dark_pixel_percentage"] <= 100
    assert 0 <= result["bright_pixel_percentage"] <= 100
    assert result["algorithm_version"] == "1.0.0"


def test_uniform_image_is_flagged_as_possibly_blurry():
    image = np.full((256, 256), 128, dtype=np.uint8)

    result = assess_image_quality(make_image(image))

    assert result["blur_score"] == 0
    assert "POSSIBLY_BLURRY" in result["quality_flags"]
    assert result["quality_status"] == "REVIEW_REQUIRED"


def test_dark_image_is_flagged():
    image = np.full((256, 256), 20, dtype=np.uint8)

    result = assess_image_quality(make_image(image))

    assert "LOW_BRIGHTNESS" in result["quality_flags"]
    assert "HIGH_DARK_PIXEL_PERCENTAGE" in result["quality_flags"]


def test_bright_image_is_flagged():
    image = np.full((256, 256), 245, dtype=np.uint8)

    result = assess_image_quality(make_image(image))

    assert "HIGH_BRIGHTNESS" in result["quality_flags"]
    assert "HIGH_BRIGHT_PIXEL_PERCENTAGE" in result["quality_flags"]


def test_empty_image_is_rejected():
    with pytest.raises(ImageQualityError, match="empty"):
        assess_image_quality(b"")


def test_corrupted_image_is_rejected():
    with pytest.raises(ImageQualityError, match="corrupted"):
        assess_image_quality(b"not-an-image")


def test_jpeg_image_is_supported():
    image = np.full((256, 256, 3), 128, dtype=np.uint8)

    result = assess_image_quality(make_image(image, "JPEG"))

    assert result["width"] == 256
    assert result["height"] == 256
