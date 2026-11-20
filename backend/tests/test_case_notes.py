from uuid import uuid4



def create_authenticated_user(client):
    unique_id = uuid4().hex
    body = {"email": f"{unique_id}@dermai.com", "password": "SecurePass@123"}
    reg = client.post("/api/v1/users/register", json={**body, "full_name": "Notes Test User"})
    assert reg.status_code == 201
    login = client.post("/api/v1/auth/login", json=body)
    assert login.status_code == 200
    return reg.json()["user_id"], {"Authorization": f"Bearer {login.json()['access_token']}"}


def _case(client, db_session):
    user_id, headers = create_authenticated_user(client)
    r = client.post("/api/v1/cases", headers=headers)
    assert r.status_code in (200, 201), r.text
    return r.json()["case_id"], headers


def test_notes_roundtrip_and_owner_only(client, db_session):
    case_id, headers = _case(client, db_session)
    r = client.patch(f"/api/v1/cases/{case_id}/notes", headers=headers,
                     json={"clinical_notes": "  check in 2 weeks ", "follow_up_date": "2030-01-15"})
    assert r.status_code == 200
    assert r.json()["clinical_notes"] == "check in 2 weeks"
    assert r.json()["follow_up_date"] == "2030-01-15"
    assert client.get(f"/api/v1/cases/{case_id}", headers=headers).json()["clinical_notes"] == "check in 2 weeks"

    _, other = create_authenticated_user(client)
    assert client.patch(f"/api/v1/cases/{case_id}/notes", headers=other,
                        json={"clinical_notes": "x"}).status_code == 404


def test_notes_validation_and_auth(client, db_session):
    case_id, headers = _case(client, db_session)
    assert client.patch(f"/api/v1/cases/{case_id}/notes", headers=headers,
                        json={"clinical_notes": "a" * 2001}).status_code == 422
    assert client.patch(f"/api/v1/cases/{case_id}/notes", headers=headers,
                        json={"follow_up_date": "not-a-date"}).status_code == 422
    assert client.patch(f"/api/v1/cases/{case_id}/notes",
                        json={"clinical_notes": "x"}).status_code == 401


def test_history_date_filter(client, db_session):
    _, headers = create_authenticated_user(client)
    ok = client.get("/api/v1/predictions/history?date_from=2030-01-01", headers=headers)
    assert ok.status_code == 200 and ok.json()["total"] == 0
    bad = client.get("/api/v1/predictions/history?date_from=2030-02-01&date_to=2030-01-01", headers=headers)
    assert bad.status_code == 422


def test_notifications_follow_up_and_auth(client, db_session):
    assert client.get("/api/v1/notifications").status_code == 401
    case_id, headers = _case(client, db_session)
    client.patch(f"/api/v1/cases/{case_id}/notes", headers=headers,
                 json={"follow_up_date": "2000-01-01"})
    data = client.get("/api/v1/notifications", headers=headers).json()
    assert any(i["type"] == "follow_up_due" and i["case_id"] == case_id for i in data["items"])
