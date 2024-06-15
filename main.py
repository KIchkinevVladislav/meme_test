import uvicorn
from fastapi import FastAPI

from app.router import meme_router

app = FastAPI()


app.include_router(meme_router, prefix="/memes", tags=["meme"])


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)