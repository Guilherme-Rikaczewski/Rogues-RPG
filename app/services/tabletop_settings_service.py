from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.rooms import Room
from app.models.room_users import RoomUser
from app.models.tabletop_settings import TabletopSettings


async def get_or_create_tabletop_settings(
    db: AsyncSession,
    room_id: int,
) -> TabletopSettings:
    result = await db.execute(
        select(TabletopSettings).where(TabletopSettings.room_id == room_id)
    )
    settings = result.scalar_one_or_none()
    if settings:
        return settings

    await db.execute(
        insert(TabletopSettings)
        .values(room_id=room_id)
        .on_conflict_do_nothing(index_elements=[TabletopSettings.room_id])
    )
    await db.commit()

    result = await db.execute(
        select(TabletopSettings).where(TabletopSettings.room_id == room_id)
    )
    return result.scalar_one()


async def update_room_tabletop_settings(
    db: AsyncSession,
    room_code: str,
    user_id: int,
    settings_data: dict,
) -> TabletopSettings | None:
    room_result = await db.execute(
        select(Room).where(Room.code == room_code)
    )
    room = room_result.scalar_one_or_none()
    if not room:
        return None

    membership_result = await db.execute(
        select(RoomUser).where(
            RoomUser.room_id == room.id,
            RoomUser.user_id == user_id,
        )
    )
    if not membership_result.scalar_one_or_none():
        return None

    settings = await get_or_create_tabletop_settings(db, room.id)
    allowed_fields = {
        "visible_grid",
        "movement_adaptable_to_grid",
        "grid_color",
        "grid_opacity",
        "background_color",
        "page_size_x",
        "page_size_y",
        "map_scale_value",
        "map_scale_unity",
    }
    for field, value in settings_data.items():
        if field in allowed_fields:
            setattr(settings, field, value)

    await db.commit()
    await db.refresh(settings)
    return settings
