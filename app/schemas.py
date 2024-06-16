from pydantic import BaseModel


class BaseMeme(BaseModel):
    content: str


class LoadingMeme(BaseMeme):
    pass


class ShowMemes(BaseMeme):
    id: int
    image_url: str


class StatusResponse(BaseModel):
    status: str
    message: str
        