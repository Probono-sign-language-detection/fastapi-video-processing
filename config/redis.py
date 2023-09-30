import logging

import redis.asyncio as aioredis
from dotenv import load_dotenv
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv('.env')

class RedisDB:
    _REDIS_HOST = os.getenv("REDIS_HOST", "redis")
    _REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    _REDIS_DB = int(os.getenv("REDIS_DB", 0))

    def __init__(self):
        self.client = None

    async def connect(self):
        try:
            self.client = aioredis.Redis(
                host=self._REDIS_HOST,
                port=self._REDIS_PORT,
                db=self._REDIS_DB,
                encoding="utf-8",
                decode_responses=True
            )
            # Redis 서버에 PING 명령을 보내 응답을 확인합니다.
            await self.client.ping()
            logger.info("Redis 데이터베이스에 성공적으로 연결되었습니다.")
        except Exception as e:
            logger.error(f"Redis 데이터베이스 연결에 실패: {e}")

    async def close(self):
        if self.client:
            await self.client.close()
            logger.info("Redis 커넥션 종료.")

    async def set(self, key: str, value: str):
        await self.client.set(key, value)

    async def get(self, key: str):
        return await self.client.get(key)

    async def expire(self, key: str, time: int):
        await self.client.expire(key, time)

    async def delete(self, key: str):
        await self.client.delete(key)

    def pubsub(self):
        return self.client.pubsub()

    async def publish(self, channel: str, message: str):
        await self.client.publish(channel, message)

# Redis 디비 싱글톤 패턴
redisdb = RedisDB()
