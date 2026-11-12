from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tabletop_pages import TabletopPage
from app.models.tabletop_texts import TabletopText
from app.models.rooms import Room
from app.models.room_users import RoomUser


async def _accessible_page(db: AsyncSession, room_code: str, user_id: int, page_id: int):
    result = await db.execute(
        select(TabletopPage)
        .join(Room, Room.id == TabletopPage.room_id)
        .join(RoomUser, RoomUser.room_id == Room.id)
        .where(Room.code == room_code, RoomUser.user_id == user_id, TabletopPage.id == page_id)
    )
    return result.scalar_one_or_none()


async def list_page_texts(db: AsyncSession, room_id: int, page_id: int) -> list[TabletopText]:
    result = await db.execute(
        select(TabletopText).join(TabletopPage, TabletopPage.id == TabletopText.page_id)
        .where(TabletopPage.room_id == room_id, TabletopText.page_id == page_id)
        .order_by(TabletopText.layer_order, TabletopText.id)
    )
    return list(result.scalars().all())


async def get_text_for_user(db: AsyncSession, room_code: str, user_id: int, page_id: int, text_id: int):
    if not await _accessible_page(db, room_code, user_id, page_id):
        return None
    result = await db.execute(
        select(TabletopText).where(TabletopText.page_id == page_id, TabletopText.id == text_id)
    )
    return result.scalar_one_or_none()


async def create_page_text(db: AsyncSession, room_code: str, user_id: int, page_id: int, values: dict):
    page = await _accessible_page(db, room_code, user_id, page_id)
    if not page:
        return None
    text = TabletopText(page_id=page_id, user_id=user_id, **values)
    db.add(text)
    await db.commit()
    await db.refresh(text)
    return text


async def update_page_text(db: AsyncSession, room_code: str, user_id: int, page_id: int, text_id: int, values: dict):
    text = await get_text_for_user(db, room_code, user_id, page_id, text_id)
    if not text:
        return None
    for field, value in values.items():
        setattr(text, field, value)
    await db.commit()
    await db.refresh(text)
    return text


async def delete_page_text(db: AsyncSession, room_code: str, user_id: int, page_id: int, text_id: int) -> bool:
    text = await get_text_for_user(db, room_code, user_id, page_id, text_id)
    if not text:
        return False
    await db.delete(text)
    await db.commit()
    return True
