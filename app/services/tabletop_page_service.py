from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.rooms import Room
from app.models.room_users import RoomUser
from app.models.tabletop_assets import TabletopAssets
from app.models.tabletop_folders import TabletopFolder
from app.models.tabletop_page_assets import TabletopPageAsset
from app.models.tabletop_pages import TabletopPage
from app.models.tabletop_page_settings import TabletopPageSettings
from app.models.tabletop_settings import TabletopSettings
from app.schemas.room_schema import RoomRole
from app.schemas.tabletop_schema import TabletopAssetResponse, TabletopLayer


_SETTING_FIELDS = (
    "visible_grid",
    "movement_adaptable_to_grid",
    "grid_color",
    "grid_opacity",
    "background_color",
    "page_size_x",
    "page_size_y",
    "map_scale_value",
    "map_scale_unity",
)


async def _lock_room(db: AsyncSession, room_id: int) -> Room | None:
    result = await db.execute(
        select(Room).where(Room.id == room_id).with_for_update()
    )
    return result.scalar_one_or_none()


async def _ensure_page_settings(
    db: AsyncSession,
    page: TabletopPage,
    legacy_settings: TabletopSettings | None = None,
) -> TabletopPageSettings:
    result = await db.execute(
        select(TabletopPageSettings).where(TabletopPageSettings.page_id == page.id)
    )
    settings = result.scalar_one_or_none()
    if settings:
        return settings

    values = {
        field: getattr(legacy_settings, field)
        for field in _SETTING_FIELDS
        if legacy_settings is not None
    }
    settings = TabletopPageSettings(page_id=page.id, **values)
    db.add(settings)
    await db.flush()
    return settings


async def ensure_room_pages(
    db: AsyncSession,
    room_id: int,
) -> tuple[list[TabletopPage], list[TabletopFolder], TabletopPage]:
    room = await _lock_room(db, room_id)
    if not room:
        raise ValueError("Room not found")

    result = await db.execute(
        select(TabletopPage)
        .where(TabletopPage.room_id == room_id)
        .order_by(TabletopPage.display_order, TabletopPage.id)
    )
    pages = list(result.scalars().all())

    folders_result = await db.execute(
        select(TabletopFolder)
        .where(TabletopFolder.room_id == room_id)
        .order_by(TabletopFolder.display_order, TabletopFolder.id)
    )
    folders = list(folders_result.scalars().all())

    legacy_result = await db.execute(
        select(TabletopSettings).where(TabletopSettings.room_id == room_id)
    )
    legacy_settings = legacy_result.scalar_one_or_none()

    if not pages:
        first_page = TabletopPage(
            room_id=room_id,
            folder_id=None,
            name="Page 1",
            display_order=0,
            is_players_page=True,
        )
        db.add(first_page)
        await db.flush()
        await _ensure_page_settings(db, first_page, legacy_settings)

        legacy_assets_result = await db.execute(
            select(TabletopAssets).where(
                TabletopAssets.room_id == room_id,
                TabletopAssets.layer.is_not(None),
            )
        )
        for asset in legacy_assets_result.scalars().all():
            db.add(TabletopPageAsset(
                page_id=first_page.id,
                asset_id=asset.id,
                layer=asset.layer,
                position_x=asset.position_x or "0",
                position_y=asset.position_y or "0",
                width=asset.width,
                height=asset.height,
                layer_order=asset.layer_order or 0,
                visible=asset.visible,
            ))
            asset.layer = None
            asset.position_x = None
            asset.position_y = None
            asset.width = None
            asset.height = None
            asset.layer_order = 0
            asset.visible = None

        pages = [first_page]
    else:
        active_pages = [page for page in pages if page.is_players_page]
        if not active_pages:
            pages[0].is_players_page = True
        elif len(active_pages) > 1:
            for page in active_pages[1:]:
                page.is_players_page = False
        for page in pages:
            await _ensure_page_settings(
                db,
                page,
                legacy_settings if page.id == pages[0].id else None,
            )

    await db.commit()
    active_page = next((page for page in pages if page.is_players_page), pages[0])
    return pages, folders, active_page


