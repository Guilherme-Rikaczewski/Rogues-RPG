from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.schemas.room_schema import RoomCode
from app.realtime.connection.manager import manager
from app.services.auth_service import get_current_user_ws_id

router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/tabletop/{room_code}")
async def tabletop_socket(
    websocket: WebSocket, room_code: RoomCode,
    user_id=Depends(get_current_user_ws_id),
):
    await manager.connect(
        room_code=room_code,
        user_id=user_id,
        websocket=websocket
    )

    try:
        await manager.broadcast(
            room_code,
            {
                'event': 'player.join',
                'user_id': user_id
            }
        )

        while True:
            data = await websocket.receive_json()

            await manager.broadcast(
                room_code,
                {
                    'event': 'message',
                    'user_id': user_id,
                    'payload': data
                }
            )
    except WebSocketDisconnect as error:
        active_socket = True

        if error.reason == "Another session connected":
            active_socket = False

        manager.disconnect(
            room_code=room_code,
            user_id=user_id,
            active_websocket=active_socket
        )

        if active_socket:
            await manager.broadcast(
                room_code,
                {
                    'event': 'player.leave',
                    'user_id': user_id
                }
            )
