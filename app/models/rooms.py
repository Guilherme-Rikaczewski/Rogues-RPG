from sqlalchemy import Column, Integer, String, DateTime, Text, func
from app.db.base import Base


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True)

    room_name = Column(String(100), nullable=False)

    code = Column(String(6), unique=True, nullable=False, index=True)
    
    thumb_image_url = Column(Text, nullable=False, default='')
    
    thumb_image_size = Column(Integer, nullable=False, default=0)
    
    thumb_image_public_id = Column(Text, nullable=False, default='')

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
