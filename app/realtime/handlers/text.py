from app.realtime.connection.manager import manager
from app.schemas.tabletop_schema import TabletopLayer
from app.services.tabletop_page_service import is_room_master
from app.services.tabletop_text_service import (
    create_page_text, delete_page_text, get_text_for_user, update_page_text,
)


async def _reject(room_code, user_id, message):
    await manager.send_to_user(room_code, user_id, {'event': 'error', 'payload': {'message': message}})
    return False


async def _editable(db, data, room_code, user_id):
    text = await get_text_for_user(db, room_code, user_id, data.page_id, data.text_id)
    if not text:
        return None
    if text.layer != TabletopLayer.players and not await is_room_master(db, room_code, user_id):
        return None
    return text


async def handle_text_create(db, data, room_code, user_id):
    master = await is_room_master(db, room_code, user_id)
    if not master and data.layer != TabletopLayer.players:
        return await _reject(room_code, user_id, "Players can only create text on their layer")
    values = data.model_dump(exclude={"type", "page_id", "client_id", "text_id", "x", "y"})
    values.update(position_x=data.x, position_y=data.y)
    text = await create_page_text(db, room_code, user_id, data.page_id, values)
    if not text:
        return await _reject(room_code, user_id, "Can't create text on this page")
    data.text_id = text.id
    return True


async def handle_text_update(db, data, room_code, user_id):
    if not await _editable(db, data, room_code, user_id):
        return await _reject(room_code, user_id, "You can't edit this text")
    values = data.model_dump(exclude={"type", "page_id", "text_id"}, exclude_unset=True, exclude_none=True)
    updated = await update_page_text(db, room_code, user_id, data.page_id, data.text_id, values)
    return bool(updated) or await _reject(room_code, user_id, "Can't update this text")


async def handle_text_move(db, data, room_code, user_id):
    if not await _editable(db, data, room_code, user_id):
        return await _reject(room_code, user_id, "You can't move this text")
    moved = await update_page_text(db, room_code, user_id, data.page_id, data.text_id,
                                   {"position_x": data.x, "position_y": data.y})
    return bool(moved) or await _reject(room_code, user_id, "Can't move this text")


async def handle_text_delete(db, data, room_code, user_id):
    if not await _editable(db, data, room_code, user_id):
        return await _reject(room_code, user_id, "You can't delete this text")
    deleted = await delete_page_text(db, room_code, user_id, data.page_id, data.text_id)
    return deleted or await _reject(room_code, user_id, "Can't delete this text")
