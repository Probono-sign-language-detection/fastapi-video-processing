
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket
from starlette.websockets import WebSocketDisconnect

from models.video import VideoData, VideoDataModel, VideoDataUpdate, UserChatModel, Database

from config.redis import redisdb
from config.websocket import websocket_manager
from beanie import PydanticObjectId
from typing import List
import logging
import time
import asyncio

chat_router = APIRouter()
# MongoDB 설정
chat_database = Database(UserChatModel)
logger = logging.getLogger(__name__)


@chat_router.websocket("/ws/chat/{user_id}")
async def websocket_endpoint(
        websocket: WebSocket,
        user_id: str):
    await websocket_manager.connect(websocket)
    try:
        while True:
            # data = await websocket.receive_text()
            user_data = await redisdb.get(user_id)
            time.sleep(3)
            if user_data:
                # await websocket.send_text(f"Data from Redis for {user_id}: {user_data}")
                await websocket_manager.send_personal_message(f"You wrote: {user_data}", websocket)
                await websocket_manager.broadcast(f"Client #{user_id} says: {user_data}")
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
        await websocket_manager.broadcast(f"Client #{user_id} left the chat")


@chat_router.websocket("/ws/chat/realtime/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await websocket_manager.connect(websocket)
    try:
        pubsub = redisdb.pubsub()
        await pubsub.subscribe(user_id)

        while True:
            res = await pubsub.get_message(timeout=20)
            if res is not None:
                if res['type'] == 'message':
                    print(f"res: {res}")
                    await websocket_manager.send_personal_message(f"You wrote: {res['data']}", websocket)
            await asyncio.sleep(3)

    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
        await websocket_manager.broadcast(f"Client left the chat room: {user_id}")


@chat_router.post("/chat/{user_id}/")
async def send_message(user_id: str, sentence: str):
    # Redis에 메시지 저장 (임시 캐싱)
    await redisdb.set(user_id, sentence)

    # MongoDB에 메시지 저장
    chat_data = {
        "user_id": user_id,
        "sentence": sentence
    }
    chat_data_instance = UserChatModel(**chat_data)

    await chat_database.save(document=chat_data_instance)

    # Publish the message to the Redis channel
    await redisdb.publish(f"chat_{user_id}", sentence)

    return {"message": "Message sent successfully"}


@chat_router.get("/chat/{user_id}/")
async def get_message(user_id: str):
    # Redis에서 메시지 확인
    sentence = await redisdb.get(user_id)
    if sentence:
        logger.info("get message from redis")
        redisdb.delete(user_id)
        logger.info(f"delete {user_id} message from redis")
        return {"user_id": user_id, "sentence": sentence}
    
    # MongoDB에서 메시지 가져오기
    chat_data = await chat_database.get({"user_id": user_id})
    if not chat_data:
        raise HTTPException(status_code=404, detail="Message not found")
    
    return chat_data.dict()