async def get_page_assets(
    db: AsyncSession,
    room_id: int,
    page_id: int,
) -> list[TabletopAssetResponse]:
    assets_result = await db.execute(
        select(TabletopAssets)
        .where(TabletopAssets.room_id == room_id)
        .order_by(TabletopAssets.id)
    )
    assets = assets_result.scalars().all()

    placements_result = await db.execute(
        select(TabletopPageAsset).where(TabletopPageAsset.page_id == page_id)
    )
    placements = {placement.asset_id: placement for placement in placements_result.scalars().all()}

    responses = []
    for asset in assets:
        placement = placements.get(asset.id)
        responses.append(TabletopAssetResponse.model_validate({
            "id": asset.id,
            "asset_image_url": asset.asset_image_url,
            "asset_image_public_id": asset.asset_image_public_id,
            "asset_image_file_name": asset.asset_image_file_name,
            "layer": placement.layer if placement else None,
            "position_x": placement.position_x if placement else None,
            "position_y": placement.position_y if placement else None,
            "visible": placement.visible if placement else None,
            "height": placement.height if placement else None,
            "width": placement.width if placement else None,
            "layer_order": placement.layer_order if placement else 0,
        }))
    return responses


async def get_page_previews(
    db: AsyncSession,
    room_id: int,
    pages: list[TabletopPage],
) -> dict[int, str]:
    if not pages:
        return {}
    result = await db.execute(
        select(TabletopPageAsset.page_id, TabletopAssets.asset_image_url)
        .join(TabletopAssets, TabletopAssets.id == TabletopPageAsset.asset_id)
        .where(
            TabletopPageAsset.page_id.in_([page.id for page in pages]),
            TabletopPageAsset.layer == TabletopLayer.map,
            TabletopAssets.room_id == room_id,
        )
        .order_by(TabletopPageAsset.page_id, TabletopPageAsset.layer_order, TabletopPageAsset.asset_id)
    )
    previews: dict[int, str] = {}
    for page_id, image_url in result.all():
        if page_id not in previews:
            previews[page_id] = image_url
    return previews


async def _get_master_room(
    db: AsyncSession,
    room_code: str,
    user_id: int,
) -> Room | None:
    room_result = await db.execute(
        select(Room).where(Room.code == room_code).with_for_update()
    )
    room = room_result.scalar_one_or_none()
    if not room:
        return None
    member_result = await db.execute(
        select(RoomUser).where(
            RoomUser.room_id == room.id,
            RoomUser.user_id == user_id,
            RoomUser.role == RoomRole.master,
        )
    )
    return room if member_result.scalar_one_or_none() else None


async def is_room_master(
    db: AsyncSession,
    room_code: str,
    user_id: int,
) -> bool:
    result = await db.execute(
        select(RoomUser.id)
        .join(Room, Room.id == RoomUser.room_id)
        .where(
            Room.code == room_code,
            RoomUser.user_id == user_id,
            RoomUser.role == RoomRole.master,
        )
    )
    return result.scalar_one_or_none() is not None


async def create_page(db: AsyncSession, room_code: str, user_id: int) -> TabletopPage | None:
    room = await _get_master_room(db, room_code, user_id)
    if not room:
        return None
    result = await db.execute(
        select(TabletopPage).where(TabletopPage.room_id == room.id)
        .order_by(TabletopPage.display_order, TabletopPage.id)
    )
    pages = list(result.scalars().all())
    page = TabletopPage(
        room_id=room.id,
        folder_id=None,
        name=f"Page {len(pages) + 1}",
        display_order=len(pages),
        is_players_page=False,
    )
    db.add(page)
    await db.flush()
    active = next((item for item in pages if item.is_players_page), None)
    active_settings = None
    if active:
        settings_result = await db.execute(
            select(TabletopPageSettings).where(TabletopPageSettings.page_id == active.id)
        )
        active_settings = settings_result.scalar_one_or_none()
    settings_values = {
        field: getattr(active_settings, field)
        for field in _SETTING_FIELDS
        if active_settings is not None
    }
    db.add(TabletopPageSettings(page_id=page.id, **settings_values))
    await db.commit()
    await db.refresh(page)
    return page


