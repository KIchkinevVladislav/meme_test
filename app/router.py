from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from .db import get_db
from .schemas import LoadingMeme, StatusResponse
from .crud import add_meme_to_db
from config import upload_image_to_minio

meme_router = APIRouter()


@meme_router.post('/', response_model=StatusResponse)
async def loading_meme(content: str = Depends(LoadingMeme), file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    try:
        image_url = await upload_image_to_minio(file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload image: {e}")
    
    await add_meme_to_db(db, content.content, image_url)
    return StatusResponse(status="ok", message="Meme uploaded successfully")