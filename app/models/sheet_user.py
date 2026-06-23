from sqlalchemy import Column, Integer, DateTime, ForeignKey, func, Boolean
from app.db.base import Base
from app.schemas.room_schema import RoomRole


class SheetUser(Base):
    __tablename__ = "sheet_users"

    id = Column(Integer, primary_key=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    sheet_id = Column(
        Integer,
        ForeignKey("sheets.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    owner = Column(
        Boolean,
        nullable=False,
    )

    last_access = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
