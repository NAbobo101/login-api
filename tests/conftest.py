import os

os.environ.setdefault("SECRET_KEY", "test-secret-key-that-is-long-enough-for-hs256")
os.environ.setdefault("DATABASE_URL", "sqlite://")

from collections.abc import Iterator  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402
from sqlmodel import Session, SQLModel, create_engine  # noqa: E402

from app.db import get_session  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def session() -> Iterator[Session]:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture
def client(session: Session) -> Iterator[TestClient]:
    app.dependency_overrides[get_session] = lambda: session
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


USERNAME = "john_doe"
PASSWORD = "S3cure-passw0rd"


@pytest.fixture
def registered_user(client: TestClient) -> dict:
    response = client.post("/auth/register", json={"username": USERNAME, "password": PASSWORD})
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def tokens(client: TestClient, registered_user: dict) -> dict:
    response = client.post("/auth/login", data={"username": USERNAME, "password": PASSWORD})
    assert response.status_code == 200
    return response.json()
