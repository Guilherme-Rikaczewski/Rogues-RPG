from app.realtime.connection.manager import manager
from app.services.tabletop_page_service import (
    create_folder, create_page, move_page, rename_folder, rename_page,
    set_players_page,
)


async def _emit(room_code: str, user_id: int, event: str, payload: dict) -> bool:
    await manager.broadcast(room_code, {'event': event, 'user_id': user_id, 'payload': payload})
    return False  # these events already contain their canonical DB response


async def handle_page_create(db, data, room_code, user_id):
    page = await create_page(db, room_code, user_id)
    if not page:
        await manager.send_to_user(room_code, user_id, {'event': 'error', 'payload': {'message': 'Only the room master can create pages'}})
        return False
    return await _emit(room_code, user_id, 'page.created', {
        'id': page.id, 'room_id': page.room_id, 'folder_id': page.folder_id,
        'name': page.name, 'display_order': page.display_order,
        'is_players_page': page.is_players_page,
    })


async def handle_folder_create(db, data, room_code, user_id):
    folder = await create_folder(db, room_code, user_id)
    if not folder:
        await manager.send_to_user(room_code, user_id, {'event': 'error', 'payload': {'message': 'Only the room master can create folders'}})
        return False
    return await _emit(room_code, user_id, 'folder.created', {
        'id': folder.id, 'room_id': folder.room_id, 'name': folder.name,
        'display_order': folder.display_order,
    })


async def handle_page_rename(db, data, room_code, user_id):
    page = await rename_page(db, room_code, user_id, data.page_id, data.name)
    if not page:
        await manager.send_to_user(room_code, user_id, {'event': 'error', 'payload': {'message': 'Unable to rename page'}})
        return False
    return await _emit(room_code, user_id, 'page.updated', {
        'id': page.id, 'folder_id': page.folder_id, 'name': page.name,
        'display_order': page.display_order, 'is_players_page': page.is_players_page,
    })


async def handle_folder_rename(db, data, room_code, user_id):
    folder = await rename_folder(db, room_code, user_id, data.folder_id, data.name)
    if not folder:
        await manager.send_to_user(room_code, user_id, {'event': 'error', 'payload': {'message': 'Unable to rename folder'}})
        return False
    return await _emit(room_code, user_id, 'folder.updated', {
        'id': folder.id, 'name': folder.name, 'display_order': folder.display_order,
    })


async def handle_page_move(db, data, room_code, user_id):
    page = await move_page(db, room_code, user_id, data.page_id, data.folder_id)
    if not page:
        await manager.send_to_user(room_code, user_id, {'event': 'error', 'payload': {'message': 'Unable to move page'}})
        return False
    return await _emit(room_code, user_id, 'page.updated', {
        'id': page.id, 'folder_id': page.folder_id, 'name': page.name,
        'display_order': page.display_order, 'is_players_page': page.is_players_page,
    })


async def handle_page_set_active(db, data, room_code, user_id):
    page = await set_players_page(db, room_code, user_id, data.page_id)
    if not page:
        await manager.send_to_user(room_code, user_id, {'event': 'error', 'payload': {'message': 'Unable to publish page'}})
        return False
    return await _emit(room_code, user_id, 'page.published', {'page_id': page.id})
