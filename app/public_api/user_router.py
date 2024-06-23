from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_db
from database.schemas import  UserCreate, ShowUser, Token
from .public_crud import create_new_user, authenticate_user, create_access_token, get_user_by_email_for_auth, ACCESS_TOKEN_EXPIRE_MINUTES

_user_router = APIRouter()

@_user_router.post('/sign-up', response_model=ShowUser)
async def create_user(body: UserCreate, db: AsyncSession = Depends(get_db)) -> ShowUser:
    user = await get_user_by_email_for_auth(body.email, db)
    if user:
        raise HTTPException(status_code=404, detail=f"User with this email name already exists.")
    try:
        return await create_new_user(body, db)
    except Exception as err:
        raise HTTPException(status_code=503, detail=f"Database error: {err}")


@_user_router.post('/token', response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    user = await authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect username or password'
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={'sub': user.email, 'other_custom_data': [1, 2, 3, 4]},
        expires_delta=access_token_expires,
    )
    return {'access_token': access_token, 'token_type': 'bearer'}
