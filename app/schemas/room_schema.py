from pydantic import BaseModel
from datetime import datetime
from app.schemas.types import RoomName, RoomCode
import enum


class RoomRole(str, enum.Enum):
    master = "master"
    player = "player"


class RoomCreate(BaseModel):
    room_name: RoomName
    thumb_image_url: str = ''
    thumb_image_size: int = 0
    thumb_image_public_id: str = ''


class RoomUpdate(BaseModel):
    room_name: RoomName


class RoomResponse(BaseModel):
    id: int
    room_name: RoomName
    code: RoomCode
    role: RoomRole
    thumb_image_url: str
    created_at: datetime
    updated_at: datetime

    model_config = {'from_attributes': True}
