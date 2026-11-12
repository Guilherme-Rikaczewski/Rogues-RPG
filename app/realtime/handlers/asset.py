from app.realtime.connection.manager import manager
from app.schemas.tabletop_schema import AssetUpdate, TabletopLayer
from app.services.tabletop_page_asset_service import (
    delete_page_asset,
    get_page_placement_for_user,
    update_page_asset,
    upsert_page_asset,
)
from app.services.tabletop_page_service import is_room_master


async def _reject(room_code, user_id, message):
    await manager.send_to_user(room_code, user_id, {
        'event': 'error', 'payload': {'message': message}
    })
    return False


async def _can_edit_placement(db, data, room_code, user_id):
    if data.page_id is None:
        return False
    placement = await get_page_placement_for_user(
        db, room_code, user_id, data.page_id, data.asset_id
    )
    if not placement:
        return False
    return placement.layer == TabletopLayer.players or await is_room_master(db, room_code, user_id)


async def _update(db, data, room_code, user_id, values, failure_message):
    if data.page_id is None:
        updated = None
    else:
        updated = await update_page_asset(
            db, room_code, user_id, data.page_id, data.asset_id,
            values.model_dump(exclude_unset=True)
        )
    if not updated:
        await manager.send_to_user(room_code, user_id, {
            'event': 'error', 'payload': {'message': failure_message}
        })
        return False
    return True


async def handle_asset_move(db, data, room_code, user_id) -> bool:
    if not await _can_edit_placement(db, data, room_code, user_id):
        return await _reject(room_code, user_id, "You can't move assets on this layer")
    return await _update(db, data, room_code, user_id,
        AssetUpdate(position_x=data.x, position_y=data.y), "Can't move the asset")


async def handle_asset_change_layer(db, data, room_code, user_id) -> bool:
    if not await is_room_master(db, room_code, user_id):
        return await _reject(room_code, user_id, "Only the room master can change asset layers")
    return await _update(db, data, room_code, user_id,
        AssetUpdate(layer=data.layer), "Can't change the asset layer")


async def handle_asset_change_order(db, data, room_code, user_id) -> bool:
    if not await is_room_master(db, room_code, user_id):
        return await _reject(room_code, user_id, "Only the room master can change layer order")
    return await _update(db, data, room_code, user_id,
        AssetUpdate(layer=data.layer, layer_order=data.layer_order), "Can't change the asset order")


async def handle_asset_remove_from_tabletop(db, data, room_code, user_id) -> bool:
    if not await _can_edit_placement(db, data, room_code, user_id):
        return await _reject(room_code, user_id, "You can't remove assets on this layer")
    removed = data.page_id is not None and await delete_page_asset(
        db, room_code, user_id, data.page_id, data.asset_id
    )
    if not removed:
        await manager.send_to_user(room_code, user_id, {
            'event': 'error', 'payload': {'message': "Can't remove the asset from tabletop"}
        })
    return bool(removed)


async def handle_asset_insert(db, data, room_code, user_id) -> bool:
    master = await is_room_master(db, room_code, user_id)
    if not master and data.asset_data.layer != TabletopLayer.players:
        return await _reject(room_code, user_id, "Players can only insert assets into their layer")
    if data.asset_data.layer is None:
        return await _reject(room_code, user_id, "An asset layer is required")
    if not master:
        existing_placement = await get_page_placement_for_user(
            db, room_code, user_id, data.page_id, data.asset_id
        )
        if existing_placement and existing_placement.layer != TabletopLayer.players:
            return await _reject(room_code, user_id, "Players can't move assets from another layer")
    inserted = await upsert_page_asset(
        db, room_code, user_id, data.page_id, data.asset_id,
        data.asset_data.model_dump(exclude_unset=True, exclude_none=True),
    )
    if not inserted:
        await manager.send_to_user(room_code, user_id, {
            'event': 'error', 'payload': {'message': "Can't insert the asset"}
        })
        return False
    return True


async def handle_asset_change_visibility(db, data, room_code, user_id):
    if not await is_room_master(db, room_code, user_id):
        return await _reject(room_code, user_id, "Only the room master can change asset visibility")
    return await _update(db, data, room_code, user_id,
        AssetUpdate(visible=data.visible), "Can't change the asset visibility")


async def handle_asset_change_size(db, data, room_code, user_id):
    if not await _can_edit_placement(db, data, room_code, user_id):
        return await _reject(room_code, user_id, "You can't resize assets on this layer")
    return await _update(db, data, room_code, user_id,
        AssetUpdate(height=data.height, width=data.width), "Can't change the asset size")
