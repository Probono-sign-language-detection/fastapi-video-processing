from motor.motor_asyncio import AsyncIOMotorClient

from typing import Optional, List, Any 
from beanie import init_beanie

from models.video import VideoDataModel

from urllib.parse import quote_plus
import logging
from dotenv import load_dotenv
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv('.env')

class MongoDB:
    _DATABASE_URI = os.getenv("DATABASE_URI")
    _DATABASE_USERNAME = os.getenv("DATABASE_USERNAME")
    _DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
    # default db -> test
    _DATABASE_NAME = os.getenv("DATABASE_NAME", "handsign_db")

    _username = quote_plus(_DATABASE_USERNAME)
    _password = quote_plus(_DATABASE_PASSWORD)

    _MONGO_URL = f"mongodb://{_username}:{_password}@{_DATABASE_URI}/?authSource=admin"

    def __init__(self):
        self.client = None
        self.engine = None

    async def connect(self):
        try:
            self.client = AsyncIOMotorClient(self._MONGO_URL)
            database = self.client[self._DATABASE_NAME]
            await init_beanie(
                database=database,
                document_models=[VideoDataModel, ],
                )
            logger.info("데이터베이스에 성공적으로 연결이 되었습니다.")
        except Exception as e:
            logger.error(f"데이터베이스 연결에 실패: {e}")

    async def close(self):
        if self.client:
            self.client.close()
            logger.info("DB 커넥션 종료.")

# 몽고 디비 싱글톤 패턴
mongodb = MongoDB()

