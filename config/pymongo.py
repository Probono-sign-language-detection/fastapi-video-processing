from pymongo import MongoClient
from urllib.parse import quote_plus
from dotenv import load_dotenv
import os

# 루트 폴더의 환경 변수 파일 읽어오기
load_dotenv('.env')

# Retrieve environment variables or use default values
DATABASE_URI = os.getenv("DATABASE_URI")
DATABASE_USERNAME = os.getenv("DATABASE_USERNAME")  
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")  
DATABASE_NAME = os.getenv("DATABASE_NAME", "test")

username = quote_plus(DATABASE_USERNAME)
password = quote_plus(DATABASE_PASSWORD)

uri = f"mongodb://{username}:{password}@{DATABASE_URI}/?authSource=admin"

# Create the MongoDB connection
connection = MongoClient(uri)