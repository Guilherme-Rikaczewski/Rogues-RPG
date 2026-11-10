from app.realtime.connection.manager import manager
from app.services.tabletop_service import (
    update_asset
)
from app.schemas.tabletop_schema import (
    AssetUpdate,
)


async def handle_change_background_settings(
    db,
    data,
    room_code,
    user_id,
) -> bool:

    # guardar informações no banco

    return True
