try:
    # fastapi
    from fastapi import APIRouter, Request, Depends, HTTPException, Query, Body, File, UploadFile
    from fastapi.responses import JSONResponse
    from typing import Dict, Union, Optional

    # requests 관련
    import requests
    from requests.exceptions import RequestException
    import os

    # 3rd party library 관련
    import boto3
    from dotenv import load_dotenv

    print("All Modules are loaded")

except Exception as e:
    print("Error : {} ".format(e))

load_dotenv()

AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")

converter_router = APIRouter()


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

@converter_router.post("/save_upload_s3/", response_class=JSONResponse, status_code=201)
async def store_file(file: UploadFile = File(...)
    ) -> Dict[str, Union[str, bool]]:
    '''
    upload video save into aws s3 using boto3
    '''
    from tempfile import NamedTemporaryFile
    import time

    start_time = time.time()
        
    # Use NamedTemporaryFile inside the static directory
    with NamedTemporaryFile(
        mode='w+b', suffix='.mp4', dir='static', delete=False) as temp_file:
        file_path = temp_file.name
        print(file_path)
        try:
            with open(file_path, "wb") as outfile:
                for chunk in file.file:
                    outfile.write(chunk)
                
            print(f"PDF saved at static folder : {file_path}")
            try: 
                s3_uri = _upload_to_s3(file_path, 'bitamin-video-storage')
                
                # model inference with s3_uri

                end_time = time.time()
                loading_time = end_time - start_time
                
                print(f"video store took {loading_time} seconds")
                response_content = {
                    "status": "success", 
                    "message": f"video saved at {s3_uri}", 
                    "s3_uri": s3_uri, 
                    "loading_time": loading_time
                    }
                
                return JSONResponse(content=response_content, status_code=201)
            
            except Exception as e: 
                raise HTTPException(status_code=500, detail=f"Error during saving to s3: {e}")

        except Exception as e:
            # If there's an error, clean up the temporary file if it was created
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(status_code=500, detail=f"Error during saving: {e}")
            

