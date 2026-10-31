import pytest

from app.core.rate_limit import limiter


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    limiter.reset()
    yield
    limiter.reset()


def test_login_rate_limit_blocks_sixth_attempt(client):
    payload = {
        "email": "nonexistent@dermai.com",
        "password": "WrongPassword@123",
    }

    for attempt in range(5):
        response = client.post(
            "/api/v1/auth/login",
            json=payload,
        )
        assert response.status_code == 401, (
            f"Attempt {attempt + 1} returned {response.status_code}"
        )

    response = client.post(
        "/api/v1/auth/login",
        json=payload,
    )

    assert response.status_code == 429