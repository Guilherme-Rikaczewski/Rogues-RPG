from sqlalchemy import Column, Enum, Float, ForeignKey, Integer, JSON, String

from app.db.base import Base
from app.schemas.tabletop_schema import TabletopLayer


class TabletopDrawing(Base):
    __tablename__ = "tabletop_drawings"

    id = Column(
        Integer,
        primary_key=True
    )

    page_id = Column(
        Integer,
        ForeignKey("tabletop_pages.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    position_x = Column(
        Float,
        nullable=False,
        default=0
    )

    position_y = Column(
        Float,
        nullable=False,
        default=0
    )

    points = Column(
        JSON,
        nullable=False
    )

    color = Column(
        String(7),
        nullable=False,
        default="#111111"
    )

    stroke_width = Column(
        Float,
        nullable=False,
        default=4
    )

    layer = Column(
        Enum(TabletopLayer,
             name="tabletop_drawings_layer"),
        nullable=False,
        default=TabletopLayer.players
    )

    layer_order = Column(
        Integer, nullable=False, default=0
    )
