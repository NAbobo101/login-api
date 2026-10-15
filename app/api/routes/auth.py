from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select

from app.core.security import (
    DUMMY_HASH,
    InvalidTokenError,
    TokenType,
    create_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.deps import SessionDep, credentials_exception, get_active_user_by_username
from app.models import User
from app.schemas import Message, RefreshRequest, Token, UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


def authenticate(session: Session, username: str, password: str) -> User | None:
    user = session.exec(select(User).where(User.username == username)).first()
    if user is None:
        # Run a hash check anyway so response time doesn't reveal whether the user exists.
        verify_password(password, DUMMY_HASH)
        return None
    if not verify_password(password, user.hashed_password) or not user.is_active:
        return None
    return user


def issue_tokens(username: str) -> Token:
    return Token(
        access_token=create_token(username, TokenType.ACCESS),
        refresh_token=create_token(username, TokenType.REFRESH),
    )


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_409_CONFLICT: {"model": Message}},
)
def register(user_in: UserCreate, session: SessionDep) -> User:
    """Create a new user account."""
    existing = session.exec(select(User).where(User.username == user_in.username)).first()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already registered")

    user = User(username=user_in.username, hashed_password=hash_password(user_in.password))
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@router.post("/login", response_model=Token, responses={status.HTTP_401_UNAUTHORIZED: {"model": Message}})
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], session: SessionDep) -> Token:
    """Exchange username and password for an access/refresh token pair (OAuth2 password flow)."""
    user = authenticate(session, form_data.username, form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return issue_tokens(user.username)


@router.post("/refresh", response_model=Token, responses={status.HTTP_401_UNAUTHORIZED: {"model": Message}})
def refresh(body: RefreshRequest, session: SessionDep) -> Token:
    """Exchange a valid refresh token for a new token pair."""
    try:
        username = decode_token(body.refresh_token, TokenType.REFRESH)
    except InvalidTokenError:
        raise credentials_exception() from None

    if get_active_user_by_username(session, username) is None:
        raise credentials_exception()
    return issue_tokens(username)
