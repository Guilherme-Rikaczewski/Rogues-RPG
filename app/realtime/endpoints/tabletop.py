from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
    Depends
)
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.room_schema import RoomCode
from app.realtime.connection.manager import manager
from app.services.auth_service import (
    get_current_user_ws_id
)
from app.services.tabletop_service import (
    update_asset, roll_dices
)
from app.services.user_service import (
    update_user, get_user
)
from app.schemas.user_schema import (
    UserUpdate
)
from app.schemas.tabletop_schema import (
    AssetUpdate,
    AssetMoveMessage,
    AssetChangeLayerMessage,
    DiceRollMessage,
    ChatMessage,
    WebSocketMessage
)
from app.db.session import get_db
import traceback
from datetime import datetime, timezone, timedelta

router = APIRouter(
    prefix="/ws",
    tags=["websocket"]
)

MESSAGE_TYPES = {
    "asset.move": AssetMoveMessage,
    "asset.change_layer": AssetChangeLayerMessage,
    "dice.roll": DiceRollMessage,
    "chat.message": ChatMessage,
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
            schema: WebSocketMessage = MESSAGE_TYPES.get(data_type) # type: ignore

            if not schema:
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

            try:
                data = schema.model_validate(data)
            except ValidationError as error:
                await manager.send_to_user(
                    room_code,
                    user_id,
                    {
                        'event': 'error',
                        'payload': {
                            'message': "Invalid payload",
                            'errors': error.errors()
                        }
                    }
                )
                continue

            if isinstance(data, AssetMoveMessage):
                updated_asset = await update_asset(
                    db,
                    data.asset_id,
                    AssetUpdate(
                        position_x=data.x,
                        position_y=data.y
                    )
                )

                if not updated_asset:
                    await manager.send_to_user(
                        room_code,
                        user_id,
                        {
                            'event': 'error',
                            'payload': {
                                'message': (
                                    "Can't move the asset"
                                )
                            }
                        }
                    )
                    continue
            elif isinstance(data, AssetChangeLayerMessage):
                updated_asset = await update_asset(
                    db,
                    data.asset_id,
                    AssetUpdate(
                        layer=data.layer
                    )
                )

                if not updated_asset:
                    await manager.send_to_user(
                        room_code,
                        user_id,
                        {
                            'event': 'error',
                            'payload': {
                                'message': (
                                    "Can't change the asset layer"
                                )
                            }
                        }
                    )
                    continue
            elif isinstance(data, DiceRollMessage):
                dices_result = roll_dices(data.quantity, data.sides)

                total = sum(dices_result) + data.bonus

                data.result["dices"] = dices_result
                data.result["total"] = total

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
                    continue
            elif isinstance(data, ChatMessage):
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
