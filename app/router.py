from fastapi import APIRouter, Query, Depends, HTTPException, File, UploadFile, Response
from sqlalchemy.ext.asyncio import AsyncSession
from minio.error import S3Error

from .db import get_db
from .schemas import LoadingMeme, StatusResponse, ShowMemes
from .crud import  get_list_memes, save_meme
from minio_server import minio_client

from app.models import Meme
from validate import validate_image


meme_router = APIRouter()


@meme_router.post('/', response_model=StatusResponse)
async def upload_meme(content: str = Depends(LoadingMeme), file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    try:
        file = validate_image(file)
        await save_meme(db, content=content.content, file=file)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload image: {e}")
    
    return StatusResponse(status="ok", message="Meme uploaded successfully")



@meme_router.get('/', response_model=list[ShowMemes])
async def get_memes(
    db: AsyncSession = Depends(get_db),     
    page: int = Query(0, ge=0, description="Номер страницы."),
    size: int = Query(10, le=100, description="Количество записей на странице"),
    sort_by: str = Query('id', description='Сортировка по значению'),
    sort_desc: bool = Query(False, description='Сортировка в обратном порядке')) -> list[ShowMemes]:

    memes = await get_list_memes(db=db, page=page, size=size, sort_by=sort_by, sort_desc=sort_desc)
    
    if not memes:
        raise HTTPException(status_code=404, detail="No memes found")
    
    return [ShowMemes(id=meme.id, content=meme.content, image_url=meme.image_url) for meme in memes]


@meme_router.get('/{meme_id}', response_model=ShowMemes)
async def get_meme(meme_id: int, db: AsyncSession = Depends(get_db)):
    try:
        meme = await db.get_one(Meme, meme_id)
        if not meme:
            raise HTTPException(status_code=404, detail="Meme not found")

        meme_data = ShowMemes(id=meme.id, content=meme.content, image_url=meme.image_url)

        return meme_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving meme data: {e}")


@meme_router.get('/image/{meme_id}')
async def get_meme_image(meme_id: int, db: AsyncSession = Depends(get_db)):
    try:
        meme = await db.get(Meme, meme_id)
        if not meme:
            raise HTTPException(status_code=404, detail="Meme not found")

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


@meme_router.patch('/{meme_id}', response_model=StatusResponse)
async def update_meme(
    meme_id: int,
    content = None,
    file: UploadFile = File(None),
    db: AsyncSession = Depends(get_db)
):
    try:
        await save_meme(db, meme_id, content, file)
          
        return StatusResponse(status="ok", message="Meme updated successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update meme: {e}")
# TODO: return information about meme?
