from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict
from app.schemas.tabletop_schema import TabletopLayer
from app.db.base import Base


class TabletopAssets(Base):
    __tablename__ = "tabletop_assets"

    id = Column(Integer, primary_key=True)

    asset_image_url = Column(Text, nullable=False, default='')

    asset_image_public_id = Column(Text, nullable=False, default='')

    asset_image_file_name = Column(Text, nullable=False, default='')

    token_settings = Column(
        MutableDict.as_mutable(JSONB), nullable=False, default=dict
    )

    layer = Column(
        Enum(TabletopLayer, name="tabletop_assets_layer"),
    )

    position_x = Column(String(256))

    position_y = Column(String(256))

    height = Column(String(256))

    width = Column(String(256))

    layer_order = Column(Integer, nullable=False, default=0)

    visible = Column(Boolean)

    room_id = Column(
        Integer,
        ForeignKey("rooms.id", ondelete="CASCADE"),
        index=True
    )

    sheet_id = Column(
        Integer,
        ForeignKey("sheets.id", ondelete="CASCADE"),
        unique=True,
        index=True
    )

    token_sheet_id = Column(
        Integer,
        ForeignKey("sheets.id", ondelete="SET NULL"),
        index=True,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
