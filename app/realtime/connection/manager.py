from fastapi import WebSocket
from app.schemas.types import RoomCode
from app.schemas.tabletop_schema import WebSocketMessage
import traceback

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[RoomCode, dict[int, WebSocket]] = {} # type: ignore

    async def connect(
        self,
        room_code: RoomCode,
        user_id: int,
        websocket: WebSocket
    ):
        room = self.active_connections.setdefault(
            room_code, {}
        )
        # if room_code not in self.active_connections:
        #     self.active_connections[room_code] = {}

        # room = self.active_connections[room_code]

        old_connection = room.get(user_id)

        if old_connection is not None:
            await old_connection.close(
                code=4001,
                reason="Another session connected"
            )

        await websocket.accept()

        # if room_code not in self.active_connections:
        #     self.active_connections[room_code] = {}

        room[user_id] = websocket

    def disconnect(
        self,
        room_code: RoomCode,
        user_id: int,
        active_websocket: bool
    ):
        room = self.active_connections.get(room_code)

        if not room:
            return

        if active_websocket:
            room.pop(user_id, None)

        if not room:
            self.active_connections.pop(room_code, None)

    async def send_to_user(
        self,
        room_code: RoomCode,
        user_id: int,
        message: WebSocketMessage | dict
    ):
        room = self.active_connections.get(room_code)

        if not room:
            return

        websocket = room.get(user_id)

        if websocket:
            await websocket.send_json(message)

    async def broadcast(
        self,
        room_code: RoomCode,
        message: dict
    ):
        room = self.active_connections.get(room_code)

        if not room:
            return

        disconnected_users = []
        for user_id, webscoket in room.items():
            try:
                await webscoket.send_json(message)
            except Exception:
                disconnected_users.append(user_id)
                traceback.print_exc()

        for user_id in disconnected_users:
            self.disconnect(
                room_code,
                user_id,
                active_websocket=True
            )


manager = ConnectionManager()
