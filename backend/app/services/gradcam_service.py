from io import BytesIO

import numpy as np
import torch
from matplotlib import colormaps
from PIL import Image, ImageOps

from app.services.inference_service import (
    InferenceError,
    MODEL_EXECUTION_LOCK,
    load_model,
    preprocess_image,
)
from ml.src.explainability.gradcam import GradCAM


# The cached model is shared across requests. Serialize Grad-CAM
# operations because the implementation stores activations on the
# GradCAM instance and registers a temporary forward hook.


def generate_gradcam(image_bytes: bytes) -> bytes:
    """
    Generate a research-only Grad-CAM PNG overlay.

    Returns:
        PNG image bytes containing the original image and Grad-CAM overlay.
    """
    if not image_bytes:
        raise InferenceError("Image data is empty.")

    try:
        with Image.open(BytesIO(image_bytes)) as source:
            original_image = ImageOps.exif_transpose(source).convert("RGB")

        model, device = load_model()
        input_tensor = preprocess_image(image_bytes).to(device)

        with MODEL_EXECUTION_LOCK:
            gradcam = GradCAM(
                model=model,
                target_layer=model.features[-1],
            )

            try:
                model.zero_grad(set_to_none=True)

                # Grad-CAM requires gradients, unlike normal inference.
                with torch.enable_grad():
                    heatmap, _ = gradcam.generate(input_tensor)

                heatmap_image = Image.fromarray(
                    np.uint8(np.clip(heatmap, 0.0, 1.0) * 255)
                ).resize(
                    original_image.size,
                    Image.Resampling.BILINEAR,
                )

                heatmap_array = np.asarray(heatmap_image) / 255.0
                colored_heatmap = colormaps["jet"](heatmap_array)[..., :3]
                colored_heatmap = Image.fromarray(
                    np.uint8(colored_heatmap * 255)
                )

                overlay = Image.blend(
                    original_image,
                    colored_heatmap,
                    alpha=0.45,
                )

                output = BytesIO()
                overlay.save(output, format="PNG")
                return output.getvalue()

            finally:
                gradcam.close()
                model.zero_grad(set_to_none=True)

    except InferenceError:
        raise
    except Exception as exc:
        raise InferenceError(
            "Unable to generate the Grad-CAM visualization."
        ) from exc
