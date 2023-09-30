from json import JSONEncoder
import json
from typing import Any
from bson import ObjectId
from fastapi.responses import JSONResponse

'''
사용하지 않음 -> 향후 도입 하거나 삭제 예정
'''
class CustomJSONEncoder(JSONEncoder):
    """
    ObjectId를 JSON으로 인코딩할 때 사용하는 사용자 정의 JSON 인코더.

    ObjectId는 JSON으로 직접 인코딩할 수 없으므로 문자열로 변환해야 합니다. 
    이 클래스는 ObjectId 인스턴스를 감지하고 문자열로 변환하는 기능을 제공합니다.
    """
    def default(self, o):
        """
        특별한 형태의 객체를 처리하기 위한 메서드.
        
        ObjectId의 인스턴스를 감지하면 문자열로 변환합니다.
        """
        if isinstance(o, ObjectId):
            return str(o)
        return super().default(o)
    

class CustomJSONResponse(JSONResponse):
    media_type = "application/json"
    
    def render(self, content: Any) -> bytes:
        return json.dumps(
            content, ensure_ascii=False, allow_nan=False, cls=CustomJSONEncoder
        ).encode("utf-8")