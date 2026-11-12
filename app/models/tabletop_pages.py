from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, text
from app.db.base import Base


class TabletopPage(Base):
    __tablename__ = "tabletop_pages"

    id = Column(
        Integer, primary_key=True
    )

    room_id = Column(
        Integer,
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    folder_id = Column(
        Integer,
        ForeignKey("tabletop_folders.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    name = Column(
        String(120), nullable=False
    )

    display_order = Column(
        Integer, nullable=False, default=0
    )

    is_players_page = Column(
        Boolean, nullable=False,
        default=False,
        server_default=text("false")
    )
