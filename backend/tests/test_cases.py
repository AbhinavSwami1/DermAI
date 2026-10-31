from uuid import uuid4

from app.models import Case


def create_authenticated_user(client):
    unique_id = uuid4().hex

    register_response = client.post(
        "/api/v1/users/register",
        json={
            "email": f"{unique_id}@dermai.com",
            "password": "SecurePass@123",
            "full_name": "Case Test User",
        },
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": f"{unique_id}@dermai.com",
            "password": "SecurePass@123",
        },
    )

    assert login_response.status_code == 200

    user_id = register_response.json()["user_id"]
    token = login_response.json()["access_token"]

    return user_id, {
        "Authorization": f"Bearer {token}"
    }


def test_create_case_success(client, db_session):
    user_id, headers = create_authenticated_user(client)

    response = client.post(
        "/api/v1/cases",
        headers=headers,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["owner_id"] == user_id
    assert data["status"] == "created"

    case = db_session.get(Case, data["case_id"])
    assert case is not None


def test_create_case_without_token(client):
    response = client.post("/api/v1/cases")

    assert response.status_code == 401


def test_get_user_cases(client):
    user_id, headers = create_authenticated_user(client)

    client.post("/api/v1/cases", headers=headers)

    response = client.get(
        f"/api/v1/users/{user_id}/cases",
        headers=headers,
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["owner_id"] == user_id


def test_user_cannot_access_another_users_cases(client):
    user_id, _ = create_authenticated_user(client)
    _, other_headers = create_authenticated_user(client)

    response = client.get(
        f"/api/v1/users/{user_id}/cases",
        headers=other_headers,
    )

    assert response.status_code == 403


def test_get_single_case(client):
    _, headers = create_authenticated_user(client)

    create_response = client.post(
        "/api/v1/cases",
        headers=headers,
    )

    case_id = create_response.json()["case_id"]

    response = client.get(
        f"/api/v1/cases/{case_id}",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["case_id"] == case_id


def test_user_cannot_access_another_users_case(client):
    _, owner_headers = create_authenticated_user(client)
    _, other_headers = create_authenticated_user(client)

    create_response = client.post(
        "/api/v1/cases",
        headers=owner_headers,
    )

    case_id = create_response.json()["case_id"]

    response = client.get(
        f"/api/v1/cases/{case_id}",
        headers=other_headers,
    )

    assert response.status_code == 404


def test_get_nonexistent_case(client):
    _, headers = create_authenticated_user(client)

    response = client.get(
        f"/api/v1/cases/{uuid4()}",
        headers=headers,
    )

    assert response.status_code == 404