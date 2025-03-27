from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from pydantic import BaseModel


SECRET_KEY = "11b076f406d8298b4199c4dfbb4f2fd7d0d93f3d1ae4140c43f56a1c3cd6956b"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


conference_users_db = {
    "admin": {
        "username": "admin",
        "first_name": "admin",
        "last_name": "admin",
        "email": "admin@example.com",
        "hashed_password": "$2b$12$P1DsWNCa0fKQEIMLy6NYYuYMRDFE5y0nC5R1.YysXaLjU.Cpc6XIW",
        "disabled": False,
    }
}


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class UserNoneAuth(BaseModel):
    username: str
    email: str 
    first_name: str
    last_name: str


class ConferenceUser(BaseModel):
    username: str
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    disabled: bool | None = None


class ConferenceUserInDB(ConferenceUser):
    hashed_password: str


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI(title="UserControlAPP")

users_db = [
    {
        "id": 0,
        "username": "Solomonov_Pantelemon",
        "first_name": "Pantelemon",
        "last_name": "Solomonov",
        "email": "Solomonov.Pantelemon@example.com"
    },
    {
        "id": 1,
        "username": "Prostov_Vasilyi",
        "first_name": "Vasilyi",
        "last_name": "Prostov",
        "email": "Prostov.Vasilyi@example.com"
    }]


@app.get(
        "/conference_users",
        summary="endpoint для обычного получения всех пользователей без авториазации",
        tags=["Взаимодействие с пользователями без авторизации"])
def get_conference_users():
    return users_db


@app.get(
        "/conference_users/{user_id}",
        summary="endpoint для обычного получения пользователя по его id без авториазации",
        tags=["Взаимодействие с пользователями без авторизации"])
def get_user(user_id: int):
    for conference_user in users_db:
        if user_id == conference_user["id"]:
            return conference_user
    raise HTTPException(status_code=404, detail="User not found")


@app.post(
        "/conference_users",
        summary="endpoint для обычного создания пользователя без авториазации",
        tags=["Взаимодействие с пользователями без авторизации"])
def create_user(conference_user: UserNoneAuth):
    users_db.append({
        "id": len(users_db) + 1, 
        "username": conference_user.username,
        "email": conference_user.email,
        "first_name": conference_user.first_name,
        "last_name": conference_user.last_name
    })
    return {"success": True}


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_conference_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return ConferenceUserInDB(**user_dict)


def authenticate_user(db, username: str, password: str):
    conference_user = get_conference_user(db, username)
    if not conference_user:
        return False
    if not verify_password(password, conference_user.hashed_password):
        return False
    return conference_user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_conference_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    conference_user = get_conference_user(conference_users_db, username=token_data.username)
    if conference_user is None:
        raise credentials_exception
    return conference_user


async def get_current_active_conference_user(
    current_conference_user: Annotated[ConferenceUser, Depends(get_current_conference_user)],
):
    if current_conference_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_conference_user


@app.post(
        "/token", 
        summary="endpoint для получения токена по логину/паролю",
        tags=["Авторизация по протоколу OAuth2 с паролем, хешированием и JWT-токенами"])
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    conference_user = authenticate_user(conference_users_db, form_data.username, form_data.password)
    if not conference_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": conference_user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@app.get(
        "/conference_users/me/", 
        response_model=ConferenceUser,
        summary="endpoint для получения информации о пользователе",
        tags=["Авторизация по протоколу OAuth2 с паролем, хешированием и JWT-токенами"])
async def read_users_me(
    current_conference_user: Annotated[ConferenceUser, Depends(get_current_active_conference_user)],
):
    return current_conference_user


@app.get(
        "/conference_users/me/items/",
        summary="endpoint для проверки активности пользователя",
        tags=["Авторизация по протоколу OAuth2 с паролем, хешированием и JWT-токенами"])
async def read_own_items(
    current_conference_user: Annotated[ConferenceUser, Depends(get_current_active_conference_user)],
):
    return [{"item_id": "yeah", "owner": current_conference_user.username}]