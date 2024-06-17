from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_db
from database.schemas import  UserCreate, ShowUser
from .public_crud import create_new_user

_user_router = APIRouter()

@_user_router.post('/sign-up', response_model=ShowUser)
async def create_user(body: UserCreate, db: AsyncSession = Depends(get_db)) -> ShowUser:
    try:
        return await create_new_user(body, db)
    except Exception as err:
        raise HTTPException(status_code=503, detail=f"Database error: {err}")
