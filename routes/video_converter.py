from starlette.websockets import WebSocket, WebSocketDisconnect

from config.websocket import websocket_manager

try:
    # fastapi
    from fastapi import APIRouter, Request, Depends, HTTPException, Query, Body, File, UploadFile
    from fastapi.responses import JSONResponse
    from typing import Dict, Union, Optional
    from utils.credential import get_access_token

    # requests 관련
    import requests
    from requests.exceptions import RequestException
    
    import os

    from models.video import VideoData, VideoDataModel, VideoDataUpdate, Database
    from config.redis import redisdb

    from typing import List

    # 3rd party library 관련
    import boto3
    from dotenv import load_dotenv

    from jose import jwt
    from jose.exceptions import ExpiredSignatureError
    
    import logging
    import subprocess

    print("All Modules are loaded")

except Exception as e:
    print("Error : {} ".format(e))

load_dotenv()

AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
SECRET_KEY = os.getenv("JWT_SECRET_KEY")

converter_router = APIRouter()
video_database = Database(VideoDataModel)

def _upload_to_s3(file_path: str, bucket_name: str, object_name: str = None) -> str:
    
    # If no object name is provided, default to the file's name
    if object_name is None:
        object_name = os.path.basename(file_path) # file's name 
    
    # Create an S3 client
    s3_client = boto3.client('s3',
                             aws_access_key_id=AWS_ACCESS_KEY,
                             aws_secret_access_key=AWS_SECRET_KEY)
    
    try:    
        s3_save_path = os.path.join('video', object_name)
        # Upload the file
        s3_client.upload_file(file_path, bucket_name, s3_save_path)
        
        # Return the URL where the uploaded object can be accessed
        return f"https://{bucket_name}.s3.amazonaws.com/{s3_save_path}"
    
    except Exception as e:
        print(f"An error occurred: {e}")
        raise e


def _convert_mov_to_mp4(input_file: str, output_file: str):
    command = ['ffmpeg', '-i', input_file, output_file]
    subprocess.run(command)


@converter_router.post("/save_upload_s3/", 
                       response_class=JSONResponse,
                       status_code=201)
async def store_file(
    access_token: str = Depends(get_access_token),
    username: Optional[str] = Body(None),
    file: UploadFile = File(...)
    ) -> Dict[str, Union[str, bool]]:
    '''
    upload video save into aws s3 using boto3
    '''
    from tempfile import NamedTemporaryFile
    import time

    print(access_token)
    print(username if username else "username is None")

    username_decoded = jwt.decode(access_token, SECRET_KEY, algorithms=["HS256"])
    print(username_decoded.get("sub"))

    inferred_username = username if username else username_decoded.get("sub")

    start_time = time.time()
    logging.info('video save start')
    print('video save start')
    # mp4, mov
    # Use NamedTemporaryFile inside the static directory
    with NamedTemporaryFile(
        mode='w+b', suffix='.mov', dir='static', delete=False) as temp_file:
        mov_file_path = temp_file.name
        print(mov_file_path)
        logging.info(mov_file_path)
        
        try:
            with open(mov_file_path, "wb") as outfile:
                for chunk in file.file:
                    outfile.write(chunk)
                
            print(f"video saved at static folder : {mov_file_path}")
            logging.info(f"video saved at static folder : {mov_file_path}")
            
            # Convert .mov to .mp4
            # mp4_file_path = file_path.replace('.mov', '.mp4')
            # _convert_mov_to_mp4(file_path, mp4_file_path)
            try:
                s3_uri = _upload_to_s3(mov_file_path, 'bitamin-video-storage')
                # inference

                # inferred_data = requests.post("http://localhost:8000/inference/")
                inferred_data = "inference data hello"

                end_time = time.time()
                loading_time = end_time - start_time
                
                print(f"video store took {loading_time} seconds")

                save_data = {
                    "user_id": inferred_username,
                    "s3_uri": s3_uri,
                    "sentence": inferred_data
                }
                # save data to db
                print(save_data)
                video_data = VideoDataModel(**save_data)
                print(video_data)
                await video_database.save(video_data)

                print('saved to db')
                print(inferred_username)
                await redisdb.set(inferred_username, inferred_data)
                print(f'saved to redis : key :{inferred_username}')
                
                try:
                    # redis_pubsub = redisdb.pubsub()
                    await redisdb.publish(channel=inferred_username, message=inferred_data)
                    print('published to redis')
                except:
                    pass
                
                # ObjectId를 문자열로 변환
                data_dict = video_data.dict()
                data_dict["id"] = str(data_dict["id"])

                response_content = {
                    "status": "success",
                    "message": f"video saved at {s3_uri} and sentence saved at db",
                    "s3_uri": s3_uri,
                    "loading_time": loading_time,
                    "data": data_dict
                }
                
                return JSONResponse(content=response_content, status_code=201)
            
            except Exception as e: 
                raise HTTPException(status_code=500, detail=f"Error during saving to s3: {e}")

        except Exception as e:
            # If there's an error, clean up the temporary files if they were created
            if os.path.exists(mov_file_path):
                os.remove(mov_file_path)
            if os.path.exists(mov_file_path):
                os.remove(mov_file_path)
            raise HTTPException(status_code=500, detail=f"Error during saving to s3: {e}")

