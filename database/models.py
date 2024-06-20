import uuid
from sqlalchemy import (
    Column,
    String,
    Integer,
    Text,
    DateTime,
    ForeignKey,
    )
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import (
    UUID
    )

from database.db import Base

class User(Base):
    """
    Define the user model.
    """
    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    surname = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True) # we use email as username for authentific
    hashed_password = Column(String, nullable=False)

    memes = relationship(
        'Meme',
        back_populates='author',
        cascade='all, delete-orphan',
    )


class Meme(Base):
    """
    Define the meme model.
    """       
    __tablename__ = 'memes'

    id = Column(Integer, primary_key=True, index=True)
    description = Column(Text)
    image_url = Column(String, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user_id = Column(
        UUID(as_uuid=True), 
        ForeignKey('users.id', ondelete='CASCADE'), 
            nullable=False
    )

    author = relationship('User', back_populates='memes')
