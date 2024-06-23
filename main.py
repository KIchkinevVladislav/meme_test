import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import yaml

from app.private_api.private_router import _private_router
from app.public_api.public_router import _public_router
from app.public_api.user_router import _user_router

origins = ["*"]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

with open("docs.yaml", "r", encoding="utf8") as file:
    custom_openapi_schema = yaml.safe_load(file)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    app.openapi_schema = custom_openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

app.include_router(_public_router, prefix="/memes", tags=["public_api"])
app.include_router(_private_router, prefix="/memes", tags=["private_api"])
app.include_router(_user_router, prefix="/user", tags=["user"])

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
    