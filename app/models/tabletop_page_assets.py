from sqlalchemy import Boolean, Column, Enum, ForeignKey, Integer, String
from app.db.base import Base
from app.schemas.tabletop_schema import TabletopLayer


class TabletopPageAsset(Base):
    __tablename__ = "tabletop_page_assets"

    page_id = Column(
        Integer,
        ForeignKey("tabletop_pages.id", ondelete="CASCADE"),
        primary_key=True
    )

    asset_id = Column(
        Integer,
        ForeignKey("tabletop_assets.id", ondelete="CASCADE"),
        primary_key=True
    )

    layer = Column(
        Enum(TabletopLayer, name="tabletop_page_assets_layer"),
        nullable=False
    )

    position_x = Column(String(256), nullable=False)

    position_y = Column(String(256), nullable=False)

    height = Column(String(256), nullable=True)

    width = Column(String(256), nullable=True)

    layer_order = Column(Integer, nullable=False, default=0)

    visible = Column(Boolean, nullable=True)
