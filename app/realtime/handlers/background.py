from app.realtime.connection.manager import manager
from app.services.tabletop_settings_service import (
    update_room_tabletop_settings
)


async def handle_change_background_settings(
    db,
    data,
    room_code,
    user_id,
) -> bool:

    settings = await update_room_tabletop_settings(
        db,
        room_code,
        user_id,
        data.model_dump(exclude_unset=True, exclude_none=True),
        page_id=data.page_id,
    )

    if not settings:
        await manager.send_to_user(
            room_code,
            user_id,
            {
                'event': 'error',
                'payload': {
                    'message': "Can't update tabletop settings"
                }
            }
        )
        return False

    return True
