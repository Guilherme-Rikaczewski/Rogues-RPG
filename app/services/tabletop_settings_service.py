from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.rooms import Room
from app.models.room_users import RoomUser
from app.models.tabletop_settings import TabletopSettings
from app.models.tabletop_pages import TabletopPage
from app.models.tabletop_page_settings import TabletopPageSettings
from app.schemas.room_schema import RoomRole


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
    page_id: int | None = None,
) -> TabletopPageSettings | None:
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
    membership = membership_result.scalar_one_or_none()
    if not membership or membership.role != RoomRole.master:
        return None

    page_result = await db.execute(
        select(TabletopPage).where(
            TabletopPage.room_id == room.id,
            TabletopPage.id == page_id if page_id is not None else TabletopPage.is_players_page.is_(True),
        )
    )
    page = page_result.scalar_one_or_none()
    if not page:
        return None
    settings_result = await db.execute(
        select(TabletopPageSettings).where(TabletopPageSettings.page_id == page.id)
    )
    settings = settings_result.scalar_one_or_none()
    if not settings:
        settings = TabletopPageSettings(page_id=page.id)
        db.add(settings)
        await db.flush()
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
