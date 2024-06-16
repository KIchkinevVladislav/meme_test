# @meme_router.get('/', response_model=list[ShowMeme])
# async def get_memes(
#     db: AsyncSession = Depends(get_db),     
#     page: int = Query(0, ge=0),
#     size: int = Query(10, le=100),
#     sort_by: str = 'id',
#     sort_desc: bool = False,):
#     memes = await get_list_memes(db=db, page=page, size=size, sort_by=sort_by, sort_desc=sort_desc)
    
#     if not memes:
#         raise HTTPException(status_code=404, detail="No memes found")
    
#     return [ShowMeme(id=meme.id, content=meme.content, image_url=meme.image_url) for meme in memes]




# async def get_list_memes(
#             db: AsyncSession, 
#             page: int, 
#             size: int, 
#             sort_by: str = 'id',
#             sort_desc: bool = False):
#     query = select(Meme).offset(page*size).limit(size)

#     # sorting
#     if sort_desc:
#         query = query.order_by(desc(getattr(Meme, sort_by)))
#     else:
#         query = query.order_by(getattr(Meme, sort_by))

#     result = await db.execute(query)
#     memes = result.scalars().all()
#     return memes




# это работает
# @meme_router.get('/memes/image')
# async def get_image(image_url: str):
#     bucket_name = 'memes'
#     file_name = image_url.split('/')[-1]

#     try:
#         response = minio_client.get_object(bucket_name, file_name)
#         content = response.read()
#         response.close()
#         response.release_conn()
#         return Response(content=content, media_type="image/jpeg")
#     except S3Error as err:
#         raise HTTPException(status_code=500, detail=f"MinIO error: {err}")



# потом проверить
# @meme_router.get('/memes/images/{meme_id}')
# async def get_image(meme_id: int, db: AsyncSession = Depends(get_db)):
#     try:
#         meme = await db.get(Meme, meme_id)
#         if not meme:
#             raise HTTPException(status_code=404, detail="Meme not found")

#         bucket_name = 'memes'
#         file_name = meme.image_url.split('/')[-1]

#         try:
#             response = minio_client.get_object(bucket_name, file_name)
#             content = response.read()
#             response.close()
#             response.release_conn()
#         except S3Error as err:
#             raise HTTPException(status_code=500, detail=f"MinIO error: {err}")

#         return Response(content=content, media_type="image/jpeg")
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error retrieving meme: {e}")
