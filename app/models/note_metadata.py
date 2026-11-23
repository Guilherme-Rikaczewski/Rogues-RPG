from sqlalchemy import Boolean, Column, ForeignKey, Integer, text
from app.db.base import Base


class NoteMetadata(Base):
    __tablename__ = "note_metadata"

    note_id = Column(Integer, ForeignKey("notes.id", ondelete="CASCADE"), primary_key=True)
    folder_id = Column(Integer, ForeignKey("note_folders.id", ondelete="SET NULL"), nullable=True, index=True)
    colors_hidden = Column(Boolean, nullable=False, default=False, server_default=text("false"))
