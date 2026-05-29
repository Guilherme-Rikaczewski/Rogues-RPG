from sqlalchemy import Column, Integer, String, DateTime, func, Text
from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)

    username = Column(String(20), unique=True, nullable=False)

    email = Column(String(256), unique=True, nullable=False)

    password = Column(Text, nullable=False)

    storage_usage = Column(Integer, nullable=False, default=0)

    hours_played = Column(Integer, nullable=False, default=0)

    profilepic_image_url = Column(Text, nullable=False, default='')

    profilepic_image_size = Column(Integer, nullable=False, default=0)

    profilepic_image_public_id = Column(Text, nullable=False, default='')

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
