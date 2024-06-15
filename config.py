import uuid

from minio import Minio
from minio.error import S3Error
from fastapi import UploadFile, HTTPException


minio_endpoint = 'localhost:9000'
minio_acces_key = 'admin'
minio_secret_key='password'

minio_client = Minio(
    minio_endpoint,
    access_key=minio_acces_key,
    secret_key=minio_secret_key,
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
