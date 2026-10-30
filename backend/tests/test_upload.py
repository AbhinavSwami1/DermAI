from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.api import upload

client = TestClient(app)


def create_image(image_format="PNG", size=(512, 512)):
    buffer = BytesIO()
    Image.new("RGB", size, "white").save(buffer, format=image_format)
    return buffer.getvalue()


def test_valid_png_upload(tmp_path, monkeypatch):
    monkeypatch.setattr(upload, "STORAGE_DIR", tmp_path)

    response = client.post(
        "/api/v1/upload",
        files={"file": ("test.png", create_image(), "image/png")}
    )

    assert response.status_code == 201
    assert response.json()["status"] == "uploaded"


def test_valid_jpeg_upload(tmp_path, monkeypatch):
    monkeypatch.setattr(upload, "STORAGE_DIR", tmp_path)

    response = client.post(
        "/api/v1/upload",
        files={"file": ("test.jpg", create_image("JPEG"), "image/jpeg")}
    )

    assert response.status_code == 201


def test_corrupted_image_rejected():
    response = client.post(
        "/api/v1/upload",
        files={"file": ("broken.jpg", b"not an image", "image/jpeg")}
    )

    assert response.status_code == 400


def test_unsupported_gif_rejected():
    response = client.post(
        "/api/v1/upload",
        files={"file": ("test.gif", create_image("GIF"), "image/gif")}
    )

    assert response.status_code == 400


def test_small_image_rejected():
    response = client.post(
        "/api/v1/upload",
        files={
            "file": (
                "small.png",
                create_image("PNG", (100, 100)),
                "image/png"
            )
        }
    )

    assert response.status_code == 400


def test_oversized_file_rejected():
    response = client.post(
        "/api/v1/upload",
        files={
            "file": (
                "large.jpg",
                b"A" * (upload.MAX_FILE_SIZE + 1),
                "image/jpeg"
            )
        }
    )

    assert response.status_code == 400
