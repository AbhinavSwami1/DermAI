from uuid import uuid4

from app.models import Role, UserRole


def make_user(client, db_session, role=None):
    unique = uuid4().hex
    body = {"email": f"{unique}@dermai.com", "password": "SecurePass@123"}
    reg = client.post("/api/v1/users/register", json={**body, "full_name": "Role Test User"})
    assert reg.status_code == 201
    user_id = reg.json()["user_id"]
    if role:
        row = db_session.query(Role).filter(Role.role_name == role).first()
        if row is None:
            row = Role(role_name=role, description=f"{role} role.")
            db_session.add(row)
            db_session.flush()
        db_session.add(UserRole(user_id=user_id, role_id=row.role_id))
        db_session.flush()
    login = client.post("/api/v1/auth/login", json=body)
    assert login.status_code == 200
    return user_id, {"Authorization": f"Bearer {login.json()['access_token']}"}


STAFF = ["/api/v1/dashboard/clinician", "/api/v1/dashboard/research", "/api/v1/dashboard/admin", "/api/v1/admin/users"]


def test_patient_is_denied_staff_endpoints_but_can_read_model_info(client, db_session):
    _, h = make_user(client, db_session)
    for url in STAFF + ["/api/v1/insights/model-metrics"]:
        assert client.get(url, headers=h).status_code == 403, url
    assert client.get("/api/v1/insights/model-info", headers=h).status_code == 200
    assert client.get("/api/v1/roles/me", headers=h).json()["roles"] == ["Patient"]


def test_dermatologist_access(client, db_session):
    _, h = make_user(client, db_session, "Dermatologist")
    assert client.get("/api/v1/dashboard/clinician", headers=h).status_code == 200
    assert client.get("/api/v1/insights/model-metrics", headers=h).status_code == 200
    for url in ("/api/v1/dashboard/research", "/api/v1/dashboard/admin", "/api/v1/admin/users"):
        assert client.get(url, headers=h).status_code == 403, url


def test_researcher_and_data_scientist_access_is_deidentified(client, db_session):
    for role in ("Medical Researcher", "Data Scientist"):
        _, h = make_user(client, db_session, role)
        r = client.get("/api/v1/dashboard/research", headers=h)
        assert r.status_code == 200
        assert "recent_analyses" not in r.json() and "case_id" not in str(r.json())
        assert client.get("/api/v1/insights/model-metrics", headers=h).status_code == 200
        for url in ("/api/v1/dashboard/clinician", "/api/v1/dashboard/admin", "/api/v1/admin/users"):
            assert client.get(url, headers=h).status_code == 403, (role, url)


def test_administrator_access_and_role_management(client, db_session):
    _, admin = make_user(client, db_session, "Administrator")
    for url in STAFF[:3] + ["/api/v1/insights/model-metrics"]:
        assert client.get(url, headers=admin).status_code == 200, url
    target_id, target = make_user(client, db_session)

    users = client.get("/api/v1/admin/users", headers=admin).json()["users"]
    assert any(u["user_id"] == target_id and u["roles"] == ["Patient"] for u in users)

    assert client.get("/api/v1/dashboard/clinician", headers=target).status_code == 403
    assign = client.post(f"/api/v1/roles/users/{target_id}", headers=admin, json={"role_name": "Dermatologist"})
    assert assign.status_code == 200
    assert client.get("/api/v1/dashboard/clinician", headers=target).status_code == 200

    revoke = client.delete(f"/api/v1/admin/users/{target_id}/roles/Dermatologist", headers=admin)
    assert revoke.status_code == 200 and "Dermatologist" not in revoke.json()["roles"]
    assert client.get("/api/v1/dashboard/clinician", headers=target).status_code == 403
    assert client.delete(f"/api/v1/admin/users/{target_id}/roles/Dermatologist", headers=admin).status_code == 404


def test_administrator_cannot_remove_own_admin_role(client, db_session):
    admin_id, admin = make_user(client, db_session, "Administrator")
    r = client.delete(f"/api/v1/admin/users/{admin_id}/roles/Administrator", headers=admin)
    assert r.status_code == 400


def test_role_endpoints_require_authentication(client):
    for url in STAFF + ["/api/v1/insights/model-info", "/api/v1/insights/model-metrics"]:
        assert client.get(url).status_code == 401, url
