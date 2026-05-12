from fastapi import WebSocket
from app.schemas.types import RoomCode


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[RoomCode, dict[int, WebSocket]] = {} # type: ignore

    async def connect(
        self,
        room_code: RoomCode,
        user_id: int,
        websocket: WebSocket
    ):
        if room_code not in self.active_connections:
            self.active_connections[room_code] = {}

        room = self.active_connections[room_code]

        connection_already_established = room.get(user_id)

        if connection_already_established is not None:
            await connection_already_established.close(
                code=4001,
                reason="Another session connected"
            )

        await websocket.accept()

        if room_code not in self.active_connections:
            self.active_connections[room_code] = {}

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
        message: dict
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

        for webscoket in room.values():
            await webscoket.send_json(message)


manager = ConnectionManager()
