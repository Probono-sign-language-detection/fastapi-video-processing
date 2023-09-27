from pydantic import BaseModel, HttpUrl, constr, validator
from beanie import Document, Indexed, init_beanie, PydanticObjectId

from typing import Optional, List, Any 
'''
모델 스키마 정의 (테이블 입력 양식)
'''

class VideoData(BaseModel):
    user_id: str
    s3_uri: str
    sentence: str

class VideoDataModel(Document, VideoData):

    # collection name을 여기서 지정가능
    class Settings:
        name = "video"
        use_revision = False

class VideoDataUpdate(BaseModel):
    user_id: Optional[str] = None
    s3_uri: Optional[str] = None
    sentence: Optional[str] = None


class Database:
    def __init__(self, model):
        self.model = model
    
    async def save(self, document) -> None:
        await document.create()
        return 
    
    async def get(self, id: PydanticObjectId) -> Any:
        doc = await self.model.get(id)
        if doc:
            return doc 
        return False
    
    async def get_all(self) -> List[Any]:
        docs = await self.model.find_all().to_list()
        if docs:
            return docs 
        return False

    async def update(self, id: PydanticObjectId, body: BaseModel) -> Any:
        doc_id = id 
        des_body = body.dict() 
        des_body = {k: v for k, v in des_body.items() if v is not None}
        
        des_body.pop("id", None)
        des_body.pop("_id", None)  

        update_query = {"$set": des_body}
        
        update_doc = await self.model.get(doc_id)
        if not update_doc:
            return False

        await update_doc.update(update_query)
        return update_doc
    
    async def delete(self, id:PydanticObjectId) -> bool:
        doc = await self.model.get(id)
        if not doc:
            return False
        await doc.delete()
        return True