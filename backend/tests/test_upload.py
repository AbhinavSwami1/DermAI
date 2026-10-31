from io import BytesIO
from uuid import uuid4, UUID

from PIL import Image

from app.api import upload
from app.models import Image as ImageModel


def create_image(image_format="PNG", size=(512, 512)):
    buffer = BytesIO()
    Image.new("RGB", size, "white").save(buffer, format=image_format)
    return buffer.getvalue()


def create_test_case(client):
    email = f"{uuid4().hex}@dermai.com"

    user_response = client.post(
        "/api/v1/users/register",
        json={
            "email": email,
            "password": "SecurePass@123",
            "full_name": "Upload Test User",
        },
    )

    assert user_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "SecurePass@123",
        },
    )

    assert login_response.status_code == 200

    headers = {
        "Authorization": f"Bearer {login_response.json()['access_token']}"
    }

    case_response = client.post(
        "/api/v1/cases",
        headers=headers,
    )

    assert case_response.status_code == 201

    return case_response.json()["case_id"], headers


def test_valid_png_upload(client, db_session, tmp_path, monkeypatch):
    monkeypatch.setattr(upload, "STORAGE_DIR", tmp_path)
    case_id, headers = create_test_case(client)

    response = client.post(
        "/api/v1/upload",
        headers=headers,
        data={"case_id": case_id},
        files={"file": ("test.png", create_image(), "image/png")},
    )

    assert response.status_code == 201
    data = response.json()

    assert data["case_id"] == case_id
    assert data["mime_type"] == "image/png"
    assert data["width"] == 512
    assert data["height"] == 512
    assert (tmp_path / data["storage_key"]).exists()

    saved_image = db_session.get(ImageModel, data["image_id"])

    assert saved_image is not None
    assert saved_image.case_id == UUID(case_id)
    assert saved_image.mime_type == "image/png"
    assert saved_image.storage_key == data["storage_key"]


def test_valid_jpeg_upload(client, tmp_path, monkeypatch):
    monkeypatch.setattr(upload, "STORAGE_DIR", tmp_path)
    case_id, headers = create_test_case(client)

    response = client.post(
        "/api/v1/upload",
        headers=headers,
        data={"case_id": case_id},
        files={
            "file": (
                "test.jpg",
                create_image("JPEG"),
                "image/jpeg",
            )
        },
    )

    assert response.status_code == 201
    assert response.json()["mime_type"] == "image/jpeg"


def test_corrupted_image_rejected(client):
    case_id, headers = create_test_case(client)

    response = client.post(
        "/api/v1/upload",
        headers=headers,
        data={"case_id": case_id},
        files={"file": ("broken.jpg", b"not an image", "image/jpeg")},
    )

    assert response.status_code == 400


def test_unsupported_gif_rejected(client):
    case_id, headers = create_test_case(client)

    response = client.post(
        "/api/v1/upload",
        headers=headers,
        data={"case_id": case_id},
        files={
            "file": (
                "test.gif",
                create_image("GIF"),
                "image/gif",
            )
        },
    )

    assert response.status_code == 400


def test_small_image_rejected(client):
    case_id, headers = create_test_case(client)

    response = client.post(
        "/api/v1/upload",
        headers=headers,
        data={"case_id": case_id},
        files={
            "file": (
                "small.png",
                create_image("PNG", (100, 100)),
                "image/png",
            )
        },
    )

    assert response.status_code == 400


def test_oversized_file_rejected(client):
    case_id, headers = create_test_case(client)

    response = client.post(
        "/api/v1/upload",
        headers=headers,
        data={"case_id": case_id},
        files={
            "file": (
                "large.jpg",
                b"A" * (upload.MAX_FILE_SIZE + 1),
                "image/jpeg",
            )
        },
    )

    assert response.status_code == 400


def test_upload_without_token_rejected(client):
    response = client.post(
        "/api/v1/upload",
        data={"case_id": str(uuid4())},
        files={"file": ("test.png", create_image(), "image/png")},
    )

    assert response.status_code == 401


def test_upload_to_another_users_case_rejected(client):
    case_id, _ = create_test_case(client)
    _, other_headers = create_test_case(client)

    response = client.post(
        "/api/v1/upload",
        headers=other_headers,
        data={"case_id": case_id},
        files={"file": ("test.png", create_image(), "image/png")},
    )

    assert response.status_code == 404