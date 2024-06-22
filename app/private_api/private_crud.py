from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from typing import Optional
from fastapi import HTTPException, UploadFile

from database.models import Meme, User
from minio_server import update_image_in_minio, upload_image_to_minio, delete_image_from_minio

async def update_meme_data(db: AsyncSession, meme_id: Optional[int], description: Optional[str] = None, file: UploadFile = None):
    async with db.begin():
        meme = await db.get(Meme, meme_id)
        
        if description:
            meme.description = description

        if file:
            new_image_url = await update_image_in_minio(file, meme.image_url)
            meme.image_url = new_image_url

        await db.flush()


async def save_meme(db: AsyncSession,  meme_id: Optional[int] = None, description: Optional[str] = None, file: UploadFile = None, author: User = None):
    try:
        if meme_id:
            await update_meme_data(db, meme_id, description, file)
        else:
            async with db.begin():
                image_url = await upload_image_to_minio(file)
                meme = Meme(description=description, image_url=image_url, author=author)
                db.add(meme)
                await db.flush()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save meme: {e}")


async def delete_meme_in_db(db: AsyncSession,  meme_id: Optional[int], image_url: Optional[str]):
    
    async with db.begin():

        exists_statement = delete(Meme).where(
            (Meme.id == meme_id)
        )
        await db.execute(exists_statement)
        await db.commit()

    await delete_image_from_minio(image_url)   

async def get_meme_from_db(db: AsyncSession, meme_id: int):
    async with db.begin():
        post = await db.execute(
            select(Meme).where(Meme.id == meme_id)
        )
        return post.scalars().first()