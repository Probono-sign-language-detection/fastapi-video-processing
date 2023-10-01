from fastapi import FastAPI
from fastapi.responses import JSONResponse

from fastapi.middleware.cors import CORSMiddleware

from config.websocket import websocket_manager
from routes.video_converter import converter_router
from routes.beanie_crud import crud_router
from routes.user import user_router
from routes.chat import chat_router

from typing import Dict

from config.motor_connection import mongodb
from config.redis import redisdb

import asyncio
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv('.env')

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=JSONResponse, status_code=200)
async def read_root() -> Dict[str, str]:
    '''
    api health check를 위한 API
    '''
    return {"response": "Hello World"}

@app.on_event("startup")
async def on_app_start():
    logger.info("서버 시작, mongo db 연결 시도")
    await mongodb.connect()
    logger.info("서버 시작, redis db 연결 시도")
    await redisdb.connect()



@app.on_event("shutdown")
async def on_app_shutdown():
    try:
        await mongodb.close()
        logger.info("서버 종료, mongo db 연결 해제")
    except asyncio.exceptions.CancelledError:
        logger.error("DB 연결 해제 중 에러 발생")
        raise
    
    try:
        await redisdb.close()
        logger.info("서버 종료, redis db 연결 해제")
    except asyncio.exceptions.CancelledError:
        logger.error("Redis 연결 해제 중 에러 발생")
        raise

    try:
        await websocket_manager.close_all_connections()
        logger.info("서버 종료, websocket 연결 해제")
    except asyncio.exceptions.CancelledError:
        logger.error("WebSocket 연결 해제 중 에러 발생")
        raise

app.include_router(converter_router, prefix="/v1/video")

app.include_router(crud_router, prefix="/v1/crud")

app.include_router(user_router, prefix="/v1/user")

app.include_router(chat_router, prefix="/v1/user-chat")