import uvicorn
from fastapi import FastAPI

from app.private_api.private_router import _private_router
from app.public_api.public_router import _public_router
from app.public_api.user_router import _user_router

app = FastAPI()

app.include_router(_public_router, prefix="/memes", tags=["public_api"])
app.include_router(_private_router, prefix="/memes", tags=["private_api"])
app.include_router(_user_router, prefix="/user", tags=["user"])

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)