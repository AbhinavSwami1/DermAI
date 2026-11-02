from io import BytesIO
from uuid import uuid4, UUID
from PIL import Image
from app.api import upload, predictions
from app.models import (
    Prediction,
    ModelVersion,
    Image as ImageModel,
    ImageQualityAssessment,
)
def create_image():
    buffer = BytesIO()
    Image.new("RGB", (512, 512), "white").save(
        buffer,
        format="PNG",
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
def get_quality_assessment(db_session, image_id):
    return db_session.query(
        ImageQualityAssessment
    ).filter_by(
        image_id=UUID(str(image_id))
    ).first()
def mark_quality_acceptable(db_session, image_id):
    assessment = get_quality_assessment(
        db_session,
        image_id,
    )
    assert assessment is not None
    assessment.quality_status = "ACCEPTABLE"
    assessment.quality_flags = []
    db_session.flush()
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
# --------------------------------------------------
# PREDICTION TESTS
# --------------------------------------------------
def test_successful_prediction_and_database_persistence(
    client,
    db_session,
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(upload, "STORAGE_DIR", tmp_path)
    monkeypatch.setattr(predictions, "STORAGE_DIR", tmp_path)
    monkeypatch.setattr(
        predictions,
        "predict_image",
        fake_prediction,
    )
    case_id, headers = create_test_case(client)
    image_id = upload_test_image(
        client,
        case_id,
        headers,
    )
    mark_quality_acceptable(db_session, image_id)
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
        Prediction,
        UUID(data["prediction_id"]),
    )
    assert saved_prediction is not None
    assert saved_prediction.predicted_label == "BCC"
    saved_model = db_session.get(
        ModelVersion,
        UUID(data["model_version_id"]),
    )
    assert saved_model is not None
    assert (
        saved_model.architecture
        == predictions.MODEL_ARCHITECTURE
    )
def test_prediction_without_token_rejected(client):
    response = client.post(
        f"/api/v1/predictions/{uuid4()}"
    )
    assert response.status_code == 401
def test_prediction_for_another_users_image_rejected(
    client,
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(upload, "STORAGE_DIR", tmp_path)
    monkeypatch.setattr(predictions, "STORAGE_DIR", tmp_path)
    monkeypatch.setattr(
        predictions,
        "predict_image",
        fake_prediction,
    )
    case_id, owner_headers = create_test_case(client)
    image_id = upload_test_image(
        client,
        case_id,
        owner_headers,
    )
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
    client,
    db_session,
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(upload, "STORAGE_DIR", tmp_path)
    monkeypatch.setattr(predictions, "STORAGE_DIR", tmp_path)
    def failed_prediction(image_bytes):
        raise predictions.InferenceError(
            "Model unavailable"
        )
    monkeypatch.setattr(
        predictions,
        "predict_image",
        failed_prediction,
    )
    case_id, headers = create_test_case(client)
    image_id = upload_test_image(
        client,
        case_id,
        headers,
    )
    mark_quality_acceptable(db_session, image_id)
    response = client.post(
        f"/api/v1/predictions/{image_id}",
        headers=headers,
    )
    assert response.status_code == 503
    assert (
        db_session.query(Prediction).count()
        == 0
    )
def test_prediction_blocks_path_traversal(
    client,
    db_session,
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(upload, "STORAGE_DIR", tmp_path)
    monkeypatch.setattr(predictions, "STORAGE_DIR", tmp_path)
    case_id, headers = create_test_case(client)
    image_id = upload_test_image(
        client,
        case_id,
        headers,
    )
    mark_quality_acceptable(db_session, image_id)
    image_record = db_session.get(
        ImageModel,
        UUID(image_id),
    )
    image_record.storage_key = "../outside.png"
    db_session.flush()
    response = client.post(
        f"/api/v1/predictions/{image_id}",
        headers=headers,
    )
    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Invalid image storage reference."
    )
def test_prediction_blocks_review_required_image(
    client,
    db_session,
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(upload, "STORAGE_DIR", tmp_path)
    monkeypatch.setattr(predictions, "STORAGE_DIR", tmp_path)
    inference_called = False
    def tracked_prediction(image_bytes):
        nonlocal inference_called
        inference_called = True
        return fake_prediction(image_bytes)
    monkeypatch.setattr(
        predictions,
        "predict_image",
        tracked_prediction,
    )
    case_id, headers = create_test_case(client)
    image_id = upload_test_image(
        client,
        case_id,
        headers,
    )
    assessment = get_quality_assessment(
        db_session,
        image_id,
    )
    assert assessment is not None
    assessment.quality_status = "REVIEW_REQUIRED"
    assessment.quality_flags = ["POSSIBLY_BLURRY"]
    db_session.flush()
    response = client.post(
        f"/api/v1/predictions/{image_id}",
        headers=headers,
    )
    assert response.status_code == 409
    detail = response.json()["detail"]
    assert detail["code"] == "IMAGE_REVIEW_REQUIRED"
    assert detail["quality_status"] == "REVIEW_REQUIRED"
    assert inference_called is False
    assert (
        db_session.query(Prediction).count()
        == 0
    )
def test_prediction_blocks_missing_quality_assessment(
    client,
    db_session,
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(upload, "STORAGE_DIR", tmp_path)
    monkeypatch.setattr(predictions, "STORAGE_DIR", tmp_path)
    inference_called = False
    def tracked_prediction(image_bytes):
        nonlocal inference_called
        inference_called = True
        return fake_prediction(image_bytes)
    monkeypatch.setattr(
        predictions,
        "predict_image",
        tracked_prediction,
    )
    case_id, headers = create_test_case(client)
    image_id = upload_test_image(
        client,
        case_id,
        headers,
    )
    assessment = get_quality_assessment(
        db_session,
        image_id,
    )
    assert assessment is not None
    db_session.delete(assessment)
    db_session.flush()
    response = client.post(
        f"/api/v1/predictions/{image_id}",
        headers=headers,
    )
    assert response.status_code == 409
    assert (
        response.json()["detail"]["code"]
        == "QUALITY_ASSESSMENT_MISSING"
    )
    assert inference_called is False
    assert (
        db_session.query(Prediction).count()
        == 0
    )
# --------------------------------------------------
# GRAD-CAM TESTS
# --------------------------------------------------
def test_gradcam_successful_png_response(
    client,
    db_session,
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(upload, "STORAGE_DIR", tmp_path)
    monkeypatch.setattr(predictions, "STORAGE_DIR", tmp_path)
    expected_png = (
        b"\x89PNG\r\n\x1a\nfake-gradcam-image"
    )
    monkeypatch.setattr(
        predictions,
        "generate_gradcam",
        lambda image: expected_png,
    )
    case_id, headers = create_test_case(client)
    image_id = upload_test_image(
        client,
        case_id,
        headers,
    )
    mark_quality_acceptable(db_session, image_id)
    response = client.post(
        f"/api/v1/predictions/{image_id}/gradcam",
        headers=headers,
    )
    assert response.status_code == 200
    assert response.content == expected_png
    assert response.headers["content-type"] == "image/png"
    assert (
        response.headers["cache-control"]
        == "no-store"
    )
    assert "not a medical diagnosis" in (
        response.headers["x-research-disclaimer"]
    )
def test_gradcam_without_token_rejected(client):
    response = client.post(
        f"/api/v1/predictions/{uuid4()}/gradcam"
    )
    assert response.status_code == 401
def test_gradcam_for_another_users_image_rejected(
    client,
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(upload, "STORAGE_DIR", tmp_path)
    monkeypatch.setattr(predictions, "STORAGE_DIR", tmp_path)
    case_id, owner_headers = create_test_case(client)
    image_id = upload_test_image(
        client,
        case_id,
        owner_headers,
    )
    _, other_headers = create_test_case(client)
    response = client.post(
        f"/api/v1/predictions/{image_id}/gradcam",
        headers=other_headers,
    )
    assert response.status_code == 404
def test_gradcam_for_nonexistent_image_rejected(client):
    _, headers = create_test_case(client)
    response = client.post(
        f"/api/v1/predictions/{uuid4()}/gradcam",
        headers=headers,
    )
    assert response.status_code == 404
def test_gradcam_generation_failure_returns_503(
    client,
    db_session,
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(upload, "STORAGE_DIR", tmp_path)
    monkeypatch.setattr(predictions, "STORAGE_DIR", tmp_path)
    def failed_gradcam(image_bytes):
        raise predictions.InferenceError(
            "Grad-CAM unavailable"
        )
    monkeypatch.setattr(
        predictions,
        "generate_gradcam",
        failed_gradcam,
    )
    case_id, headers = create_test_case(client)
    image_id = upload_test_image(
        client,
        case_id,
        headers,
    )
    mark_quality_acceptable(db_session, image_id)
    response = client.post(
        f"/api/v1/predictions/{image_id}/gradcam",
        headers=headers,
    )
    assert response.status_code == 503
def test_gradcam_blocks_path_traversal(
    client,
    db_session,
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(upload, "STORAGE_DIR", tmp_path)
    monkeypatch.setattr(predictions, "STORAGE_DIR", tmp_path)
    case_id, headers = create_test_case(client)
    image_id = upload_test_image(
        client,
        case_id,
        headers,
    )
    mark_quality_acceptable(db_session, image_id)
    image_record = db_session.get(
        ImageModel,
        UUID(image_id),
    )
    image_record.storage_key = "../outside.png"
    db_session.flush()
    response = client.post(
        f"/api/v1/predictions/{image_id}/gradcam",
        headers=headers,
    )
    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Invalid image storage reference."
    )
def test_gradcam_blocks_review_required_image(
    client,
    db_session,
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(upload, "STORAGE_DIR", tmp_path)
    monkeypatch.setattr(predictions, "STORAGE_DIR", tmp_path)
    gradcam_called = False
    def tracked_gradcam(image_bytes):
        nonlocal gradcam_called
        gradcam_called = True
        return b"fake-gradcam"
    monkeypatch.setattr(
        predictions,
        "generate_gradcam",
        tracked_gradcam,
    )
    case_id, headers = create_test_case(client)
    image_id = upload_test_image(
        client,
        case_id,
        headers,
    )
    assessment = get_quality_assessment(
        db_session,
        image_id,
    )
    assert assessment is not None
    assessment.quality_status = "REVIEW_REQUIRED"
    assessment.quality_flags = ["POSSIBLY_BLURRY"]
    db_session.flush()
    response = client.post(
        f"/api/v1/predictions/{image_id}/gradcam",
        headers=headers,
    )
    assert response.status_code == 409
    assert (
        response.json()["detail"]["code"]
        == "IMAGE_REVIEW_REQUIRED"
    )
    assert gradcam_called is False


# --------------------------------------------------
# PREDICTION HISTORY TESTS
# --------------------------------------------------

def create_saved_test_prediction(
    client,
    db_session,
    tmp_path,
    monkeypatch,
    headers,
):
    """
    Upload an image and create a saved prediction
    for the authenticated user.
    """

    monkeypatch.setattr(upload, "STORAGE_DIR", tmp_path)
    monkeypatch.setattr(predictions, "STORAGE_DIR", tmp_path)
    monkeypatch.setattr(
        predictions,
        "predict_image",
        fake_prediction,
    )

    case_response = client.post(
        "/api/v1/cases",
        headers=headers,
    )

    assert case_response.status_code == 201

    case_id = case_response.json()["case_id"]

    image_id = upload_test_image(
        client,
        case_id,
        headers,
    )

    mark_quality_acceptable(
        db_session,
        image_id,
    )

    prediction_response = client.post(
        f"/api/v1/predictions/{image_id}",
        headers=headers,
    )

    assert prediction_response.status_code == 201

    return prediction_response.json()


def test_prediction_history_requires_authentication(client):
    response = client.get(
        "/api/v1/predictions/history"
    )

    assert response.status_code == 401


def test_prediction_history_returns_empty_list_for_new_user(client):
    _, headers = create_test_case(client)

    response = client.get(
        "/api/v1/predictions/history",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["items"] == []
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["page_size"] == 10
    assert data["total_pages"] == 0
    assert "not a medical diagnosis" in data["disclaimer"]


def test_prediction_history_returns_saved_predictions(
    client,
    db_session,
    tmp_path,
    monkeypatch,
):
    _, headers = create_test_case(client)

    saved_prediction = create_saved_test_prediction(
        client,
        db_session,
        tmp_path,
        monkeypatch,
        headers,
    )

    response = client.get(
        "/api/v1/predictions/history",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1

    item = data["items"][0]

    assert item["prediction_id"] == saved_prediction["prediction_id"]
    assert item["image_id"] == saved_prediction["image_id"]
    assert item["predicted_label"] == "BCC"
    assert item["confidence"] == 0.40
    assert item["status"] == "completed"
    assert len(item["class_scores"]) == 6
    assert item["architecture"] == predictions.MODEL_ARCHITECTURE


def test_prediction_history_is_isolated_between_users(
    client,
    db_session,
    tmp_path,
    monkeypatch,
):
    _, user_a_headers = create_test_case(client)

    user_a_prediction = create_saved_test_prediction(
        client,
        db_session,
        tmp_path,
        monkeypatch,
        user_a_headers,
    )

    _, user_b_headers = create_test_case(client)

    user_b_prediction = create_saved_test_prediction(
        client,
        db_session,
        tmp_path,
        monkeypatch,
        user_b_headers,
    )

    user_a_response = client.get(
        "/api/v1/predictions/history",
        headers=user_a_headers,
    )

    user_b_response = client.get(
        "/api/v1/predictions/history",
        headers=user_b_headers,
    )

    assert user_a_response.status_code == 200
    assert user_b_response.status_code == 200

    user_a_items = user_a_response.json()["items"]
    user_b_items = user_b_response.json()["items"]

    assert len(user_a_items) == 1
    assert len(user_b_items) == 1

    assert (
        user_a_items[0]["prediction_id"]
        == user_a_prediction["prediction_id"]
    )

    assert (
        user_b_items[0]["prediction_id"]
        == user_b_prediction["prediction_id"]
    )

    assert (
        user_a_items[0]["prediction_id"]
        != user_b_items[0]["prediction_id"]
    )


def test_prediction_history_rejects_invalid_pagination(client):
    _, headers = create_test_case(client)

    invalid_page = client.get(
        "/api/v1/predictions/history?page=0",
        headers=headers,
    )

    invalid_page_size = client.get(
        "/api/v1/predictions/history?page_size=51",
        headers=headers,
    )

    assert invalid_page.status_code == 422
    assert invalid_page_size.status_code == 422