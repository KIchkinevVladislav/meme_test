from typing import Optional

from pydantic import BaseModel
from fastapi import UploadFile, File


class BaseMeme(BaseModel):
    content: str


class LoadingMeme(BaseMeme):
    pass


class ShowMemes(BaseMeme):
    id: int
    image_url: str


class UpdateMeme(BaseModel):
    content: Optional[str]
    file: Optional[UploadFile] = None
    

class StatusResponse(BaseModel):
    status: str
    message: str
        