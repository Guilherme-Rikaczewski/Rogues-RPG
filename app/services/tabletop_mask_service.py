from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rooms import Room
from app.models.room_users import RoomUser
from app.models.tabletop_page_masks import TabletopPageMask, TabletopPageMaskSetting
from app.models.tabletop_pages import TabletopPage


async def _accessible_page(db: AsyncSession, room_code: str, user_id: int, page_id: int):
    result = await db.execute(
        select(TabletopPage)
        .join(Room, Room.id == TabletopPage.room_id)
        .join(RoomUser, RoomUser.room_id == Room.id)
        .where(Room.code == room_code, RoomUser.user_id == user_id, TabletopPage.id == page_id)
    )
    return result.scalar_one_or_none()


async def list_page_masks(db: AsyncSession, room_id: int, page_id: int) -> list[TabletopPageMask]:
    result = await db.execute(
        select(TabletopPageMask).join(TabletopPage, TabletopPage.id == TabletopPageMask.page_id)
        .where(TabletopPage.room_id == room_id, TabletopPageMask.page_id == page_id)
        .order_by(TabletopPageMask.id)
    )
    return list(result.scalars().all())


async def get_page_mask_opacity(db: AsyncSession, page_id: int) -> int:
    result = await db.execute(select(TabletopPageMaskSetting).where(TabletopPageMaskSetting.page_id == page_id))
    setting = result.scalar_one_or_none()
    return setting.dm_darkness_opacity if setting else 45


async def create_page_mask(db: AsyncSession, room_code: str, user_id: int, page_id: int, operation: str, shape: str, points: list[dict]):
    if not await _accessible_page(db, room_code, user_id, page_id):
        return None
    mask = TabletopPageMask(page_id=page_id, user_id=user_id, operation=operation, shape=shape, points=points)
    db.add(mask)
    await db.commit()
    await db.refresh(mask)
    return mask


async def delete_page_mask(db: AsyncSession, room_code: str, user_id: int, page_id: int, mask_id: int) -> bool:
    if not await _accessible_page(db, room_code, user_id, page_id):
        return False
    result = await db.execute(select(TabletopPageMask).where(TabletopPageMask.page_id == page_id, TabletopPageMask.id == mask_id))
    mask = result.scalar_one_or_none()
    if not mask:
        return False
    await db.delete(mask)
    await db.commit()
    return True


async def update_page_mask_opacity(db: AsyncSession, room_code: str, user_id: int, page_id: int, opacity: int):
    if not await _accessible_page(db, room_code, user_id, page_id):
        return None
    result = await db.execute(select(TabletopPageMaskSetting).where(TabletopPageMaskSetting.page_id == page_id))
    setting = result.scalar_one_or_none()
    if setting is None:
        setting = TabletopPageMaskSetting(page_id=page_id, dm_darkness_opacity=opacity)
        db.add(setting)
    else:
        setting.dm_darkness_opacity = opacity
    await db.commit()
    await db.refresh(setting)
    return setting
