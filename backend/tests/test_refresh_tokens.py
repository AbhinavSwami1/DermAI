from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select

from app.core.refresh_tokens import hash_refresh_token
from app.models import RefreshToken, User
from app.services.refresh_token_service import create_refresh_token


def test_refresh_token_persistence(client, db_session):
    # Create a real user.
    response = client.post(
        "/api/v1/users/register",
        json={
            "email": "refresh-test@dermai.com",
            "password": "SecurePass@123",
            "full_name": "Refresh Token Test",
        },
    )

    assert response.status_code == 201

    user = db_session.scalar(
        select(User).where(User.email == "refresh-test@dermai.com")
    )
    assert user is not None

    # Generate and persist a refresh token.
    raw_token, token_record = create_refresh_token(
        db_session,
        user.user_id,
    )

    stored_token = db_session.get(
        RefreshToken,
        token_record.token_id,
    )

    assert stored_token is not None
    assert stored_token.user_id == user.user_id
    assert stored_token.token_hash == hash_refresh_token(raw_token)
    assert stored_token.token_hash != raw_token
    assert len(stored_token.token_hash) == 64
    assert isinstance(stored_token.family_id, UUID)
    assert stored_token.revoked_at is None


def test_refresh_token_expiry_is_seven_days(client, db_session):
    response = client.post(
        "/api/v1/users/register",
        json={
            "email": "refresh-expiry@dermai.com",
            "password": "SecurePass@123",
            "full_name": "Refresh Expiry Test",
        },
    )

    assert response.status_code == 201

    user = db_session.scalar(
        select(User).where(User.email == "refresh-expiry@dermai.com")
    )
    assert user is not None

    before_creation = datetime.now(timezone.utc)

    _, token_record = create_refresh_token(
        db_session,
        user.user_id,
    )

    after_creation = datetime.now(timezone.utc)

    expected_min = before_creation + timedelta(days=7)
    expected_max = after_creation + timedelta(days=7)

    assert expected_min <= token_record.expires_at <= expected_max

def test_refresh_token_rotation(client, db_session):
    response = client.post(
        "/api/v1/users/register",
        json={
            "email": "rotation-test@dermai.com",
            "password": "SecurePass@123",
            "full_name": "Rotation Test",
        },
    )
    assert response.status_code == 201

    user = db_session.scalar(
        select(User).where(User.email == "rotation-test@dermai.com")
    )

    old_raw_token, old_record = create_refresh_token(
        db_session, user.user_id
    )

    from app.services.refresh_token_service import rotate_refresh_token

    result = rotate_refresh_token(db_session, old_raw_token)

    assert result is not None

    new_raw_token, new_record = result

    db_session.refresh(old_record)

    assert new_raw_token != old_raw_token
    assert new_record.family_id == old_record.family_id
    assert old_record.revoked_at is not None
    assert old_record.replaced_by_token_id == new_record.token_id
    assert new_record.revoked_at is None


def test_reuse_of_rotated_token_revokes_family(client, db_session):
    response = client.post(
        "/api/v1/users/register",
        json={
            "email": "reuse-test@dermai.com",
            "password": "SecurePass@123",
            "full_name": "Reuse Test",
        },
    )
    assert response.status_code == 201

    user = db_session.scalar(
        select(User).where(User.email == "reuse-test@dermai.com")
    )

    old_raw_token, old_record = create_refresh_token(
        db_session, user.user_id
    )

    from app.services.refresh_token_service import rotate_refresh_token

    new_raw_token, new_record = rotate_refresh_token(
        db_session, old_raw_token
    )

    # Reuse the old, already-rotated token.
    result = rotate_refresh_token(db_session, old_raw_token)

    assert result is None

    db_session.refresh(new_record)

    assert new_record.revoked_at is not None

