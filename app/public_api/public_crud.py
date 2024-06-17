from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
from typing import List

from database.models import Meme
from database.schemas import UserCreate, ShowUser
from utils import Hasher, UserDAL

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


async def create_new_user(body: UserCreate, db: AsyncSession) -> ShowUser:
    async with db.begin():
        user_dal = UserDAL(db)
        user = await user_dal.create_user(
            name=body.name,
            surname=body.surname,
            email=body.email,
            hashed_password=Hasher.get_password_hash(body.password),

        )
        return ShowUser(
            user_id=user.id,
            name=user.name,
            surname=user.surname,
            email=user.email,
        )
