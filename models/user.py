from pydantic import BaseModel, Field
from beanie.odm.documents import Document
from beanie.odm.fields import PydanticObjectId
from typing import Optional
from datetime import datetime, timedelta

class User(Document):
    username: str
    hashed_password: str

    class Settings:
        name = "user"
        use_revision = False

class UserIn(BaseModel):
    username: str
    password: str
    
class UserOut(BaseModel):
    id: str
    username: str