def test_login_sets_secure_refresh_cookie(client, db_session):
    email = "refresh-cookie@dermai.com"
    password = "SecurePass@123"

    # Register user.
    registration = client.post(
        "/api/v1/users/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Cookie Test",
        },
    )
    assert registration.status_code == 201

    # Login.
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "refresh_token" not in response.json()

    # Verify refresh cookie.
    cookie = response.cookies.get("dermai_refresh_token")
    assert cookie is not None

    cookie_header = response.headers.get("set-cookie", "").lower()

    assert "httponly" in cookie_header
    assert "samesite=lax" in cookie_header
    assert "path=/api/v1/auth" in cookie_header

    # Verify hashed token exists in the database.
    from app.core.refresh_tokens import hash_refresh_token

    stored_token = db_session.query(RefreshToken).filter_by(
        token_hash=hash_refresh_token(cookie)
    ).first()

    assert stored_token is not None
    assert stored_token.revoked_at is None


def test_refresh_api_rotates_cookie_and_access_token(client, db_session):
    email = "refresh-api@dermai.com"
    password = "SecurePass@123"

    registration = client.post(
        "/api/v1/users/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Refresh API Test",
        },
    )
    assert registration.status_code == 201

    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200

    old_access_token = login.json()["access_token"]
    old_refresh_token = login.cookies.get("dermai_refresh_token")
    assert old_refresh_token is not None

    refresh = client.post("/api/v1/auth/refresh")

    assert refresh.status_code == 200
    assert refresh.json()["access_token"] != old_access_token

    new_refresh_token = refresh.cookies.get("dermai_refresh_token")
    assert new_refresh_token is not None
    assert new_refresh_token != old_refresh_token

    old_record = db_session.query(RefreshToken).filter_by(
        token_hash=hash_refresh_token(old_refresh_token)
    ).first()

    new_record = db_session.query(RefreshToken).filter_by(
        token_hash=hash_refresh_token(new_refresh_token)
    ).first()

    assert old_record is not None
    assert old_record.revoked_at is not None
    assert new_record is not None
    assert new_record.revoked_at is None
    assert old_record.family_id == new_record.family_id

def test_logout_revokes_refresh_token_and_clears_cookie(client, db_session):
    email = "logout-test@dermai.com"
    password = "SecurePass@123"

    registration = client.post(
        "/api/v1/users/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Logout Test",
        },
    )
    assert registration.status_code == 201

    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200

    raw_token = login.cookies.get("dermai_refresh_token")
    assert raw_token is not None

    stored_token = db_session.query(RefreshToken).filter_by(
        token_hash=hash_refresh_token(raw_token)
    ).first()

    assert stored_token is not None
    assert stored_token.revoked_at is None

    logout = client.post("/api/v1/auth/logout")

    assert logout.status_code == 200
    assert logout.json()["message"] == "Logged out successfully."

    db_session.refresh(stored_token)
    assert stored_token.revoked_at is not None

    cookie_header = logout.headers.get("set-cookie", "").lower()
    assert "dermai_refresh_token" in cookie_header
    assert "max-age=0" in cookie_header

def test_refresh_api_rejects_reused_token(client, db_session):
    email = "replay-test@dermai.com"
    password = "SecurePass@123"

    registration = client.post(
        "/api/v1/users/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Replay Test",
        },
    )
    assert registration.status_code == 201

    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )

    old_token = login.cookies.get("dermai_refresh_token")
    assert old_token is not None

    # First refresh rotates the token.
    first_refresh = client.post("/api/v1/auth/refresh")
    assert first_refresh.status_code == 200

    # Replay the old token.
    replay = client.post(
        "/api/v1/auth/refresh",
        cookies={"dermai_refresh_token": old_token},
    )

    assert replay.status_code == 401

    # The newly issued token must also be revoked.
    new_token = first_refresh.cookies.get("dermai_refresh_token")

    new_record = db_session.query(RefreshToken).filter_by(
        token_hash=hash_refresh_token(new_token)
    ).first()

    assert new_record is not None
    db_session.refresh(new_record)
    assert new_record.revoked_at is not None