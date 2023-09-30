from datetime import datetime, timedelta
from typing import Optional

import bcrypt

from fastapi import Depends, HTTPException, APIRouter, status
from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials,
    OAuth2PasswordRequestForm,
)
from config.redis import redisdb
from utils.credential import get_access_token

from jose import jwt
from jose.exceptions import ExpiredSignatureError

from beanie import init_beanie
from beanie.odm.documents import Document
from beanie.odm.fields import PydanticObjectId

from models.user import User, UserIn, CreateOTPRequest, VerifyOTPRequest
import os
import random

user_router = APIRouter()

ALGORITHM = "HS256"
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ACCESS_TOKEN_EXPIRE_MINUTES = 30



def create_otp() -> int:
    return random.randint(1000, 9999)


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


# post otp
@user_router.post("/email/otp")
async def create_otp_handler(
    request: CreateOTPRequest,
    access_token: str = Depends(get_access_token)
):
    otp: int = create_otp()

    await redisdb.set(request.email, otp)
    await redisdb.expire(request.email, 30 * 60)

    # send otp to email
    return {"otp": otp}

@user_router.post("/email/otp/verify")
async def verify_otp_handler(
    request: VerifyOTPRequest,
    # background_tasks: BackgroundTasks,
    access_token: str = Depends(get_access_token),
) -> dict[str, str]:
    otp: str | None = await redisdb.get(request.email)
    print('otp', otp)

    if not otp:
        raise HTTPException(status_code=400, detail="Bad Request")

    if request.otp != int(otp):
        raise HTTPException(status_code=400, detail="Bad Request")

    token_username: str = jwt.decode(access_token, SECRET_KEY, algorithms=["HS256"]).get("sub")

    user: User | None = await User.find_one(User.username == token_username)
    if not user:
        raise HTTPException(status_code=404, detail="User Not Found")

    print(user.dict())
    # save email to user

    # send email to user
    # background_tasks.add_task(
    #     user_service.send_email_to_user,
    #     email="admin@fastapi.com"
    # )

    return user.dict()


# eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJoYWp1bnkiLCJleHAiOjE2OTYwNjMwMTJ9.kjGMABZsfTdrgEKgm36OkXbUgjYf1wz4XLIPz3wC3Ts