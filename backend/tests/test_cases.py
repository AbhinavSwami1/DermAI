from uuid import uuid4

from app.models import Case


def create_test_user(client):
    response = client.post(
        "/api/v1/users/register",
        json={
            "email": "caseuser@dermai.com",
            "password": "SecurePass@123",
            "full_name": "Case Test User",
        },
    )

    assert response.status_code == 201
    return response.json()["user_id"]


def test_create_case_success(client, db_session):
    user_id = create_test_user(client)

    response = client.post(
        "/api/v1/cases",
        json={"owner_id": user_id},
    )

    assert response.status_code == 201

    data = response.json()

    assert data["owner_id"] == user_id
    assert data["status"] == "created"

    case = db_session.get(Case, data["case_id"])
    assert case is not None


def test_create_case_user_not_found(client):
    response = client.post(
        "/api/v1/cases",
        json={"owner_id": str(uuid4())},
    )

    assert response.status_code == 404


def test_get_user_cases(client):
    user_id = create_test_user(client)

    client.post(
        "/api/v1/cases",
        json={"owner_id": user_id},
    )

    response = client.get(
        f"/api/v1/users/{user_id}/cases"
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["owner_id"] == user_id


def test_get_single_case(client):
    user_id = create_test_user(client)

    create_response = client.post(
        "/api/v1/cases",
        json={"owner_id": user_id},
    )

    case_id = create_response.json()["case_id"]

    response = client.get(f"/api/v1/cases/{case_id}")

    assert response.status_code == 200
    assert response.json()["case_id"] == case_id


def test_get_nonexistent_case(client):
    response = client.get(f"/api/v1/cases/{uuid4()}")

    assert response.status_code == 404