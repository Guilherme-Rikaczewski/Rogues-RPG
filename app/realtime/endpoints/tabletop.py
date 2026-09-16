from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
    Depends
)
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.room_schema import RoomCode
from app.realtime.connection.manager import manager
from app.services.auth_service import (
    get_current_user_ws_id
)
from app.services.user_service import (
    update_user, get_user
)
from app.schemas.user_schema import (
    UserUpdate
)
from app.realtime.handlers.asset import (
    handle_asset_change_layer,
    handle_asset_move
)
from app.realtime.handlers.chat import (
    handle_chat_message
)
from app.realtime.handlers.dice import (
    handle_dice_roll
)
from app.realtime.handlers.validator import validate
from app.db.session import get_db
import traceback
from datetime import datetime, timezone, timedelta
from typing import Callable


router = APIRouter(
    prefix="/ws",
    tags=["websocket"]
)

MESSAGE_HANDLERS = {
    "asset.move": handle_asset_move,
    "asset.change_layer": handle_asset_change_layer,
    "chat.message": handle_chat_message,
    "dice.roll": handle_dice_roll,
}


@router.websocket("/tabletop/{room_code}")
async def tabletop_socket(
    websocket: WebSocket,
    room_code: RoomCode,
    user_id: int = Depends(get_current_user_ws_id),
    db: AsyncSession = Depends(get_db),
):
    await manager.connect(
        room_code=room_code,
        user_id=user_id,
        websocket=websocket
    )

    try:
        await update_user(
            db,
            user_id,
            user_data=UserUpdate(
                last_room_enter_at=datetime.now(timezone.utc)
            )
        )

        await manager.broadcast(
            room_code,
            {
                'event': 'player.join',
                'user_id': user_id
            }
        )

        while True:
            data = await websocket.receive_json()
            data_type = data.get("type")
            handler: Callable | None = MESSAGE_HANDLERS.get(
                data_type  # type: ignore
            )

            if not handler:
                await manager.send_to_user(
                    room_code,
                    user_id,
                    {
                        'event': 'error',
                        'payload': {
                            'message': (
                                "Unknown message type"
                            )
                        }
                    }
                )
                continue

            should_send_broadcast = await handler(
                db,
                data,
                room_code,
                user_id,
                validate
            )

            if not should_send_broadcast:
                continue

            await manager.broadcast(
                room_code,
                {
                    'event': 'message',
                    'user_id': user_id,
                    'payload': data.model_dump()
                }
            )

    except WebSocketDisconnect as error:
        active_socket = True

        if error.reason == "Another session connected":
            active_socket = False

        if active_socket:
            manager.disconnect(
                room_code=room_code,
                user_id=user_id,
                active_websocket=active_socket
            )

            user = await get_user(db, user_id)
            if user:
                disconnect_datetime = datetime.now(timezone.utc)
                time_connected: timedelta = (
                    disconnect_datetime - user.last_room_enter_at  # type: ignore
                )
                seconds_connected = int(time_connected.total_seconds())
                new_seconds_played = int(
                    user.seconds_played + seconds_connected
                )
                await update_user(
                    db,
                    user_id,
                    user_data=UserUpdate(
                        seconds_played=new_seconds_played
                    )
                )

            await manager.broadcast(
                room_code,
                {
                    'event': 'player.leave',
                    'user_id': user_id
                }
            )

    except Exception:
        manager.disconnect(
            room_code=room_code,
            user_id=user_id,
            active_websocket=True
        )

        traceback.print_exc()

        try:
            await websocket.close(
                code=1011,
                reason="Internal server error"
            )
        except Exception:
            pass
