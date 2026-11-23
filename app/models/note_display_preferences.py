from sqlalchemy import Boolean, Column, ForeignKey, Integer, text
from app.db.base import Base


class NoteDisplayPreferences(Base):
    __tablename__ = "note_display_preferences"

    note_id = Column(Integer, ForeignKey("notes.id", ondelete="CASCADE"), primary_key=True)
    colors_centered = Column(Boolean, nullable=False, default=False, server_default=text("false"))
