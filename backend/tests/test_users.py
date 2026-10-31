from app.core.security import verify_password
from app.models import User


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