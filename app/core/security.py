from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any
from uuid import uuid4

import jwt
from pwdlib import PasswordHash

from app.core.config import get_settings

password_hash = PasswordHash.recommended()

# Used to keep login timing constant when the username does not exist.
DUMMY_HASH = password_hash.hash("dummy-password-for-timing-safety")


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"


class InvalidTokenError(Exception):
    """Raised when a JWT is malformed, expired, or of the wrong type."""


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


def create_token(subject: str, token_type: TokenType) -> str:
    settings = get_settings()
    minutes = (
        settings.access_token_expire_minutes
        if token_type is TokenType.ACCESS
        else settings.refresh_token_expire_minutes
    )
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type.value,
        "iat": now,
        "exp": now + timedelta(minutes=minutes),
        "jti": uuid4().hex,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str, expected_type: TokenType) -> str:
    """Validate a token and return its subject."""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["sub", "exp", "type"]},
        )
    except jwt.PyJWTError as exc:
        raise InvalidTokenError from exc

    if payload.get("type") != expected_type.value:
        raise InvalidTokenError
    return payload["sub"]
