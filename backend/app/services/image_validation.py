from io import BytesIO

from PIL import Image, UnidentifiedImageError


ALLOWED_FORMATS = {"JPEG", "PNG"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
MIN_IMAGE_WIDTH = 224
MIN_IMAGE_HEIGHT = 224


class ImageValidationError(Exception):
    """Raised when an uploaded image fails validation."""


def validate_image(image_bytes: bytes) -> dict:
    """
    Validate uploaded image format, file size and dimensions.

    Returns verified image metadata.
    """

    if not image_bytes:
        raise ImageValidationError("Uploaded file is empty.")

    if len(image_bytes) > MAX_FILE_SIZE:
        raise ImageValidationError(
            "Image size exceeds the maximum limit of 10 MB."
        )

    try:
        with Image.open(BytesIO(image_bytes)) as image:
            image_format = image.format
            width, height = image.size

            if image_format not in ALLOWED_FORMATS:
                raise ImageValidationError(
                    "Only JPEG and PNG images are supported."
                )

            image.verify()

        if width < MIN_IMAGE_WIDTH or height < MIN_IMAGE_HEIGHT:
            raise ImageValidationError(
                "Image dimensions must be at least 224 x 224 pixels."
            )

        return {
            "format": image_format,
            "width": width,
            "height": height,
            "file_size_bytes": len(image_bytes),
            "mime_type": (
                "image/jpeg" if image_format == "JPEG" else "image/png"
            ),
        }

    except ImageValidationError:
        raise

    except (UnidentifiedImageError, OSError, SyntaxError, ValueError):
        raise ImageValidationError(
            "Uploaded file is corrupted or is not a valid image."
        )