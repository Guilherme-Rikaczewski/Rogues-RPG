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
    validator
) -> bool:

    validated_data = validator(data)

    if not validated_data:
        await manager.send_to_user(
            room_code,
            user_id,
            {
                'event': 'error',
                'payload': {
                    'message': "Invalid payload"
                }
            }
        )
        return False

    updated_asset = await update_asset(
        db,
        validated_data.asset_id,
        AssetUpdate(
            position_x=validated_data.x,
            position_y=validated_data.y
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
    validator
) -> bool:

    validated_data = validator(data)

    if not validated_data:
        await manager.send_to_user(
            room_code,
            user_id,
            {
                'event': 'error',
                'payload': {
                    'message': "Invalid payload"
                }
            }
        )
        return False

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
