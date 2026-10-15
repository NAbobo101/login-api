from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select

from app.core.security import InvalidTokenError, TokenType, decode_token
from app.db import get_session
from app.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

SessionDep = Annotated[Session, Depends(get_session)]


def credentials_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_active_user_by_username(session: Session, username: str) -> User | None:
    user = session.exec(select(User).where(User.username == username)).first()
    if user is None or not user.is_active:
        return None
    return user


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], session: SessionDep) -> User:
    try:
        username = decode_token(token, TokenType.ACCESS)
    except InvalidTokenError:
        raise credentials_exception() from None

    user = get_active_user_by_username(session, username)
    if user is None:
        raise credentials_exception()
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
