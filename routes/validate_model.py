from pydantic import BaseModel
from typing import Optional

class ArticleURL(BaseModel):
    url: str
    title: Optional[str] = None