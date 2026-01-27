# PYTHON CHALLENGE - 001 FastAPI
#USING FASTAPI TO CREATE A LOGIN API
from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional
import secrets


from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlmodel import Field, Session, SQLModel, create_engine, select
from sqlalchemy import UniqueConstraint


SECRET_KEY = "2bab70a280371c284b0c265e978fc6063c2b8b5e9d5cd97f2828e7867534a833"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# DATABASE SETUP
sqlite_url = "sqlite:///database.db"
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False}, echo=False)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

# SQL MODELS
class UserBase(SQLModel):
    username: str = Field(index=True)

class User(UserBase, table=True):
    __table_args__ = (UniqueConstraint('username'),)
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str
    is_active: bool = True
    create_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(UserBase):
    password: str

class UserRead(UserBase):
    id: int
    is_active: bool
    create_at: datetime

class Token(SQLModel):
    access_token: str
    token_type: str


# SECURITY SETUP
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oaut2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)

def create_acess_token(*, subject: str, expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    to_encode = {"sub": subject, "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def authenticate_user(session: Session, username: str, password: str) -> Optional[User]:
    user = session.exec(select(User).where(User.username == username))
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        return None
    return user

def get_current_user(
        token: Annotated[str, Depends(oaut2_scheme)],
        session: SessionDep,
) -> User:
    credentials_exception = HttpException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if not username:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = session.exec(select(User).where(User.username == username)).first()
    if not user or not user.is_active:
        raise credentials_exception
    return user

# FASTAPI APP
app = FastAPI()


@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.post("/users/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(user_in: UserCreate, session: SessionDep):
    existing = session.exec(select(User).where(User.username == user_in.username)).first()
    if existing:
        raise HttpException(status_code=409, detail="Username already registered (Esse nome de usuario ja existe)")
    user = User(
        username=user_in.username,
        hashed_password=hash_password(user_in.password),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@app.post("/token")
def login_for_acess_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: SessionDep,
):
    user = authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HttpException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username or Password incorrect (Usuário ou senha incorretos)",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_acess_token(subject=user.username)
    return Token(acess_token=token)

@app.get("/me", response_model=UserRead)
def read_me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user


