import uuid

from fastapi import HTTPException, UploadFile
from minio import Minio
from minio.error import S3Error

from config import MINIO_ACCESS_KEY, MINIO_ENDPOINT, MINIO_SECRET_KEY

minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False
)


async def upload_image_to_minio(file: UploadFile) -> str:
    bucket_name = 'memes'
    if not minio_client.bucket_exists(bucket_name):
        minio_client.make_bucket(bucket_name)

    file_id = str(uuid.uuid4())
    file_name = f"{file_id}_{file.filename}"

    try:
        minio_client.put_object(bucket_name, file_name, file.file, length=-1, part_size=10*1024*1024)
    except S3Error as err:
        raise HTTPException(status_code=500, detail=f"MinIO error: {err}")
    
    return f"http://127.0.0.1:9001/{bucket_name}/{file_name}"


async def delete_image_from_minio(image_url: str):
    try:
        bucket_name = "memes"
        file_name = image_url.split("/")[-1]

        minio_client.remove_object(bucket_name, file_name)
        
    except S3Error as err:
        raise HTTPException(status_code=500, detail=f"MinIO error: {err}")
    

async def update_image_in_minio(file: UploadFile, image_url: str):
    new_image_url = await upload_image_to_minio(file)
    await delete_image_from_minio(image_url)

    return new_image_url
