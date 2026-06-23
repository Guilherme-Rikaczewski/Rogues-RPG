from sqlalchemy import Column, Integer, String, DateTime, func, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict
from app.db.base import Base


class Sheet(Base):
    __tablename__ = "sheets"

    id = Column(Integer, primary_key=True)

    game_system = Column(String(256), nullable=False)

    sheet_type = Column(String(6), nullable=False, default='player')

    name = Column(Text, nullable=False)

    content = Column(
        MutableDict.as_mutable(JSONB),
        nullable=False,
        default=dict
    )

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
