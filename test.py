from typing import AsyncGenerator
import asyncio
import unittest

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from database.db import get_db
from database.models import Base
from main import app

DATABASE_URL_TEST = "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres_test"

engine_test = create_async_engine(DATABASE_URL_TEST, poolclass=NullPool)

async_session_maker = sessionmaker(engine_test, class_=AsyncSession, expire_on_commit=False)

async def override_get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session

app.dependency_overrides[get_db] = override_get_async_session

async def init_db():
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def drop_db():
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        


class TestBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        asyncio.run(drop_db())
        asyncio.run(init_db())
    
    def setUp(self):
        self.client = TestClient(app)
        
    def test_good_user(self):
        response = self.client.post(
            "/user/sign-up",
            json={
                "name": "test",
                "surname": "test",
                "email": "test@example.com",
                "password": "testpassword",
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get('email'), 'test@example.com')

    def test_repeat_user_email(self):
        response = self.client.post(
            "/user/sign-up",
            json={
                "name": "test",
                "surname": "test",
                "email": "test@example.com",
                "password": "testpassword",
            },
        )

        self.assertEqual(response.status_code, 503)

    def test_login_for_access_token(self):
        response = self.client.post(
            "/user/token",
            data={
                "username": "test@example.com",
                "password": "testpassword"
            },
        )
        self.assertEqual(response.status_code, 200)
    
    def test_login_for_access_token_fail(self):
        response = self.client.post(
            "/user/token",
            data={
                "username": "test@example.com",
                "password": "password"
            },
        )
        self.assertEqual(response.status_code, 401)
