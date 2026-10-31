import torch
import pytest

from app.services import inference_service


class FakeModel:
    def __call__(self, input_tensor):
        return torch.tensor(
            [[2.0, 1.0, 0.5, 0.2, 0.1, 0.3]],
            device=input_tensor.device,
        )


def test_preprocessing_output_shape_and_type():
    from io import BytesIO
    from PIL import Image

    buffer = BytesIO()
    Image.new("RGB", (512, 512), "white").save(
        buffer, format="PNG"
    )

    tensor = inference_service.preprocess_image(buffer.getvalue())

    assert tensor.shape == (1, 3, 224, 224)
    assert tensor.dtype == torch.float32


def test_prediction_returns_six_class_scores(monkeypatch):
    monkeypatch.setattr(
        inference_service,
        "load_model",
        lambda: (FakeModel(), torch.device("cpu")),
    )

    from io import BytesIO
    from PIL import Image

    buffer = BytesIO()
    Image.new("RGB", (512, 512), "white").save(
        buffer, format="PNG"
    )

    result = inference_service.predict_image(buffer.getvalue())

    assert result["predicted_label"] == "ACK"
    assert result["confidence"] == result["class_scores"]["ACK"]
    assert set(result["class_scores"]) == set(
        inference_service.CLASS_NAMES
    )
    assert sum(result["class_scores"].values()) == pytest.approx(1.0)
    assert all(
        0.0 <= score <= 1.0
        for score in result["class_scores"].values()
    )


def test_empty_image_rejected():
    with pytest.raises(inference_service.InferenceError):
        inference_service.predict_image(b"")


def test_corrupted_image_rejected(monkeypatch):
    monkeypatch.setattr(
        inference_service,
        "load_model",
        lambda: (FakeModel(), torch.device("cpu")),
    )

    with pytest.raises(inference_service.InferenceError):
        inference_service.predict_image(b"not-an-image")
