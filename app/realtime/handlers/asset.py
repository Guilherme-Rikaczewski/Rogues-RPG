from app.realtime.connection.manager import manager
from app.schemas.tabletop_schema import AssetUpdate, TabletopLayer
from app.services.tabletop_page_asset_service import (
    delete_page_asset,
    get_page_placement_for_user,
    update_page_asset,
    upsert_page_asset,
    create_page_asset_from_image,
    update_token_settings,
    duplicate_page_asset,
    can_manage_token_settings,
)
from app.services.tabletop_page_service import is_room_master
import math
import re


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
    if await is_room_master(db, room_code, user_id):
        return True
    return placement.layer != TabletopLayer.map and await can_manage_token_settings(
        db, room_code, user_id, data.page_id, data.asset_id
    )


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
    master = await is_room_master(db, room_code, user_id)
    if not master and (
        data.layer != TabletopLayer.players
        or not await _can_edit_placement(db, data, room_code, user_id)
    ):
        return await _reject(room_code, user_id, "You can't change this token's layer")
    return await _update(db, data, room_code, user_id,
        AssetUpdate(layer=data.layer), "Can't change the asset layer")


async def handle_asset_change_order(db, data, room_code, user_id) -> bool:
    master = await is_room_master(db, room_code, user_id)
    if not await _can_edit_placement(db, data, room_code, user_id):
        return await _reject(room_code, user_id, "You can't change this token's order")
    if not master:
        placement = await get_page_placement_for_user(
            db, room_code, user_id, data.page_id, data.asset_id
        )
        if not placement or data.layer != placement.layer:
            return await _reject(room_code, user_id, "You can't move this token to another layer")
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
        if existing_placement and (
            existing_placement.layer == TabletopLayer.map
            or not await can_manage_token_settings(
                db, room_code, user_id, data.page_id, data.asset_id
            )
        ):
            return await _reject(room_code, user_id, "You can't edit this token")
    inserted = await upsert_page_asset(
        db, room_code, user_id, data.page_id, data.asset_id,
        data.asset_data.model_dump(exclude_unset=True, exclude_none=True),
    )
    if not inserted:
        await manager.send_to_user(room_code, user_id, {
            'event': 'error', 'payload': {'message': "Can't insert the asset"}
        })
        return False
    data.asset_data.layer_order = inserted.layer_order
    return True


async def handle_asset_create_from_image(db, data, room_code, user_id) -> bool:
    if data.asset_data.layer is None:
        return await _reject(room_code, user_id, "An asset layer is required")
    if data.asset_data.layer != TabletopLayer.players and not await is_room_master(db, room_code, user_id):
        return await _reject(room_code, user_id, "Players can only insert assets into their layer")

    placement = await create_page_asset_from_image(
        db, room_code, user_id, data.page_id, data.source_asset_id,
        data.asset_data.model_dump(exclude_unset=True, exclude_none=True),
    )
    if not placement:
        return await _reject(room_code, user_id, "Can't create the asset from this image")

    # Broadcast the normal insertion shape with the newly allocated identity.
    data.asset_data.layer_order = placement.layer_order
    data.type = "asset.insert"
    data.asset_id = placement.asset_id
    return True


async def handle_asset_update_token_settings(db, data, room_code, user_id) -> bool:
    if (not await is_room_master(db, room_code, user_id)
            and not await can_manage_token_settings(db, room_code, user_id, data.page_id, data.asset_id)):
        return await _reject(room_code, user_id, "You can't edit this token")
    settings = data.token_settings
    if len(str(settings)) > 12000:
        return await _reject(room_code, user_id, "Token settings are too large")
    if not _valid_token_settings(settings):
        return await _reject(room_code, user_id, "Invalid token settings")
    updated = await update_token_settings(
        db, room_code, user_id, data.page_id, data.asset_id, settings
    )
    if not updated:
        return await _reject(room_code, user_id, "Can't save token settings")
    return True


def _valid_token_settings(settings: dict) -> bool:
    visibility = {"invisible", "everyone", "owner", "dm"}
    color_ok = lambda value: isinstance(value, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", value) is not None
    number_ok = lambda value: isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and 0 <= value <= 100
    value_ok = lambda value: value == "" or (isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and 0 <= value <= 1000000000)
    if set(settings) != {"bars", "general", "auras"}:
        return False
    bars, auras, general = settings["bars"], settings["auras"], settings["general"]
    if not isinstance(bars, list) or len(bars) != 3 or not isinstance(auras, list) or len(auras) != 2 or not isinstance(general, dict):
        return False
    if set(general) != {"opacity", "nameplate", "nameplateDm", "showNumbers", "maskColor", "maskOpacity"}:
        return False
    if not number_ok(general["opacity"]) or not number_ok(general["maskOpacity"]):
        return False
    if not all(isinstance(general[key], bool) for key in ("nameplate", "nameplateDm", "showNumbers")):
        return False
    if not color_ok(general["maskColor"]):
        return False
    bar_fields = {"current", "max", "component", "visibility", "location", "color"}
    components = {"none", "hp", "temp_hp", "weight", "armor_class", "initiative"}
    locations = {"above", "below", "top-overlap", "bottom-overlap"}
    for bar in bars:
        if not isinstance(bar, dict) or set(bar) != bar_fields:
            return False
        if not value_ok(bar["current"]) or not value_ok(bar["max"]):
            return False
        if (not isinstance(bar["component"], str) or bar["component"] not in components
                or not isinstance(bar["visibility"], str) or bar["visibility"] not in visibility
                or not isinstance(bar["location"], str) or bar["location"] not in locations
                or not color_ok(bar["color"])):
            return False
    aura_fields = {"radius", "shape", "visibility", "opacity", "color"}
    shapes = {"circle", "square", "hexagon", "circle-border", "square-border", "hexagon-border"}
    for aura in auras:
        if not isinstance(aura, dict) or set(aura) != aura_fields:
            return False
        if not value_ok(aura["radius"]) or not number_ok(aura["opacity"]):
            return False
        if (not isinstance(aura["shape"], str) or aura["shape"] not in shapes
                or not isinstance(aura["visibility"], str) or aura["visibility"] not in visibility
                or not color_ok(aura["color"])):
            return False
    return True


async def handle_asset_duplicate(db, data, room_code, user_id) -> bool:
    if not await _can_edit_placement(db, data, room_code, user_id):
        return await _reject(room_code, user_id, "You can't duplicate this token")
    placement = await duplicate_page_asset(
        db, room_code, user_id, data.page_id, data.asset_id,
        data.position_x, data.position_y, data.layer_order,
    )
    if not placement:
        return await _reject(room_code, user_id, "Can't duplicate the token")
    data.asset_id = placement.asset_id
    data.type = "asset.insert"
    data.asset_data = {
        "layer": placement.layer.value,
        "position_x": placement.position_x,
        "position_y": placement.position_y,
        "width": placement.width,
        "height": placement.height,
        "layer_order": placement.layer_order,
        "visible": placement.visible,
    }
    return True


async def handle_asset_change_visibility(db, data, room_code, user_id):
    if not await _can_edit_placement(db, data, room_code, user_id):
        return await _reject(room_code, user_id, "You can't change this token's visibility")
    return await _update(db, data, room_code, user_id,
        AssetUpdate(visible=data.visible), "Can't change the asset visibility")


async def handle_asset_change_size(db, data, room_code, user_id):
    if not await _can_edit_placement(db, data, room_code, user_id):
        return await _reject(room_code, user_id, "You can't resize assets on this layer")
    return await _update(db, data, room_code, user_id,
        AssetUpdate(height=data.height, width=data.width), "Can't change the asset size")
