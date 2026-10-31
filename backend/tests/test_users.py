from uuid import uuid4

from app.core.security import verify_password
from app.models import User


def create_authenticated_user(client):
    unique_id = uuid4().hex
    email = f"{unique_id}@dermai.com"
    password = "SecurePass@123"

    register_response = client.post(
        "/api/v1/users/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Test User",
        },
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert login_response.status_code == 200

    return login_response.json()["access_token"]


def test_user_registration_success(client, db_session):
    response = client.post(
        "/api/v1/users/register",
        json={
            "email": "testuser@dermai.com",
            "password": "SecurePass@123",
            "full_name": "Test User",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == "testuser@dermai.com"
    assert data["full_name"] == "Test User"
    assert "password" not in data
    assert "password_hash" not in data

    user = db_session.query(User).filter_by(
        email="testuser@dermai.com"
    ).first()

    assert user is not None
    assert user.password_hash != "SecurePass@123"
    assert verify_password("SecurePass@123", user.password_hash)


def test_duplicate_email_rejected(client):
    payload = {
        "email": "duplicate@dermai.com",
        "password": "SecurePass@123",
        "full_name": "Test User",
    }

    first_response = client.post(
        "/api/v1/users/register",
        json=payload,
    )

    second_response = client.post(
        "/api/v1/users/register",
        json=payload,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_invalid_email_rejected(client):
    response = client.post(
        "/api/v1/users/register",
        json={
            "email": "invalid-email",
            "password": "SecurePass@123",
            "full_name": "Test User",
        },
    )

    assert response.status_code == 422


def test_current_user_profile_success(client):
    token = create_authenticated_user(client)

    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["email"] is not None
    assert response.json()["full_name"] == "Test User"
    assert "password_hash" not in response.json()


def test_current_user_profile_without_token(client):
    response = client.get("/api/v1/users/me")

    assert response.status_code == 401


def test_current_user_profile_invalid_token(client):
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401