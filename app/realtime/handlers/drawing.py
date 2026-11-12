from app.realtime.connection.manager import manager
from app.schemas.tabletop_schema import TabletopLayer
from app.services.tabletop_drawing_service import (
    create_page_drawing, delete_page_drawing, get_drawing_for_user, move_page_drawing,
)
from app.services.tabletop_page_service import is_room_master


async def _reject(room_code, user_id, message):
    await manager.send_to_user(room_code, user_id, {'event': 'error', 'payload': {'message': message}})
    return False


async def _editable(db, data, room_code, user_id):
    drawing = await get_drawing_for_user(db, room_code, user_id, data.page_id, data.drawing_id)
    if not drawing:
        return None
    if drawing.layer != TabletopLayer.players and not await is_room_master(db, room_code, user_id):
        return None
    return drawing


async def handle_drawing_create(db, data, room_code, user_id):
    master = await is_room_master(db, room_code, user_id)
    if not master and data.layer != TabletopLayer.players:
        return await _reject(room_code, user_id, "Players can only draw on their layer")
    values = data.model_dump(exclude={"type", "page_id", "client_id", "drawing_id"})
    values["points"] = [point.model_dump() for point in data.points]
    drawing = await create_page_drawing(db, room_code, user_id, data.page_id, values)
    if not drawing:
        return await _reject(room_code, user_id, "Can't draw on this page")
    data.drawing_id = drawing.id
    return True


async def handle_drawing_move(db, data, room_code, user_id):
    if not await _editable(db, data, room_code, user_id):
        return await _reject(room_code, user_id, "You can't move this drawing")
    drawing = await move_page_drawing(db, room_code, user_id, data.page_id, data.drawing_id, data.position_x, data.position_y)
    return bool(drawing) or await _reject(room_code, user_id, "Can't move this drawing")


async def handle_drawing_delete(db, data, room_code, user_id):
    if not await _editable(db, data, room_code, user_id):
        return await _reject(room_code, user_id, "You can't delete this drawing")
    deleted = await delete_page_drawing(db, room_code, user_id, data.page_id, data.drawing_id)
    return deleted or await _reject(room_code, user_id, "Can't delete this drawing")
