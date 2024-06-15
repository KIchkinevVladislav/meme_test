from pydantic import BaseModel


class MemeBase(BaseModel):
    content: str
    image_url: str


class LoadingMeme(BaseModel):
    content: str


class ShowMeme(MemeBase):
    int: int

    class Config:
        from_attributes = True


class StatusResponse(BaseModel):
    status: str
    message: str
        