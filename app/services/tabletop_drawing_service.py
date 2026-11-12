from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rooms import Room
from app.models.room_users import RoomUser
from app.models.tabletop_drawings import TabletopDrawing
from app.models.tabletop_pages import TabletopPage


async def _accessible_page(db: AsyncSession, room_code: str, user_id: int, page_id: int):
    result = await db.execute(
        select(TabletopPage)
        .join(Room, Room.id == TabletopPage.room_id)
        .join(RoomUser, RoomUser.room_id == Room.id)
        .where(Room.code == room_code, RoomUser.user_id == user_id, TabletopPage.id == page_id)
    )
    return result.scalar_one_or_none()


async def list_page_drawings(db: AsyncSession, room_id: int, page_id: int) -> list[TabletopDrawing]:
    result = await db.execute(
        select(TabletopDrawing).join(TabletopPage, TabletopPage.id == TabletopDrawing.page_id)
        .where(TabletopPage.room_id == room_id, TabletopDrawing.page_id == page_id)
        .order_by(TabletopDrawing.layer_order, TabletopDrawing.id)
    )
    return list(result.scalars().all())


async def get_drawing_for_user(db: AsyncSession, room_code: str, user_id: int, page_id: int, drawing_id: int):
    if not await _accessible_page(db, room_code, user_id, page_id):
        return None
    result = await db.execute(
        select(TabletopDrawing).where(TabletopDrawing.page_id == page_id, TabletopDrawing.id == drawing_id)
    )
    return result.scalar_one_or_none()


async def create_page_drawing(db: AsyncSession, room_code: str, user_id: int, page_id: int, values: dict):
    if not await _accessible_page(db, room_code, user_id, page_id):
        return None
    drawing = TabletopDrawing(page_id=page_id, user_id=user_id, **values)
    db.add(drawing)
    await db.commit()
    await db.refresh(drawing)
    return drawing


async def move_page_drawing(db: AsyncSession, room_code: str, user_id: int, page_id: int, drawing_id: int, x: float, y: float):
    drawing = await get_drawing_for_user(db, room_code, user_id, page_id, drawing_id)
    if not drawing:
        return None
    drawing.position_x = x
    drawing.position_y = y
    await db.commit()
    await db.refresh(drawing)
    return drawing


async def delete_page_drawing(db: AsyncSession, room_code: str, user_id: int, page_id: int, drawing_id: int) -> bool:
    drawing = await get_drawing_for_user(db, room_code, user_id, page_id, drawing_id)
    if not drawing:
        return False
    await db.delete(drawing)
    await db.commit()
    return True
