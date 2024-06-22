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
from config import (DB_TEST_HOST, DB_TEST_PORT, DB_TEST_NAME, DB_TEST_USER, DB_TEST_PASS,)

# DATABASE_URL_TEST = f"postgresql+asyncpg://{DB_TEST_USER}:{DB_TEST_PASS}@{DB_TEST_HOST}:{DB_TEST_PORT}/{DB_TEST_NAME}"
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
    
        cls.client = TestClient(app)
        
    @classmethod
    def tearDownClass(cls):
        asyncio.run(drop_db())
        
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
    

class TestBaseForPrivateRouter(TestBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        response = cls.client.post(
            "/user/sign-up",
            json={
                "name": "test",
                "surname": "test",
                "email": "test@example.com",
                "password": "testpassword",
            },
        )

        response = cls.client.post(
            "/user/token",
            data={
                "username": "test@example.com",
                "password": "testpassword"
            },
        )

        cls.token = response.json()["access_token"]

        cls.headers = Headers({"Authorization": f"Bearer {cls.token}"})

        response = cls.client.post(
            "/user/sign-up",
            json={
                "name": "testtest",
                "surname": "testtest",
                "email": "testtest@example.com",
                "password": "testtestpassword",
                },
            )

        response = cls.client.post(
            "/user/token",
            data={
                "username": "testtest@example.com",
                "password": "testtestpassword"
            },
        )

        cls.token_2 = response.json()["access_token"]

        cls.headers_2 = Headers({"Authorization": f"Bearer {cls.token_2}"})


class TestMemePrivateRouterUpload(TestBaseForPrivateRouter):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_upload_meme_success(self):

        with open("tests/fixtures/test_image_2.jpeg", "rb") as f:
            file_content = f.read()

        files = {"file": ("test_image.jpg", BytesIO(file_content), "image/jpeg"),}
        params = {'description': 'Meme description'}

        response = self.client.post("/memes/", files=files, params=params, headers=self.headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "message": "Meme uploaded successfully"})

    def test_upload_meme_unauthorized(self):    
        self.headers = {} 
        with open("tests/fixtures/test_image_2.jpeg", "rb") as f:
            file_content = f.read()

        files = {"file": ("test_image.jpg", BytesIO(file_content), "image/jpeg"),}
        params = {'description': 'Meme description'}

        response = self.client.post("/memes/", files=files, params=params, headers=self.headers)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Not authenticated")

    def test_upload_meme_invalid_image(self):
        headers = Headers({"Authorization": f"Bearer {self.token}"})

        with open("tests/fixtures/test.txt", "rb") as f:
            file_content = f.read()

        files = {"file": ("test.txt", BytesIO(file_content), "text/plain"),}
        params = {'description': 'Meme description'}

        response = self.client.post("/memes/", files=files, params=params, headers=self.headers)

        self.assertEqual(response.status_code, 500)
        self.assertIn("Failed to upload image: 400: Uploaded file is not an image", response.json()["detail"])


class TestMemePrivateRouterUpdate(TestBaseForPrivateRouter):

    def setUp(self):
        super().setUp()

        with open("tests/fixtures/test_image_2.jpeg", "rb") as f:
            file_content = f.read()

        files = {"file": ("test_image.jpg", BytesIO(file_content), "image/jpeg"),}
        params = {'description': 'Meme description'}

        response = self.client.post("/memes/", files=files, params=params, headers=self.headers)

    def test_update_meme_success(self):

        with open("tests/fixtures/test_image_1.jpg", "rb") as f:
            file_content = f.read()

        files = {"file": ("test_image.jpg", BytesIO(file_content), "image/jpeg"),}
        params_update = {'description': 'Meme description new'}

        response = self.client.patch(f"/memes/{1}", files=files, params=params_update, headers=self.headers)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "message": "Meme updated successfully"})

    def test_update_meme_not_meme(self):

        with open("tests/fixtures/test_image_1.jpg", "rb") as f:
            file_content = f.read()

        files = {"file": ("test_image.jpg", BytesIO(file_content), "image/jpeg"),}
        params_update = {'description': 'Meme description new'}

        response = self.client.patch(f"/memes/{100}", files=files, params=params_update, headers=self.headers)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['detail'], 'Meme number 100 does not exist.')

    def test_update_meme_unauthorized(self):    
        self.headers = {} 
        with open("tests/fixtures/test_image_1.jpg", "rb") as f:
            file_content = f.read()

        files = {"file": ("test_image.jpg", BytesIO(file_content), "image/jpeg"),}
        params_update = {'description': 'Meme description new'}

        response = self.client.patch(f"/memes/{1}", files=files, params=params_update, headers=self.headers)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Not authenticated")

    def test_update_meme_invalid_image(self):

        with open("tests/fixtures/test.txt", "rb") as f:
            file_content = f.read()

        files = {"file": ("test.txt", BytesIO(file_content), "text/plain"),}
        params_update = {'description': 'Meme description new'}

        response = self.client.patch(f"/memes/{1}", files=files,params=params_update, headers=self.headers)

        self.assertEqual(response.status_code, 500)
        self.assertIn("Failed to upload image: 400: Uploaded file is not an image", response.json()["detail"])

    def test_update_meme_no_author(self):

        with open("tests/fixtures/test_image_1.jpg", "rb") as f:
            file_content = f.read()

        files = {"file": ("test_image.jpg", BytesIO(file_content), "image/jpeg"),}
        params_update = {'description': 'Meme description new'}

        response = self.client.patch(f"/memes/{1}", files=files, params=params_update, headers=self.headers_2)
        
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['detail'], "Only the author can update this meme.")

class TestMemePrivateRouterGetMeme(TestBaseForPrivateRouter):

    def setUp(self):
        super().setUp()

        with open("tests/fixtures/test_image_2.jpeg", "rb") as f:
            file_content = f.read()

        files = {"file": ("test_image.jpg", BytesIO(file_content), "image/jpeg"),}
        params = {'description': 'Meme description'}

        response = self.client.post("/memes/", files=files, params=params, headers=self.headers)   

    def test_get_meme_not_meme(self):
        response = self.client.get(f"/memes/{6}", headers=self.headers)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['detail'], 'Meme number 6 does not exist.')

    def test_get_meme_ok(self):
        response = self.client.get(f"/memes/{1}", headers=self.headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['id'], 1)
        self.assertEqual(response.json()['description'], 'Meme description')

    def test_get_meme_no_author(self):
        response = self.client.get(f"/memes/{1}", headers=self.headers_2)
        
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['detail'], "Only the author can access this meme.")


class TestMemePrivateRouterDeleteMeme(TestBaseForPrivateRouter):

    def setUp(self):
        super().setUp()

        with open("tests/fixtures/test_image_2.jpeg", "rb") as f:
            file_content = f.read()

        files = {"file": ("test_image.jpg", BytesIO(file_content), "image/jpeg"),}
        params = {'description': 'Meme description'}

        response = self.client.post("/memes/", files=files, params=params, headers=self.headers)   

    def test_delete_meme_not_meme(self):
        response = self.client.delete(f"/memes/{6}", headers=self.headers)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['detail'], 'Meme number 6 does not exist.')

    def test_delete_meme_ok(self):
        response = self.client.delete(f"/memes/{1}", headers=self.headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "message": "Meme number 1 deleted successfully"})

    def test_delete_meme_no_author(self):
        response = self.client.delete(f"/memes/{1}", headers=self.headers_2)
        
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['detail'], "Only the author can delete this meme.")

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