async def create_folder(db: AsyncSession, room_code: str, user_id: int) -> TabletopFolder | None:
    room = await _get_master_room(db, room_code, user_id)
    if not room:
        return None
    result = await db.execute(select(TabletopFolder).where(TabletopFolder.room_id == room.id))
    folders = list(result.scalars().all())
    folder = TabletopFolder(room_id=room.id, name=f"Folder {len(folders) + 1}", display_order=len(folders))
    db.add(folder)
    await db.commit()
    await db.refresh(folder)
    return folder


async def rename_page(db: AsyncSession, room_code: str, user_id: int, page_id: int, name: str) -> TabletopPage | None:
    room = await _get_master_room(db, room_code, user_id)
    clean_name = name.strip()
    if not room or not clean_name or len(clean_name) > 120:
        return None
    result = await db.execute(select(TabletopPage).where(TabletopPage.id == page_id, TabletopPage.room_id == room.id))
    page = result.scalar_one_or_none()
    if not page:
        await db.rollback()
        return None
    page.name = clean_name
    await db.commit()
    await db.refresh(page)
    return page


async def rename_folder(db: AsyncSession, room_code: str, user_id: int, folder_id: int, name: str) -> TabletopFolder | None:
    room = await _get_master_room(db, room_code, user_id)
    clean_name = name.strip()
    if not room or not clean_name or len(clean_name) > 120:
        return None
    result = await db.execute(select(TabletopFolder).where(TabletopFolder.id == folder_id, TabletopFolder.room_id == room.id))
    folder = result.scalar_one_or_none()
    if not folder:
        await db.rollback()
        return None
    folder.name = clean_name
    await db.commit()
    await db.refresh(folder)
    return folder


async def move_page(db: AsyncSession, room_code: str, user_id: int, page_id: int, folder_id: int | None) -> TabletopPage | None:
    room = await _get_master_room(db, room_code, user_id)
    if not room:
        return None
    page_result = await db.execute(select(TabletopPage).where(TabletopPage.id == page_id, TabletopPage.room_id == room.id))
    page = page_result.scalar_one_or_none()
    if not page:
        await db.rollback()
        return None
    if folder_id is not None:
        folder_result = await db.execute(select(TabletopFolder).where(TabletopFolder.id == folder_id, TabletopFolder.room_id == room.id))
        if not folder_result.scalar_one_or_none():
            await db.rollback()
            return None
    page.folder_id = folder_id
    result = await db.execute(
        select(TabletopPage).where(TabletopPage.room_id == room.id, TabletopPage.folder_id == folder_id)
    )
    siblings = [item for item in result.scalars().all() if item.id != page.id]
    page.display_order = len(siblings)
    await db.commit()
    await db.refresh(page)
    return page


async def set_players_page(db: AsyncSession, room_code: str, user_id: int, page_id: int) -> TabletopPage | None:
    room = await _get_master_room(db, room_code, user_id)
    if not room:
        return None
    result = await db.execute(select(TabletopPage).where(TabletopPage.id == page_id, TabletopPage.room_id == room.id))
    page = result.scalar_one_or_none()
    if not page:
        await db.rollback()
        return None
    await db.execute(update(TabletopPage).where(TabletopPage.room_id == room.id).values(is_players_page=False))
    page.is_players_page = True
    await db.commit()
    await db.refresh(page)
    return page
