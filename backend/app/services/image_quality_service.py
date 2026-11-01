from io import BytesIO

import cv2
import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError


ALGORITHM_VERSION = "1.0.0"

# Preliminary research heuristics; these are not clinical thresholds.
MIN_BLUR_SCORE = 100.0
MIN_BRIGHTNESS = 40.0
MAX_BRIGHTNESS = 220.0
MAX_DARK_PIXEL_PERCENTAGE = 50.0
MAX_BRIGHT_PIXEL_PERCENTAGE = 50.0


class ImageQualityError(Exception):
    """Raised when image quality cannot be assessed."""


def assess_image_quality(image_bytes: bytes) -> dict:
    """Calculate basic image-quality metrics for a JPEG or PNG image."""

    if not image_bytes:
        raise ImageQualityError("Image is empty.")

    try:
        with Image.open(BytesIO(image_bytes)) as source:
            if source.format not in {"JPEG", "PNG"}:
                raise ImageQualityError(
                    "Only JPEG and PNG images are supported."
                )

            image = ImageOps.exif_transpose(source).convert("RGB")
            width, height = image.size
            rgb = np.asarray(image)

    except ImageQualityError:
        raise
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ImageQualityError(
            "Image is corrupted or cannot be decoded."
        ) from exc

    if width < 1 or height < 1:
        raise ImageQualityError("Image dimensions are invalid.")

    grayscale = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)

    blur_score = float(cv2.Laplacian(
        grayscale, cv2.CV_64F
    ).var())

    brightness_mean = float(np.mean(grayscale))

    dark_percentage = float(
        np.mean(grayscale < MIN_BRIGHTNESS) * 100.0
    )
    bright_percentage = float(
        np.mean(grayscale > MAX_BRIGHTNESS) * 100.0
    )

    flags = []

    if blur_score < MIN_BLUR_SCORE:
        flags.append("POSSIBLY_BLURRY")

    if brightness_mean < MIN_BRIGHTNESS:
        flags.append("LOW_BRIGHTNESS")
    elif brightness_mean > MAX_BRIGHTNESS:
        flags.append("HIGH_BRIGHTNESS")

    if dark_percentage > MAX_DARK_PIXEL_PERCENTAGE:
        flags.append("HIGH_DARK_PIXEL_PERCENTAGE")

    if bright_percentage > MAX_BRIGHT_PIXEL_PERCENTAGE:
        flags.append("HIGH_BRIGHT_PIXEL_PERCENTAGE")

    return {
        "width": width,
        "height": height,
        "blur_score": blur_score,
        "brightness_mean": brightness_mean,
        "dark_pixel_percentage": dark_percentage,
        "bright_pixel_percentage": bright_percentage,
        "quality_status": (
            "REVIEW_REQUIRED" if flags else "ACCEPTABLE"
        ),
        "quality_flags": flags,
        "algorithm_version": ALGORITHM_VERSION,
    }
