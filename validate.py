from fastapi import HTTPException, UploadFile


def validate_image(file: UploadFile):

    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Uploaded file is not an image")

    return file