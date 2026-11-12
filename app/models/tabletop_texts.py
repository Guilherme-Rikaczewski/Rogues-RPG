from sqlalchemy import Boolean, Column, Enum, Float, ForeignKey, Integer, String, Text

from app.db.base import Base
from app.schemas.tabletop_schema import TabletopLayer


class TabletopText(Base):
    __tablename__ = "tabletop_texts"

    id = Column(Integer, primary_key=True)

    page_id = Column(
        Integer,
        ForeignKey("tabletop_pages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    content = Column(Text, nullable=False, default="")

    position_x = Column(Float, nullable=False, default=0)

    position_y = Column(Float, nullable=False, default=0)

    layer = Column(
        Enum(TabletopLayer, name="tabletop_text_layer"),
        nullable=False,
        default=TabletopLayer.players,
    )

    font_family = Column(String(100), nullable=False, default="Arial")

    font_size = Column(Integer, nullable=False, default=24)

    color = Column(String(7), nullable=False, default="#EFE5D5")

    bold = Column(Boolean, nullable=False, default=False)

    italic = Column(Boolean, nullable=False, default=False)

    layer_order = Column(Integer, nullable=False, default=0)
