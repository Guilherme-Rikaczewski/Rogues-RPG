from app.realtime.connection.manager import manager


async def handle_chat_message(
    _,
    data,
    room_code,
    user_id,
    validator
) -> bool:

    if data.only_for_user_id is not None:
        await manager.send_to_user(
            room_code,
            data.only_for_user_id,
            message={
                'event': 'message',
                'user_id': user_id,
                'payload': data.model_dump()
            }
        )
        return False

    return True
