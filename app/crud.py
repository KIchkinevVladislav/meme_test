from sqlalchemy.ext.asyncio import AsyncSession

from .models import Meme
from .schemas import ShowMeme


async def add_meme_to_db(db: AsyncSession, content: str, image_url: str) -> ShowMeme:
    async with db.begin():
        db_meme = Meme(content=content, image_url=image_url)
        db.add(db_meme)
        await db.flush() 
