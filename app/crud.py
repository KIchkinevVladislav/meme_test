from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
from typing import List, Optional
from fastapi import HTTPException, UploadFile

from .models import Meme
from minio_server import update_image_in_minio, upload_image_to_minio


async def get_list_memes(
            db: AsyncSession, 
            page: int, 
            size: int, 
            sort_by: str = 'id',
            sort_desc: bool = False) -> List[Meme]:
    
    query = select(Meme).offset(page*size).limit(size)

    # sorting
    if sort_desc:
        query = query.order_by(desc(getattr(Meme, sort_by)))
    else:
        query = query.order_by(getattr(Meme, sort_by))

    result = await db.execute(query)
    memes = result.scalars().all()
    return memes


async def update_meme_data(db: AsyncSession, meme_id: Optional[int], content: Optional[str] = None, file: UploadFile = None):
    async with db.begin():
        meme = await db.get(Meme, meme_id)
        if not meme:
            raise HTTPException(status_code=404, detail="Meme not found")
        
        if content:
            meme.content = content

        if file:
            new_image_url = await update_image_in_minio(file, meme.image_url)
            meme.image_url = new_image_url

        await db.flush()


async def save_meme(db: AsyncSession,  meme_id: Optional[int] = None, content: Optional[str] = None, file: UploadFile = None):
    try:
        if meme_id:
            await update_meme_data(db, meme_id, content, file)
        else:
            async with db.begin():
                image_url = await upload_image_to_minio(file)
                meme = Meme(content=content, image_url=image_url)
                db.add(meme)
                await db.flush()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save meme: {e}")
    