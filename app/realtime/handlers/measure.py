from app.realtime.connection.manager import manager


async def handle_measure_update(db, data, room_code, user_id) -> bool:
    """Broadcast a transient measurement without persisting it."""
    await manager.broadcast(
        room_code,
        {
            "event": "measure.update",
            "user_id": user_id,
            "payload": data.model_dump(),
        },
    )
    return False
