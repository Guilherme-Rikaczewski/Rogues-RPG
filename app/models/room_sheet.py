from sqlalchemy import Column, Integer, ForeignKey
from app.db.base import Base


class RoomSheet(Base):
    __tablename__ = "room_sheets"

    id = Column(Integer, primary_key=True)

    room_id = Column(
        Integer,
        ForeignKey("rooms.id", ondelete="CASCADE"),
        index=True
    )

    sheet_id = Column(
        Integer,
        ForeignKey("sheets.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
