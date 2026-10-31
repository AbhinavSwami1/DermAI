from uuid import uuid4

from sqlalchemy import select

from app.models import User, Role, UserRole


def create_authenticated_user(client):
    unique_id = uuid4().hex
    email = f"{unique_id}@dermai.com"
    password = "SecurePass@123"

    response = client.post(
        "/api/v1/users/register",
        json={
            "email": email,
            "password": password,
            "full_name": "RBAC Test User",
        },
    )

    assert response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert login_response.status_code == 200

    user = client.get(
        "/api/v1/users/me",
        headers={
            "Authorization": f"Bearer {login_response.json()['access_token']}"
        },
    )

    return user.json()["user_id"], {
        "Authorization": f"Bearer {login_response.json()['access_token']}"
    }


def test_user_can_view_own_roles(client):
    user_id, headers = create_authenticated_user(client)

    response = client.get(
        "/api/v1/roles/me",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["user_id"] == user_id
    assert response.json()["roles"] == ["Patient"]


def test_view_roles_without_token_rejected(client):
    response = client.get("/api/v1/roles/me")

    assert response.status_code == 401


def test_patient_cannot_assign_roles(client):
    _, headers = create_authenticated_user(client)

    target_id, _ = create_authenticated_user(client)

    response = client.post(
        f"/api/v1/roles/users/{target_id}",
        json={"role_name": "Dermatologist"},
        headers=headers,
    )

    assert response.status_code == 403


def test_administrator_can_assign_role(client, db_session):
    admin_id, admin_headers = create_authenticated_user(client)
    target_id, _ = create_authenticated_user(client)

    admin = db_session.scalar(
        select(User).where(User.user_id == admin_id)
    )

    admin_role = db_session.scalar(
        select(Role).where(Role.role_name == "Administrator")
    )

    if admin_role is None:
        admin_role = Role(
            role_name="Administrator",
            description="System administrator",
        )
        db_session.add(admin_role)
        db_session.flush()

    db_session.add(
        UserRole(
            user_id=admin.user_id,
            role_id=admin_role.role_id,
        )
    )
    db_session.flush()

    response = client.post(
        f"/api/v1/roles/users/{target_id}",
        json={"role_name": "Dermatologist"},
        headers=admin_headers,
    )

    assert response.status_code == 200
    assert "Dermatologist" in response.json()["roles"]


def test_duplicate_role_assignment_is_prevented(client, db_session):
    admin_id, admin_headers = create_authenticated_user(client)
    target_id, _ = create_authenticated_user(client)

    admin = db_session.scalar(
        select(User).where(User.user_id == admin_id)
    )

    admin_role = Role(
        role_name="Administrator",
        description="System administrator",
    )
    db_session.add(admin_role)
    db_session.flush()

    db_session.add(
        UserRole(
            user_id=admin.user_id,
            role_id=admin_role.role_id,
        )
    )
    db_session.flush()

    payload = {"role_name": "Dermatologist"}

    first_response = client.post(
        f"/api/v1/roles/users/{target_id}",
        json=payload,
        headers=admin_headers,
    )

    second_response = client.post(
        f"/api/v1/roles/users/{target_id}",
        json=payload,
        headers=admin_headers,
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert second_response.json()["roles"].count("Dermatologist") == 1