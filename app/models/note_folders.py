from sqlalchemy import Column, ForeignKey, Integer, String
from app.db.base import Base


class NoteFolder(Base):
    __tablename__ = "note_folders"

    id = Column(Integer, primary_key=True)
    room_id = Column(Integer, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(120), nullable=False)
    display_order = Column(Integer, nullable=False, default=0)
