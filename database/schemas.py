from datetime import datetime
from typing import Optional
import re
import uuid


from pydantic import BaseModel, EmailStr, field_validator
from fastapi import UploadFile, HTTPException


class BaseMeme(BaseModel):
    description: str


class LoadingMeme(BaseMeme):
    pass


class ShowMemesPublic(BaseMeme):
    id: int
    created_at: datetime

class ShowMemesPrivate(BaseMeme):
    id: int
    image_url: str
    created_at: datetime

class UpdateMeme(BaseModel):
    description: Optional[str]
    file: Optional[UploadFile] = None
    

class StatusResponse(BaseModel):
    status: str
    message: str


LETTER_MATCH_PATTERN = re.compile(r'^[а-яА-Яa-zA-Z\-]+$')


class UserCreate(BaseModel):
    name: str
    surname: str
    email: EmailStr
    password: str

    @field_validator('name')
    def validate_name(cls, value):
        if not LETTER_MATCH_PATTERN.match(value):
            raise HTTPException(
                status_code=422, detail='Name should contains only letters'
            )
        return value
        

    @field_validator('surname')
    def validate_surname(cls, value):
        if not LETTER_MATCH_PATTERN.match(value):
            raise HTTPException(
                status_code=422, detail='Surname should contains only letters'
            )
        return value
    

class TunedModel(BaseModel):
    class Config:
        """Tells pydantic to convert even non dict obj to json"""

        from_attributes = True


class ShowUser(TunedModel):
    user_id: uuid.UUID
    name: str
    surname: str
    email: EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str