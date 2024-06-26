from fastapi import (APIRouter, Depends, File, HTTPException, Response,
                     UploadFile)
from minio.error import S3Error
from sqlalchemy.ext.asyncio import AsyncSession

from app.public_api.public_crud import get_current_user_from_token
from database.db import get_db
from database.models import User
from database.schemas import LoadingMeme, ShowMemesPrivate, StatusResponse
from minio_server import minio_client
from utils import validate_image

from .private_crud import delete_meme_in_db, get_meme_from_db, save_meme

_private_router = APIRouter()


@_private_router.post('/', response_model=StatusResponse)
async def upload_meme(file: UploadFile, description: str=None, 
                       db: AsyncSession=Depends(get_db),  author: User=Depends(get_current_user_from_token)):
    try:
        file = validate_image(file)
        await save_meme(db, description=description, file=file, author=author)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload image: {e}")
   
    return StatusResponse(status="ok", message="Meme uploaded successfully")


@_private_router.get('/{meme_id}', response_model=ShowMemesPrivate)
async def get_meme(meme_id: int, db: AsyncSession = Depends(get_db), author: User = Depends(get_current_user_from_token)):
    meme = await get_meme_from_db(db, meme_id)
    if not meme:
        raise HTTPException(status_code=404, detail=f"Meme number {meme_id} does not exist.")

    if meme.user_id != author.id:
        raise HTTPException(status_code=404, detail=f"Only the author can access this meme.")

    try:
        meme_data = ShowMemesPrivate(id=meme.id, description=meme.description, image_url=meme.image_url, created_at=meme.created_at)

        return meme_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving meme data: {e}")


@_private_router.get('/image/{meme_id}')
async def get_meme_image(meme_id: int, db: AsyncSession = Depends(get_db), author: User = Depends(get_current_user_from_token)):
    meme = await get_meme_from_db(db, meme_id)
    if not meme:
        raise HTTPException(status_code=404, detail=f"Meme number {meme_id} does not exist.")
    
    if meme.user_id != author.id:
        raise HTTPException(status_code=404, detail=f"Only the author can access this meme.")
    
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
    file: UploadFile=File(None),
    description: str=None,
    db: AsyncSession=Depends(get_db), author: User=Depends(get_current_user_from_token)
):
    meme = await get_meme_from_db(db, meme_id)
    if not meme:
        raise HTTPException(status_code=404, detail=f"Meme number {meme_id} does not exist.")

    if meme.user_id != author.id:
        raise HTTPException(status_code=404, detail=f"Only the author can update this meme.")  

    try:
        file = validate_image(file)
        await save_meme(db, meme_id, description, file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload image: {e}")
    return StatusResponse(status="ok", message="Meme updated successfully")


@_private_router.delete('/{meme_id}', response_model=StatusResponse)
async def delete_meme(meme_id: int, db: AsyncSession = Depends(get_db), author: User = Depends(get_current_user_from_token)):
    meme = await get_meme_from_db(db, meme_id)
    if not meme:
        raise HTTPException(status_code=404, detail=f"Meme number {meme_id} does not exist.")

    if meme.user_id != author.id:
        raise HTTPException(status_code=404, detail=f"Only the author can delete this meme.") 

    try:
        await delete_meme_in_db(db, meme_id, meme.image_url)

        return StatusResponse(status="ok", message=f"Meme number {meme_id} deleted successfully")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete meme: {e}")
