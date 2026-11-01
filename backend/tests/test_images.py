from io import BytesIO
from uuid import uuid4

from PIL import Image

from app.api import upload


def create_image():
    buffer = BytesIO()
    Image.new("RGB", (512, 512), "white").save(buffer, format="PNG")
    return buffer.getvalue()


def create_test_user_and_case(client):
    email = f"{uuid4().hex}@dermai.com"
    password = "SecurePass@123"

    register = client.post(
        "/api/v1/users/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Quality Test User",
        },
    )
    assert register.status_code == 201

    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200

    headers = {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }

    case = client.post("/api/v1/cases", headers=headers)
    assert case.status_code == 201

    return case.json()["case_id"], headers


def upload_test_image(client, case_id, headers, tmp_path, monkeypatch):
    monkeypatch.setattr(upload, "STORAGE_DIR", tmp_path)

    response = client.post(
        "/api/v1/upload",
        headers=headers,
        data={"case_id": case_id},
        files={
            "file": (
                "quality_test.png",
                create_image(),
                "image/png",
            )
        },
    )

    assert response.status_code == 201
    return response.json()["image_id"]


def test_owner_can_get_image_quality(
    client, tmp_path, monkeypatch
):
    case_id, headers = create_test_user_and_case(client)

    image_id = upload_test_image(
        client, case_id, headers, tmp_path, monkeypatch
    )

    response = client.get(
        f"/api/v1/images/{image_id}/quality",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["image_id"] == image_id
    assert data["quality_status"] == "REVIEW_REQUIRED"
    assert "POSSIBLY_BLURRY" in data["quality_flags"]
    assert data["algorithm_version"] == "1.0.0"
    assert "Research-only" in data["disclaimer"]


def test_quality_endpoint_requires_authentication(client):
    response = client.get(
        f"/api/v1/images/{uuid4()}/quality"
    )

    assert response.status_code == 401


def test_user_cannot_access_another_users_image(
    client, tmp_path, monkeypatch
):
    case_id, owner_headers = create_test_user_and_case(client)

    image_id = upload_test_image(
        client, case_id, owner_headers, tmp_path, monkeypatch
    )

    _, other_headers = create_test_user_and_case(client)

    response = client.get(
        f"/api/v1/images/{image_id}/quality",
        headers=other_headers,
    )

    assert response.status_code == 404