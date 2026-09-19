from app.realtime.connection.manager import manager
from app.services.tabletop_service import (
    update_asset
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
                        "Can't change the asset layer"
                    )
                }
            }
        )
        return False

    return True
