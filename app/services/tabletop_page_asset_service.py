from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tabletop_assets import TabletopAssets
from app.models.tabletop_page_assets import TabletopPageAsset
from app.models.tabletop_pages import TabletopPage
from app.models.rooms import Room
from app.models.room_users import RoomUser


async def _page_access(db, room_code: str, user_id: int, page_id: int) -> TabletopPage | None:
    result = await db.execute(
        select(TabletopPage)
        .join(Room, Room.id == TabletopPage.room_id)
        .join(RoomUser, RoomUser.room_id == Room.id)
        .where(Room.code == room_code, RoomUser.user_id == user_id, TabletopPage.id == page_id)
    )
    return result.scalar_one_or_none()


async def get_page_placement_for_user(
    db: AsyncSession, room_code: str, user_id: int, page_id: int, asset_id: int
) -> TabletopPageAsset | None:
    result = await db.execute(
        select(TabletopPageAsset)
        .join(TabletopPage, TabletopPage.id == TabletopPageAsset.page_id)
        .join(Room, Room.id == TabletopPage.room_id)
        .join(RoomUser, RoomUser.room_id == Room.id)
        .where(
            Room.code == room_code,
            RoomUser.user_id == user_id,
            TabletopPageAsset.page_id == page_id,
            TabletopPageAsset.asset_id == asset_id,
        )
    )
    return result.scalar_one_or_none()


async def upsert_page_asset(
    db: AsyncSession, room_code: str, user_id: int, page_id: int, asset_id: int, asset_data: dict
) -> TabletopPageAsset | None:
    page = await _page_access(db, room_code, user_id, page_id)
    asset_result = await db.execute(
        select(TabletopAssets).where(
            TabletopAssets.id == asset_id,
            TabletopAssets.room_id == page.room_id if page else False,
        )
    )
    asset = asset_result.scalar_one_or_none()
    if not page or not asset:
        await db.rollback()
        return None

    result = await db.execute(select(TabletopPageAsset).where(
        TabletopPageAsset.page_id == page_id,
        TabletopPageAsset.asset_id == asset_id,
    ))
    placement = result.scalar_one_or_none()
    if placement is None:
        placement = TabletopPageAsset(page_id=page_id, asset_id=asset_id, **asset_data)
        db.add(placement)
    else:
        for field, value in asset_data.items():
            setattr(placement, field, value)
    await db.commit()
    await db.refresh(placement)
    return placement


async def update_page_asset(
    db: AsyncSession, room_code: str, user_id: int, page_id: int, asset_id: int, asset_data: dict
) -> TabletopPageAsset | None:
    if not await _page_access(db, room_code, user_id, page_id):
        await db.rollback()
        return None
    result = await db.execute(select(TabletopPageAsset).where(
        TabletopPageAsset.page_id == page_id,
        TabletopPageAsset.asset_id == asset_id,
    ))
    placement = result.scalar_one_or_none()
    if not placement:
        return None
    for field, value in asset_data.items():
        setattr(placement, field, value)
    await db.commit()
    await db.refresh(placement)
    return placement


async def delete_page_asset(db: AsyncSession, room_code: str, user_id: int, page_id: int, asset_id: int) -> bool:
    if not await _page_access(db, room_code, user_id, page_id):
        await db.rollback()
        return False
    result = await db.execute(select(TabletopPageAsset).where(
        TabletopPageAsset.page_id == page_id,
        TabletopPageAsset.asset_id == asset_id,
    ))
    placement = result.scalar_one_or_none()
    if not placement:
        return False
    await db.delete(placement)
    await db.commit()
    return True
