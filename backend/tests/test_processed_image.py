from io import BytesIO

import pytest
from PIL import Image

from app.services.processed_image import IMAGE_SIZE, PREPROCESSING_VERSION, render_model_input


def _encode(image, fmt="PNG", **kwargs):
    buffer = BytesIO()
    image.save(buffer, format=fmt, **kwargs)
    return buffer.getvalue()


def test_output_is_224_rgb_png_and_deterministic():
    data = _encode(Image.new("RGB", (300, 200), (200, 120, 90)))
    png, info = render_model_input(data)
    out = Image.open(BytesIO(png))
    assert out.size == (IMAGE_SIZE, IMAGE_SIZE) and out.mode == "RGB"
    assert info["version"] == PREPROCESSING_VERSION
    assert info["original_size"] == [300, 200] and info["processed_size"] == [224, 224]
    assert render_model_input(data)[0] == png


@pytest.mark.parametrize("mode", ["L", "RGBA"])
def test_grayscale_and_alpha_become_rgb(mode):
    png, _ = render_model_input(_encode(Image.new(mode, (64, 64))))
    assert Image.open(BytesIO(png)).mode == "RGB"


def test_exif_orientation_is_applied_once():
    image = Image.new("RGB", (40, 20), (10, 200, 10))
    exif = image.getexif()
    exif[0x0112] = 6  # rotate 270 / swap width and height
    _, info = render_model_input(_encode(image, "JPEG", exif=exif))
    assert info["original_size"] == [20, 40]


@pytest.mark.parametrize("data", [b"", b"not an image", b"\x89PNG\r\n\x1a\nbroken"])
def test_invalid_bytes_raise_value_error(data):
    with pytest.raises(ValueError):
        render_model_input(data)


def test_image_size_matches_inference_service():
    from app.services import inference_service
    assert IMAGE_SIZE == inference_service.IMAGE_SIZE
