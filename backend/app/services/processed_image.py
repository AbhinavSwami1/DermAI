"""Reconstruct the exact image the model receives (before normalisation).

Mirrors backend/app/services/inference_service.preprocess_image: EXIF orientation,
RGB conversion, 224x224 LANCZOS resize. ToTensor and ImageNet normalisation follow
at inference time and are not visible as an image. The result is deterministic and is
regenerated on demand from the stored original; it is not persisted.
"""
from io import BytesIO

from PIL import Image, ImageOps

PREPROCESSING_VERSION = "1.0.0"
IMAGE_SIZE = 224  # must equal inference_service.IMAGE_SIZE (checked by a test)


def render_model_input(image_bytes: bytes) -> tuple[bytes, dict]:
    """Return (PNG bytes of the model input, description of the steps applied)."""
    try:
        with Image.open(BytesIO(image_bytes)) as image:
            image = ImageOps.exif_transpose(image)
            oriented_size = list(image.size)
            image = image.convert("RGB")
            image = image.resize((IMAGE_SIZE, IMAGE_SIZE), Image.Resampling.LANCZOS)
            buffer = BytesIO()
            image.save(buffer, format="PNG")
    except Exception as exc:
        raise ValueError("Unable to preprocess the image.") from exc

    info = {
        "version": PREPROCESSING_VERSION,
        "original_size": oriented_size,
        "processed_size": [IMAGE_SIZE, IMAGE_SIZE],
        "orientation": "EXIF orientation applied",
        "color_mode": "RGB",
        "resize": "direct resize to 224 x 224",
        "interpolation": "LANCZOS",
        "aspect_ratio": "not preserved",
        "normalization": "ImageNet mean/std applied after this step, at inference",
        "persisted": False,
    }
    return buffer.getvalue(), info
