from io import BytesIO
from uuid import uuid4, UUID

from PIL import Image

from app.api import upload, predictions
from app.models import Prediction, ModelVersion, Image as ImageModel


def create_image():
    buffer = BytesIO()
    Image.new("RGB", (512, 512), "white").save(
        buffer, format="PNG"
    )
    return buffer.getvalue()


def create_test_case(client):
    email = f"{uuid4().hex}@dermai.com"

    registration = client.post(
        "/api/v1/users/register",
        json={
            "email": email,
            "password": "SecurePass@123",
            "full_name": "Prediction Test User",
        },
    )
    assert registration.status_code == 201

    login = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "SecurePass@123",
        },
    )
    assert login.status_code == 200

    headers = {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }

    case = client.post(
        "/api/v1/cases",
        headers=headers,
    )
    assert case.status_code == 201

    return case.json()["case_id"], headers


def upload_test_image(client, case_id, headers):
    response = client.post(
        "/api/v1/upload",
        headers=headers,
        data={"case_id": case_id},
        files={
            "file": (
                "test.png",
                create_image(),
                "image/png",
            )
        },
    )

    assert response.status_code == 201
    return response.json()["image_id"]


def fake_prediction(image_bytes):
    return {
        "predicted_label": "BCC",
        "confidence": 0.40,
        "class_scores": {
            "ACK": 0.10,
            "BCC": 0.40,
            "MEL": 0.15,
            "NEV": 0.15,
            "SCC": 0.10,
            "SEK": 0.10,
        },
    }


def test_successful_prediction_and_database_persistence(
    client, db_session, tmp_path, monkeypatch
):
    monkeypatch.setattr(upload, "STORAGE_DIR", tmp_path)
    monkeypatch.setattr(predictions, "STORAGE_DIR", tmp_path)
    monkeypatch.setattr(
        predictions, "predict_image", fake_prediction
    )

    case_id, headers = create_test_case(client)
    image_id = upload_test_image(client, case_id, headers)

    response = client.post(
        f"/api/v1/predictions/{image_id}",
        headers=headers,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["image_id"] == image_id
    assert data["predicted_label"] == "BCC"
    assert data["confidence"] == 0.40
    assert data["status"] == "completed"
    assert len(data["class_scores"]) == 6
    assert sum(data["class_scores"].values()) == 1.0
    assert data["model_name"] == predictions.MODEL_NAME
    assert "not a medical diagnosis" in data["disclaimer"]

    saved_prediction = db_session.get(
        Prediction, UUID(data["prediction_id"])
    )
    assert saved_prediction is not None
    assert saved_prediction.predicted_label == "BCC"

    saved_model = db_session.get(
        ModelVersion, UUID(data["model_version_id"])
    )
    assert saved_model is not None
    assert saved_model.architecture == predictions.MODEL_ARCHITECTURE


def test_prediction_without_token_rejected(client):
    response = client.post(
        f"/api/v1/predictions/{uuid4()}"
    )

    assert response.status_code == 401


def test_prediction_for_another_users_image_rejected(
    client, tmp_path, monkeypatch
):
    monkeypatch.setattr(upload, "STORAGE_DIR", tmp_path)
    monkeypatch.setattr(predictions, "STORAGE_DIR", tmp_path)
    monkeypatch.setattr(
        predictions, "predict_image", fake_prediction
    )

    case_id, owner_headers = create_test_case(client)
    image_id = upload_test_image(client, case_id, owner_headers)

    _, other_headers = create_test_case(client)

    response = client.post(
        f"/api/v1/predictions/{image_id}",
        headers=other_headers,
    )

    assert response.status_code == 404


def test_prediction_for_nonexistent_image_rejected(client):
    _, headers = create_test_case(client)

    response = client.post(
        f"/api/v1/predictions/{uuid4()}",
        headers=headers,
    )

    assert response.status_code == 404


def test_prediction_inference_failure_returns_503(
    client, db_session, tmp_path, monkeypatch
):
    monkeypatch.setattr(upload, "STORAGE_DIR", tmp_path)
    monkeypatch.setattr(predictions, "STORAGE_DIR", tmp_path)

    def failed_prediction(image_bytes):
        raise predictions.InferenceError("Model unavailable")

    monkeypatch.setattr(
        predictions, "predict_image", failed_prediction
    )

    case_id, headers = create_test_case(client)
    image_id = upload_test_image(client, case_id, headers)

    response = client.post(
        f"/api/v1/predictions/{image_id}",
        headers=headers,
    )

    assert response.status_code == 503
    assert db_session.query(Prediction).count() == 0


def test_prediction_blocks_path_traversal(
    client, db_session, tmp_path, monkeypatch
):
    monkeypatch.setattr(upload, "STORAGE_DIR", tmp_path)
    monkeypatch.setattr(predictions, "STORAGE_DIR", tmp_path)

    case_id, headers = create_test_case(client)
    image_id = upload_test_image(client, case_id, headers)

    image_record = db_session.get(ImageModel, UUID(image_id))
    image_record.storage_key = "../outside.png"
    db_session.flush()

    response = client.post(
        f"/api/v1/predictions/{image_id}",
        headers=headers,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image storage reference."
