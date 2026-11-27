from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tabletop_assets import TabletopAssets
from app.models.tabletop_page_assets import TabletopPageAsset
from app.models.tabletop_pages import TabletopPage
from app.models.rooms import Room
from app.models.room_users import RoomUser
from app.schemas.tabletop_schema import TabletopLayer
from app.services.tabletop_stack_order_service import next_page_layer_order


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


async def can_manage_token_settings(
    db: AsyncSession, room_code: str, user_id: int, page_id: int, asset_id: int
) -> bool:
    page = await _page_access(db, room_code, user_id, page_id)
    if not page:
        return False
    result = await db.execute(
        select(TabletopPageAsset.owner_user_id, TabletopAssets.user_id, TabletopPageAsset.layer)
        .join(TabletopAssets, TabletopAssets.id == TabletopPageAsset.asset_id)
        .where(
            TabletopPageAsset.page_id == page_id,
            TabletopPageAsset.asset_id == asset_id,
            TabletopAssets.room_id == page.room_id,
        )
    )
    ownership = result.first()
    return bool(
        ownership
        and ownership.layer != TabletopLayer.map
        and (ownership.owner_user_id or ownership.user_id) == user_id
    )


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
    target_layer = asset_data.get("layer") or (placement.layer if placement else None)
    layer_order = await next_page_layer_order(db, page_id, target_layer) if target_layer else None
    if layer_order is None:
        await db.rollback()
        return None
    asset_data = {**asset_data, "layer_order": layer_order}
    if placement is None:
        placement = TabletopPageAsset(
            page_id=page_id, asset_id=asset_id, owner_user_id=user_id, **asset_data
        )
        db.add(placement)
    else:
        for field, value in asset_data.items():
            setattr(placement, field, value)
    await db.commit()
    await db.refresh(placement)
    return placement


async def create_page_asset_from_image(
    db: AsyncSession, room_code: str, user_id: int, page_id: int,
    source_asset_id: int, asset_data: dict,
) -> TabletopPageAsset | None:
    """Create a distinct tabletop asset from a user's reusable room image."""
    page = await _page_access(db, room_code, user_id, page_id)
    if not page:
        await db.rollback()
        return None

    result = await db.execute(select(TabletopAssets).where(
        TabletopAssets.id == source_asset_id,
        TabletopAssets.room_id == page.room_id,
        TabletopAssets.user_id == user_id,
        TabletopAssets.asset_image_public_id != '',
    ))
    source = result.scalar_one_or_none()
    if not source:
        await db.rollback()
        return None

    layer_order = await next_page_layer_order(db, page_id, asset_data.get("layer"))
    if layer_order is None:
        await db.rollback()
        return None
    asset_data = {**asset_data, "layer_order": layer_order}

    asset = TabletopAssets(
        asset_image_url=source.asset_image_url,
        # The upload remains owned by the source library item. Copies must not
        # claim ownership of the Cloudinary object or delete it independently.
        asset_image_public_id='',
        asset_image_file_name=source.asset_image_file_name,
        token_sheet_id=source.token_sheet_id or source.sheet_id,
        room_id=page.room_id,
        user_id=user_id,
    )
    db.add(asset)
    await db.flush()
    placement = TabletopPageAsset(
        page_id=page_id, asset_id=asset.id, owner_user_id=user_id, **asset_data
    )
    db.add(placement)
    await db.commit()
    await db.refresh(placement)
    return placement


async def update_token_settings(
    db: AsyncSession, room_code: str, user_id: int, page_id: int,
    asset_id: int, token_settings: dict,
) -> bool:
    if not await _page_access(db, room_code, user_id, page_id):
        await db.rollback()
        return False
    placement_result = await db.execute(select(TabletopPageAsset).where(
        TabletopPageAsset.page_id == page_id,
        TabletopPageAsset.asset_id == asset_id,
    ))
    placement = placement_result.scalar_one_or_none()
    asset_result = await db.execute(
        select(TabletopAssets).join(
            TabletopPageAsset, TabletopPageAsset.asset_id == TabletopAssets.id
        ).where(
            TabletopPageAsset.page_id == page_id,
            TabletopPageAsset.asset_id == asset_id,
        )
    )
    asset = asset_result.scalar_one_or_none()
    if not placement or not asset:
        return False
    asset.token_settings = token_settings
    await db.commit()
    return True


async def duplicate_page_asset(
    db: AsyncSession, room_code: str, user_id: int, page_id: int,
    asset_id: int, position_x: str, position_y: str, layer_order: int,
) -> TabletopPageAsset | None:
    page = await _page_access(db, room_code, user_id, page_id)
    if not page:
        await db.rollback()
        return None
    result = await db.execute(
        select(TabletopAssets, TabletopPageAsset)
        .join(TabletopPageAsset, TabletopPageAsset.asset_id == TabletopAssets.id)
        .where(
            TabletopAssets.room_id == page.room_id,
            TabletopPageAsset.page_id == page_id,
            TabletopPageAsset.asset_id == asset_id,
        )
    )
    source, source_placement = result.first() or (None, None)
    if not source or not source_placement:
        await db.rollback()
        return None
    layer_order = await next_page_layer_order(db, page_id, source_placement.layer)
    if layer_order is None:
        await db.rollback()
        return None
    clone = TabletopAssets(
        asset_image_url=source.asset_image_url,
        asset_image_public_id='',
        asset_image_file_name=source.asset_image_file_name,
        token_settings=dict(source.token_settings or {}),
        room_id=page.room_id,
        user_id=user_id,
        token_sheet_id=source.token_sheet_id or source.sheet_id,
    )
    db.add(clone)
    await db.flush()
    placement = TabletopPageAsset(
        page_id=page_id,
        asset_id=clone.id,
        owner_user_id=user_id,
        layer=source_placement.layer,
        position_x=position_x,
        position_y=position_y,
        width=source_placement.width,
        height=source_placement.height,
        layer_order=layer_order,
        visible=source_placement.visible,
    )
    db.add(placement)
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
