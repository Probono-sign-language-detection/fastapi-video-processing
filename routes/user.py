from datetime import datetime, timedelta
from typing import Optional

import bcrypt

from fastapi import Depends, HTTPException, APIRouter, status
from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials,
    OAuth2PasswordRequestForm,
)

from jose import jwt
from jose.exceptions import ExpiredSignatureError

from beanie import init_beanie
from beanie.odm.documents import Document
from beanie.odm.fields import PydanticObjectId

from models.user import User, UserIn
import os

user_router = APIRouter()

ALGORITHM = "HS256"
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ACCESS_TOKEN_EXPIRE_MINUTES = 30

async def get_current_user(
        authorization: HTTPAuthorizationCredentials = Depends(
            HTTPBearer(auto_error=False)
        )
) -> User:
    token = authorization.credentials # access_token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user = await User.find_one(User.username == payload.get("sub"))
        # print(user)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
        return user
    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")


@user_router.post("/register/")
async def register(user_in: UserIn) -> dict[str, str]:
    user = await User.find_one(User.username == user_in.username)
    if user:
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed_password = bcrypt.hashpw(user_in.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    user = User(username=user_in.username,
                hashed_password=hashed_password,
                password=user_in.password)
    await user.insert()
    return {"msg": "User created successfully."}


@user_router.post("/login/")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await User.find_one(User.username == form_data.username)
    if not user or not bcrypt.checkpw(form_data.password.encode('utf-8'), user.hashed_password.encode('utf-8')):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token_data = {"sub": user.username, "exp": expire}
    token = jwt.encode(token_data, SECRET_KEY, algorithm="HS256")

    return {"access_token": token}


@user_router.post("/logout/")
async def logout(current_user: User = Depends(get_current_user)):
    '''
    로그아웃 로직. JWT 토큰 기반 시스템에서는 클라이언트의 토큰을 만료시키거나 삭제하는 방식으로 처리.
    '''
    return {"msg": "Logout successful."}


@user_router.get("/users/me", response_model=User)
async def get_current_user(user: dict = Depends(get_current_user)):
    return user
