from datetime import UTC, datetime, timedelta

import jwt
from fastapi.testclient import TestClient

from app.core.config import get_settings
from tests.conftest import USERNAME


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_me_returns_current_user(client: TestClient, tokens: dict) -> None:
    response = client.get("/users/me", headers=auth_header(tokens["access_token"]))

    assert response.status_code == 200
    assert response.json()["username"] == USERNAME


def test_me_without_token_returns_401(client: TestClient) -> None:
    assert client.get("/users/me").status_code == 401


def test_me_rejects_refresh_token(client: TestClient, tokens: dict) -> None:
    response = client.get("/users/me", headers=auth_header(tokens["refresh_token"]))
    assert response.status_code == 401


def test_me_rejects_expired_token(client: TestClient, registered_user: dict) -> None:
    settings = get_settings()
    past = datetime.now(UTC) - timedelta(minutes=5)
    token = jwt.encode(
        {"sub": USERNAME, "type": "access", "iat": past, "exp": past},
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )

    assert client.get("/users/me", headers=auth_header(token)).status_code == 401


def test_me_rejects_token_signed_with_other_key(client: TestClient, registered_user: dict) -> None:
    token = jwt.encode(
        {"sub": USERNAME, "type": "access", "exp": datetime.now(UTC) + timedelta(minutes=5)},
        "another-secret-key-that-is-long-enough-123",
        algorithm="HS256",
    )

    assert client.get("/users/me", headers=auth_header(token)).status_code == 401


def test_health(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "ok"}
