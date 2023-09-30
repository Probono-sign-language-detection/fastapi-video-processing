from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from models.video import VideoData, VideoDataModel, VideoDataUpdate, Database
from typing import List

video_database = Database(VideoDataModel)
crud_router = APIRouter()

@crud_router.post("/save_video", response_model=dict, status_code=201)
async def save_s3_uri_db(video_body: VideoData):
    video_data = VideoDataModel(**video_body.dict())
    await video_database.save(video_data)

    # ObjectId를 문자열로 변환
    data_dict = video_data.dict()
    data_dict["id"] = str(data_dict["id"])

    return {
        "status": "success", 
        "message": "video data를 db에 저장",
        "data": data_dict
    }

@crud_router.get("/get_video/{id}", response_model=VideoDataModel, status_code=200)
async def get_video_data_by_obj_id(id: PydanticObjectId) -> VideoDataModel:
    video_data = await video_database.get_by_obj_id(id)
    
    if video_data:
        return video_data
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, 
        detail="video data를 찾을 수 없습니다"
        )

@crud_router.get("/get_video/", response_model=List[VideoDataModel], status_code=200)
async def get_all_video_data() -> List[VideoDataModel]:
    video_datas = await video_database.get_all()
    
    if video_datas:
        return video_datas
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, 
        detail="video data를 가져오는 데 에러가 발생하였습니다."
        )

@crud_router.put("/update_video/{id}", response_model=VideoDataModel, status_code=200)
async def update_video_data(id: PydanticObjectId, body: VideoDataUpdate) -> VideoDataModel:
    '''
    issue : response id에서 revision_id가 나오는 문제
    '''
    updated_video_data = await video_database.update(id, body)
    
    if not updated_video_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="video data를 찾을 수 없습니다"
            )
    
    return updated_video_data

@crud_router.delete("/delete_video/{id}", response_model=dict, status_code=200)
async def delete_video_data(id: PydanticObjectId) -> dict:
    deleted_video_data = await video_database.delete(id)
    
    if not deleted_video_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="video data를 찾을 수 없습니다"
            )
    
    return {
        "status": "success", 
        "message": "video data를 삭제하였습니다."
    }