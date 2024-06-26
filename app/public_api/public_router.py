from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_db
from database.schemas import ShowMemesPublic

from .public_crud import get_list_memes

_public_router = APIRouter()


@_public_router.get('/', response_model=list[ShowMemesPublic])
async def get_memes(
    db: AsyncSession = Depends(get_db),     
    page: int=Query(0, ge=0, description="Номер страницы."),
    size: int=Query(10, le=100, description="Количество записей на странице"),
    sort_by: str=Query('id', description='Сортировка по значению'),
    sort_desc: bool=Query(False, description='Сортировка в обратном порядке')) -> list[ShowMemesPublic]:

    memes = await get_list_memes(db=db, page=page, size=size, sort_by=sort_by, sort_desc=sort_desc)
   
    if not memes:
        raise HTTPException(status_code=404, detail="No memes found")
   
    return [ShowMemesPublic(id=meme.id, description=meme.description, created_at=meme.created_at) for meme in memes]
