from sqlalchemy import Column, ForeignKey, Integer, JSON, String

from app.db.base import Base


class TabletopPageMask(Base):
    __tablename__ = "tabletop_page_masks"

    id = Column(Integer, primary_key=True)
    page_id = Column(Integer, ForeignKey("tabletop_pages.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    operation = Column(String(8), nullable=False)
    shape = Column(String(16), nullable=False)
    points = Column(JSON, nullable=False, default=list)


class TabletopPageMaskSetting(Base):
    __tablename__ = "tabletop_page_mask_settings"

    page_id = Column(Integer, ForeignKey("tabletop_pages.id", ondelete="CASCADE"), primary_key=True)
    dm_darkness_opacity = Column(Integer, nullable=False, default=45, server_default="45")
