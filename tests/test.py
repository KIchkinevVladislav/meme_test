import os
from io import BytesIO
from starlette.datastructures import Headers
from typing import AsyncGenerator
import asyncio
import unittest
import aiofiles

from fastapi import UploadFile
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from database.db import Base, get_db
from database.models import Meme, User
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
        asyncio.run(init_db())
        
    @classmethod
    def tearDownClass(cls):
        asyncio.run(drop_db())
        
    def setUp(self):
        self.client = TestClient(app)


class TestUserRouter(TestBase):
        
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


class TestMemePublicRouterNotMemes(TestBase):

    def test_not_memes(self):
        response = self.client.get(
            "/memes/",
        )
        self.assertEqual(response.status_code, 404)


class TestMemePublicRouter(TestBase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        asyncio.run(create_test_data_meme())


    def test_get_memes(self):
        response = self.client.get("/memes/",)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.json()) == 3)

    def test_get_memes_with_pagination(self):
        response = self.client.get("/memes/?page=0&size=2")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.json()) == 2)    

    def test_get_memes_with_sorting(self):
        response = self.client.get("/memes/?sort_by=id&sort_desc=true")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.json()) == 3)   

    def test_get_memes_with_invalid_parameters(self):

        response = self.client.get("/memes/?page=-1&size=0")

        self.assertEqual(response.status_code, 422)
        self.assertIn("detail", response.json())   


    def test_get_memes_empty_result(self):

        response = self.client.get("/memes/?page=10&size=10")

        self.assertEqual(response.status_code, 404)
        self.assertIn("detail", response.json())
        self.assertEqual(response.json()["detail"], "No memes found")
    

class TestMemePrivateRouter(TestBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        client = TestClient(app)

        response = client.post(
            "/user/sign-up",
            json={
                "name": "test",
                "surname": "test",
                "email": "test@example.com",
                "password": "testpassword",
            },
        )
        response.status_code == 200

        response = client.post(
            "/user/token",
            data={
                "username": "test@example.com",
                "password": "testpassword"
            },
        )
        response.status_code == 200


    def setUp(self):
        super().setUp()

        response = self.client.post(
            "/user/token",
            data={
                "username": "test@example.com",
                "password": "testpassword"
            },
        )
        self.assertEqual(response.status_code, 200)

        self.token = response.json()["access_token"]


    def test_upload_meme_success(self):
        headers = Headers({"Authorization": f"Bearer {self.token}"})

        with open("tests/fixtures/test_image_2.jpeg", "rb") as f:
            file_content = f.read()

        files = {"file": ("test_image.jpg", BytesIO(file_content), "image/jpeg"),}
        data = {'content': 'Meme description'}

        response = self.client.post("/memes/", files=files, data=data, headers=headers)

        assert response.status_code == 200
        assert response.json() == {"status": "ok", "message": "Meme uploaded successfully"}

    def test_upload_meme_unauthorized(self):    
        headers = {} 
        with open("tests/fixtures/test_image_2.jpeg", "rb") as f:
            file_content = f.read()

        files = {"file": ("test_image.jpg", BytesIO(file_content), "image/jpeg"),}
        data = {'content': 'Meme description'}

        response = self.client.post("/memes/", files=files, data=data, headers=headers)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Not authenticated")


    def test_upload_meme_invalid_image(self):
            headers = Headers({"Authorization": f"Bearer {self.token}"})

            with open("tests/fixtures/test.txt", "rb") as f:
                file_content = f.read()

            files = {"file": ("test.txt", BytesIO(file_content), "text/plain"),}
            data = {'content': 'Meme description'}

            response = self.client.post("/memes/", files=files, data=data, headers=headers)

            self.assertEqual(response.status_code, 500)
            self.assertIn("Failed to upload image: 400: Uploaded file is not an image", response.json()["detail"])


    def test_update_meme_success(self):
        headers = Headers({"Authorization": f"Bearer {self.token}"})

        with open("tests/fixtures/test_image_3.jpeg", "rb") as f:
            file_content = f.read()

        files = {"file": ("test_image.jpg", BytesIO(file_content), "image/jpeg"),}
        data = {'content': 'New Meme description'}

        response = self.client.patch("/memes/", files=files, data=data, headers=headers)

        assert response.status_code == 200
        assert response.json() == {"status": "ok", "message": "Meme updated successfully"}





async def create_test_data_meme():
        async with async_session_maker() as db_session:
            user = User(name="test", surname='test', email='test@example.com', hashed_password="$2b$12$D/6ZRIonVLLgqU5HuVfMeOZG9N61HqeD8yKt/5aVS0YY.s.qts5KO")
            db_session.add(user)
            await db_session.flush()

            image_files = [
                'tests/fixtures/test_image_1.jpg',
                'tests/fixtures/test_image_2.jpeg',
                'tests/fixtures/test_image_3.png'
            ]

            for file_path in image_files:
                async with aiofiles.open(file_path, 'rb') as f:
                    file_content = await f.read()

                file = UploadFile(filename=os.path.basename(file_path), file=BytesIO(file_content))
                meme = Meme(description="Test Meme", image_url=file.filename, author=user)
                db_session.add(meme)

            await db_session.commit()