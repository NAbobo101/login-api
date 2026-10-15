from fastapi import APIRouter

from app.deps import CurrentUser
from app.models import User
from app.schemas import UserRead

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
def read_me(current_user: CurrentUser) -> User:
    """Return the authenticated user's profile."""
    return current_user
