from uuid import uuid4

from app.core.security import verify_password
from app.models import User
from sqlalchemy import select
from app.models import Role, User, UserRole
from app.core.database import get_db


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

def test_new_user_receives_patient_role(client, db_session):
    response = client.post(
        "/api/v1/users/register",
        json={
            "email": "patient-role-test@dermai.com",
            "password": "SecurePass@123",
            "full_name": "Patient Role Test",
        },
    )

    assert response.status_code == 201

    user = db_session.scalar(
        select(User).where(
            User.email == "patient-role-test@dermai.com"
        )
    )

    assert user is not None

    assigned_role = db_session.scalar(
        select(Role.role_name)
        .join(UserRole, UserRole.role_id == Role.role_id)
        .where(UserRole.user_id == user.user_id)
    )

    assert assigned_role == "Patient"

def test_patient_role_is_not_administrator(client):
    token = create_authenticated_user(client)

    from app.core.auth import require_roles
    from fastapi import Depends, FastAPI
    from fastapi.testclient import TestClient

    role_test_app = FastAPI()
    role_test_app.dependency_overrides[get_db] = client.app.dependency_overrides[get_db]

    @role_test_app.get("/admin-only")
    def admin_only(
        user=Depends(require_roles("Administrator")),
    ):
        return {"message": "Administrator access granted"}

    role_client = TestClient(role_test_app)

    response = role_client.get(
        "/admin-only",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403