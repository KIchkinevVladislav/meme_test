from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Response
from sqlalchemy.ext.asyncio import AsyncSession
from minio.error import S3Error

from database.db import get_db
from database.schemas import LoadingMeme, StatusResponse, ShowMemes
from database.models import User
from .private_crud import  save_meme, delete_meme_in_db, get_meme_from_db
from app.public_api.public_crud import get_current_user_from_token
from minio_server import minio_client

from utils import validate_image


_private_router = APIRouter()


@_private_router.post('/', response_model=StatusResponse)
async def upload_meme(content: str = Depends(LoadingMeme), file: UploadFile = File(...), db: AsyncSession = Depends(get_db),  author: User = Depends(get_current_user_from_token)):
    try:
        file = validate_image(file)
        await save_meme(db, content=content.content, file=file, author=author)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload image: {e}")
    
    return StatusResponse(status="ok", message="Meme uploaded successfully")



@_private_router.get('/{meme_id}', response_model=ShowMemes)
async def get_meme(meme_id: int, db: AsyncSession = Depends(get_db)):
    meme = await get_meme_from_db(db, meme_id)
    if not meme:
        raise HTTPException(status_code=404, detail=f"Meme number {meme_id} does not exist.")
       
    try:
        meme_data = ShowMemes(id=meme.id, content=meme.content, image_url=meme.image_url)

        return meme_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving meme data: {e}")


@_private_router.get('/image/{meme_id}')
async def get_meme_image(meme_id: int, db: AsyncSession = Depends(get_db)):
    meme = await get_meme_from_db(db, meme_id)
    if not meme:
        raise HTTPException(status_code=404, detail=f"Meme number {meme_id} does not exist.")
    
    try:
        bucket_name = 'memes'
        file_name = meme.image_url.split('/')[-1]

        try:
            response = minio_client.get_object(bucket_name, file_name)
            content = response.read()
            response.close()
            response.release_conn()
            return Response(content=content, media_type="image/jpeg")
        except S3Error as err:
            raise HTTPException(status_code=500, detail=f"MinIO error: {err}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving meme image: {e}")


@_private_router.patch('/{meme_id}', response_model=StatusResponse)
async def update_meme(
    meme_id: int,
    content = None,
    file: UploadFile = File(None),
    db: AsyncSession = Depends(get_db)
):    
    meme = await get_meme_from_db(db, meme_id)
    if not meme:
        raise HTTPException(status_code=404, detail=f"Meme number {meme_id} does not exist.")
    
    try:
        await save_meme(db, meme_id, content, file)
          
        return StatusResponse(status="ok", message="Meme updated successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update meme: {e}")
# TODO: return information about meme?


@_private_router.delete('/{meme_id}', response_model=StatusResponse)
async def delete_meme(meme_id: int, db: AsyncSession = Depends(get_db)):
    meme = await get_meme_from_db(db, meme_id)
    if not meme:
        raise HTTPException(status_code=404, detail=f"Meme number {meme_id} does not exist.")

    try:
        await delete_meme_in_db(db, meme_id, meme.image_url)

        return StatusResponse(status="ok", message=f"Meme number {meme_id} deleted successfully")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete meme: {e}")
    
