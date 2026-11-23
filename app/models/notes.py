from sqlalchemy import Column, Integer, String, Text, ForeignKey
from app.db.base import Base


class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True)

    color = Column(String(7), nullable=False)

    tittle = Column(Text, nullable=False)

    content = Column(Text)

    position_x = Column(String(256))

    position_y = Column(String(256))

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    room_id = Column(
        Integer,
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    page_id = Column(
        Integer,
        ForeignKey("tabletop_pages.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    width = Column(String(256), nullable=True)

    height = Column(String(256), nullable=True)
