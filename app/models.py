from sqlalchemy import (
    Column,
    String,
    Integer,
    Text,
    )

from .db import Base


class Meme(Base):
    """
    Define the meme model.
    """       
    __tablename__ = 'memes'

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text)
    image_url = Column(String, unique=True)