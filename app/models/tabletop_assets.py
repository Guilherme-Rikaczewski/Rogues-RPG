from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum
from app.schemas.tabletop_schema import TabletopLayer
from app.db.base import Base


class TabletopAssets(Base):
    __tablename__ = "tabletop_assets"

    id = Column(Integer, primary_key=True)

    asset_image_url = Column(Text, nullable=False, default='')

    asset_image_public_id = Column(Text, nullable=False, default='')

    asset_image_file_name = Column(Text, nullable=False, default='')

    layer = Column(
        Enum(TabletopLayer, name="tabletop_assets_layer"),
    )

    position_x = Column(String(256))

    position_y = Column(String(256))

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

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
