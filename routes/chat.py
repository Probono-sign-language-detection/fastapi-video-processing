
from fastapi import APIRouter, Depends, HTTPException, status

from models.video import VideoData, VideoDataModel, VideoDataUpdate, UserChatModel, Database

from config.redis import redisdb
from beanie import PydanticObjectId
from typing import List
import logging


chat_router = APIRouter()
# MongoDB 설정
chat_database = Database(UserChatModel)
logger = logging.getLogger(__name__)


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
