
from fastapi import APIRouter, Depends, HTTPException, status

from models.video import VideoData, VideoDataModel, VideoDataUpdate, Database

import redis.asyncio as aioredis
from beanie import PydanticObjectId
from typing import List


chat_router = APIRouter()
# MongoDB 설정
video_database = Database(VideoDataModel)

# Redis 설정 (비동기)
redis_client = aioredis.Redis(host="redis", port=6379, db=0)

@chat_router.post("/chat/{user_id}/")
async def send_message(user_id: str, sentence: str):
    # Redis에 메시지 저장 (임시 캐싱)
    await redis_client.set(user_id, sentence)
    
    # MongoDB에 메시지 저장
    chat_data = {
        "user_id": user_id,
        "sentence": sentence
    }
    video_database.save(chat_data)
    
    return {"message": "Message sent successfully"}

@chat_router.get("/chat/{user_id}/")
async def get_message(user_id: str):
    # Redis에서 메시지 확인
    sentence = await redis_client.get(user_id)
    if sentence:
        return {"user_id": user_id, "sentence": sentence.decode()}
    
    # MongoDB에서 메시지 가져오기
    chat_data = video_database.get({"user_id": user_id})
    if not chat_data:
        raise HTTPException(status_code=404, detail="Message not found")
    
    return chat_data
