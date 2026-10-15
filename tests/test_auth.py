import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models import User
from tests.conftest import PASSWORD, USERNAME


def test_register_creates_user(client: TestClient, session: Session) -> None:
    response = client.post("/auth/register", json={"username": USERNAME, "password": PASSWORD})

    assert response.status_code == 201
    body = response.json()
    assert body["username"] == USERNAME
    assert body["is_active"] is True
    assert "password" not in body and "hashed_password" not in body

    user = session.exec(select(User)).one()
    assert user.hashed_password != PASSWORD


def test_register_duplicate_username_returns_409(client: TestClient, registered_user: dict) -> None:
    response = client.post("/auth/register", json={"username": USERNAME, "password": PASSWORD})
    assert response.status_code == 409


@pytest.mark.parametrize(
    "payload",
    [
        {"username": "ab", "password": PASSWORD},
        {"username": "invalid name!", "password": PASSWORD},
        {"username": USERNAME, "password": "short"},
        {"username": USERNAME},
    ],
)
def test_register_rejects_invalid_payload(client: TestClient, payload: dict) -> None:
    assert client.post("/auth/register", json=payload).status_code == 422


def test_login_returns_token_pair(tokens: dict) -> None:
    assert tokens["token_type"] == "bearer"
    assert tokens["access_token"]
    assert tokens["refresh_token"]


@pytest.mark.parametrize(
    ("username", "password"),
    [(USERNAME, "wrong-password"), ("unknown_user", PASSWORD)],
)
def test_login_with_invalid_credentials_returns_401(
    client: TestClient, registered_user: dict, username: str, password: str
) -> None:
    response = client.post("/auth/login", data={"username": username, "password": password})

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"


def test_login_inactive_user_returns_401(client: TestClient, session: Session, registered_user: dict) -> None:
    user = session.exec(select(User)).one()
    user.is_active = False
    session.add(user)
    session.commit()

    response = client.post("/auth/login", data={"username": USERNAME, "password": PASSWORD})
    assert response.status_code == 401


def test_refresh_returns_new_tokens(client: TestClient, tokens: dict) -> None:
    response = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})

    assert response.status_code == 200
    new_tokens = response.json()
    me = client.get("/users/me", headers={"Authorization": f"Bearer {new_tokens['access_token']}"})
    assert me.status_code == 200


def test_refresh_rejects_access_token(client: TestClient, tokens: dict) -> None:
    response = client.post("/auth/refresh", json={"refresh_token": tokens["access_token"]})
    assert response.status_code == 401


def test_refresh_rejects_garbage(client: TestClient) -> None:
    response = client.post("/auth/refresh", json={"refresh_token": "not-a-jwt"})
    assert response.status_code == 401
