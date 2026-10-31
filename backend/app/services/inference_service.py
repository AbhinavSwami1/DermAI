import os
from functools import lru_cache
from io import BytesIO
from pathlib import Path

import torch
from PIL import Image, ImageOps
from torchvision import transforms

from ml.src.models.mobilenet import create_mobilenet_model
from threading import Lock


CLASS_NAMES = ["ACK", "BCC", "MEL", "NEV", "SCC", "SEK"]
MODEL_EXECUTION_LOCK = Lock()

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CHECKPOINT = (
    PROJECT_ROOT
    / "ml"
    / "checkpoints"
    / "mobilenet"
    / "best_mobilenet_v3_small.pth"
)


class InferenceError(Exception):
    """Raised when model loading or inference fails."""


def get_inference_device():
    if torch.cuda.is_available():
        return torch.device("cuda")

    if torch.backends.mps.is_available():
        return torch.device("mps")

    return torch.device("cpu")


def get_preprocessing_transform():
    return transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(
            mean=IMAGENET_MEAN,
            std=IMAGENET_STD,
        ),
    ])


@lru_cache(maxsize=1)
def load_model():
    checkpoint_path = Path(
        os.getenv("DERMAI_MODEL_CHECKPOINT", str(DEFAULT_CHECKPOINT))
    ).expanduser()

    if not checkpoint_path.is_absolute():
        checkpoint_path = PROJECT_ROOT / checkpoint_path

    if not checkpoint_path.is_file():
        raise InferenceError(
            f"Model checkpoint not found: {checkpoint_path}"
        )

    device = get_inference_device()

    try:
        checkpoint = torch.load(
            checkpoint_path,
            map_location="cpu",
            weights_only=True,
        )

        if not isinstance(checkpoint, dict):
            raise InferenceError("Invalid model checkpoint format.")

        state_dict = checkpoint.get("model_state_dict")

        if not isinstance(state_dict, dict):
            raise InferenceError(
                "Checkpoint does not contain model_state_dict."
            )

        model = create_mobilenet_model(pretrained=False)
        model.load_state_dict(state_dict, strict=True)
        model.to(device)
        model.eval()

        return model, device

    except InferenceError:
        raise
    except Exception as exc:
        raise InferenceError(
            "Unable to load the trained MobileNetV3-Small checkpoint."
        ) from exc


def preprocess_image(image_bytes: bytes) -> torch.Tensor:
    try:
        with Image.open(BytesIO(image_bytes)) as image:
            image = ImageOps.exif_transpose(image)
            image = image.convert("RGB")
            image = image.resize(
                (224, 224),
                Image.Resampling.LANCZOS,
            )

            tensor = get_preprocessing_transform()(image)

        return tensor.unsqueeze(0)

    except Exception as exc:
        raise InferenceError(
            "Unable to preprocess the uploaded image."
        ) from exc


def predict_image(image_bytes: bytes) -> dict:
    if not image_bytes:
        raise InferenceError("Image data is empty.")

    model, device = load_model()
    input_tensor = preprocess_image(image_bytes).to(device)

    try:
        with MODEL_EXECUTION_LOCK:
            with torch.inference_mode():
                logits = model(input_tensor)
                probabilities = torch.softmax(logits, dim=1)[0]
                probabilities = probabilities.cpu()

        if probabilities.numel() != len(CLASS_NAMES):
            raise InferenceError(
                "Model returned an unexpected number of classes."
            )

        if not torch.isfinite(probabilities).all():
            raise InferenceError(
                "Model returned invalid probability values."
            )

        predicted_index = int(torch.argmax(probabilities).item())

        class_scores = {
            class_name: float(probabilities[index].item())
            for index, class_name in enumerate(CLASS_NAMES)
        }

        return {
            "predicted_label": CLASS_NAMES[predicted_index],
            "confidence": class_scores[CLASS_NAMES[predicted_index]],
            "class_scores": class_scores,
        }

    except InferenceError:
        raise
    except Exception as exc:
        raise InferenceError("Model inference failed.") from exc
