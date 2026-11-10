from app.realtime.connection.manager import manager
from app.services.tabletop_service import (
    update_asset,
    remove_asset_from_tabletop,
)
from app.schemas.tabletop_schema import (
    AssetUpdate,
)


async def handle_asset_move(
    db,
    data,
    room_code,
    user_id,
) -> bool:

    updated_asset = await update_asset(
        db,
        data.asset_id,
        AssetUpdate(
            position_x=data.x,
            position_y=data.y
        )
    )

    if not updated_asset:
        await manager.send_to_user(
            room_code,
            user_id,
            {
                'event': 'error',
                'payload': {
                    'message': (
                        "Can't move the asset"
                    )
                }
            }
        )
        return False

    return True


async def handle_asset_change_layer(
    db,
    data,
    room_code,
    user_id,
) -> bool:

    updated_asset = await update_asset(
        db,
        data.asset_id,
        AssetUpdate(
            layer=data.layer
        )
    )

    if not updated_asset:
        await manager.send_to_user(
            room_code,
            user_id,
            {
                'event': 'error',
                'payload': {
                    'message': (
                        "Can't change the asset layer"
                    )
                }
            }
        )
        return False

    return True


async def handle_asset_change_order(
    db,
    data,
    room_code,
    user_id,
) -> bool:
    updated_asset = await update_asset(
        db,
        data.asset_id,
        AssetUpdate(
            layer=data.layer,
            layer_order=data.layer_order,
        )
    )

    if not updated_asset:
        await manager.send_to_user(
            room_code,
            user_id,
            {'event': 'error', 'payload': {'message': "Can't change the asset order"}}
        )
        return False

    return True


async def handle_asset_remove_from_tabletop(
    db,
    data,
    room_code,
    user_id,
) -> bool:
    removed = await remove_asset_from_tabletop(db, data.asset_id)
    if not removed:
        await manager.send_to_user(
            room_code,
            user_id,
            {'event': 'error', 'payload': {'message': "Can't remove the asset from tabletop"}}
        )
        return False

    return True


async def handle_asset_insert(
    db,
    data,
    room_code,
    user_id,
) -> bool:

    updated_asset = await update_asset(
        db,
        data.asset_id,
        asset_data=data.asset_data
    )

    if not updated_asset:
        await manager.send_to_user(
            room_code,
            user_id,
            {
                'event': 'error',
                'payload': {
                    'message': (
                        "Can't insert the asset"
                    )
                }
            }
        )
        return False

    return True


async def handle_asset_change_visibility(
    db,
    data,
    room_code,
    user_id,
):

    updated_asset = await update_asset(
        db,
        data.asset_id,
        AssetUpdate(
            visible=data.visible
        )
    )

    if not updated_asset:
        await manager.send_to_user(
            room_code,
            user_id,
            {
                'event': 'error',
                'payload': {
                    'message': (
                        "Can't change the asset visibility"
                    )
                }
            }
        )
        return False

    return True


async def handle_asset_change_size(
    db,
    data,
    room_code,
    user_id,
):

    updated_asset = await update_asset(
        db,
        data.asset_id,
        AssetUpdate(
            height=data.height,
            width=data.width
        )
    )

    if not updated_asset:
        await manager.send_to_user(
            room_code,
            user_id,
            {
                'event': 'error',
                'payload': {
                    'message': (
                        "Can't change the asset size"
                    )
                }
            }
        )
        return False

    return True
