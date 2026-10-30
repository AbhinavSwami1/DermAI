from pathlib import Path
import numpy as np
from PIL import Image


def load_image(image_path):
    image_path = Path(image_path)

    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    with Image.open(image_path) as image:
        image.load()
        image = image.convert("RGB")

    return image


def resize_image(image, target_size=(224, 224)):
    return image.resize(
        target_size,
        Image.Resampling.LANCZOS
    )


def normalize_image(image):
    """
    Convert image pixels from 0-255 to 0-1.
    """

    image_array = np.asarray(image, dtype=np.float32)

    normalized_image = image_array / 255.0

    return normalized_image

def preprocess_image(image_path, target_size=(224, 224)):
    """
    Complete image preprocessing pipeline:
    1. Load image
    2. Convert to RGB
    3. Resize image
    4. Normalize pixel values
    """

    image = load_image(image_path)

    image = resize_image(image, target_size)

    image_array = normalize_image(image)

    return image_array