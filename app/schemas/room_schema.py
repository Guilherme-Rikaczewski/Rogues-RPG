from pydantic import BaseModel
from datetime import datetime
from app.schemas.types import RoomName, RoomCode


class RoomCreate(BaseModel):
    room_name: RoomName


class RoomUpdate(BaseModel):
    room_name: RoomName


class RoomResponse(BaseModel):
    id: int
    room_name: RoomName
    code: RoomCode
    created_at: datetime
    updated_at: datetime

    model_config = {'from_attributes': True}
