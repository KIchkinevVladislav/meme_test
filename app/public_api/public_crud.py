from typing import List, Optional
from datetime import datetime, timedelta
from starlette import status

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

from database.db import get_db
from database.models import Meme
from database.schemas import UserCreate, ShowUser
from utils import Hasher, UserDAL
from config import (SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES,)

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


async def get_user_by_email_for_auth(
        email: str, db: AsyncSession
):
    async with db.begin():
        user_dal = UserDAL(db)
        return await user_dal.get_user_by_email(
            email=email,
        )
    

async def authenticate_user(
        email: str, password: str, db: AsyncSession
):
    user = await get_user_by_email_for_auth(email=email, db=db)
    if user is None:
        return
    if not Hasher.verify_password(password, user.hashed_password):
        return
    return user


# variables to configure JWT
SECRET_KEY = SECRET_KEY
ALGORITHM = ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = ACCESS_TOKEN_EXPIRE_MINUTES

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/user/token')

async def get_current_user_from_token(
        token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
    )
    try:
        payload = jwt.decode(
            token, 
            SECRET_KEY,
            algorithms = [ALGORITHM],
        )
        email: str = payload.get('sub')
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = await get_user_by_email_for_auth(email=email, db=db)
    if user is None:
        raise credentials_exception
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({'exp': expire})
    encoded_jwt = jwt.encode(
        to_encode, SECRET_KEY, algorithm=ALGORITHM
    )
    return encoded_jwt