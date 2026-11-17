from app.realtime.connection.manager import manager
from app.services.tabletop_mask_service import (
    create_page_mask, delete_page_mask, update_page_mask_opacity,
)
from app.services.tabletop_page_service import is_room_master


async def _reject(room_code, user_id, message):
    await manager.send_to_user(room_code, user_id, {'event': 'error', 'payload': {'message': message}})
    return False


async def handle_mask_create(db, data, room_code, user_id):
    if not await is_room_master(db, room_code, user_id):
        return await _reject(room_code, user_id, "Only the room master can draw masks")
    required_points = {"rectangle": 2, "circle": 2, "polygon": 3, "full_page": 0}[data.shape]
    if len(data.points) != required_points and not (data.shape == "polygon" and len(data.points) >= required_points):
        return await _reject(room_code, user_id, "Mask geometry is incomplete")
    points = [point.model_dump() for point in data.points]
    mask = await create_page_mask(db, room_code, user_id, data.page_id, data.operation, data.shape, points)
    if not mask:
        return await _reject(room_code, user_id, "Can't create a mask on this page")
    data.mask_id = mask.id
    return True


async def handle_mask_delete(db, data, room_code, user_id):
    if not await is_room_master(db, room_code, user_id):
        return await _reject(room_code, user_id, "Only the room master can remove masks")
    deleted = await delete_page_mask(db, room_code, user_id, data.page_id, data.mask_id)
    return deleted or await _reject(room_code, user_id, "Can't remove this mask")


async def handle_mask_opacity(db, data, room_code, user_id):
    if not await is_room_master(db, room_code, user_id):
        return await _reject(room_code, user_id, "Only the room master can change mask opacity")
    updated = await update_page_mask_opacity(db, room_code, user_id, data.page_id, data.opacity)
    return bool(updated) or await _reject(room_code, user_id, "Can't update mask opacity")
