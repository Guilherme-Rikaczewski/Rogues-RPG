from sqlalchemy import (
    Boolean,
    Column,
    Float,
    ForeignKey,
    Integer,
    String,
    text
)
from app.db.base import Base


class TabletopSettings(Base):
    __tablename__ = "tabletop_settings"

    room_id = Column(
        Integer,
        ForeignKey("rooms.id", ondelete="CASCADE"),
        primary_key=True,
    )

    visible_grid = Column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )

    movement_adaptable_to_grid = Column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )

    grid_color = Column(
        String(7), nullable=False, default="#ffffff", server_default="#ffffff"
    )

    grid_opacity = Column(
        Integer, nullable=False, default=25, server_default="25"
    )

    background_color = Column(
        String(7), nullable=False, default="#949494", server_default="#949494"
    )

    page_size_x = Column(
        Integer, nullable=False, default=1920, server_default="1920"
    )

    page_size_y = Column(
        Integer, nullable=False, default=1080, server_default="1080"
    )

    map_scale_value = Column(
        Float, nullable=False, default=1, server_default="1"
    )

    map_scale_unity = Column(
        String(32), nullable=False, default="meters", server_default="meters"
    )
