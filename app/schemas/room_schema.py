from pydantic import BaseModel, Field
from datetime import datetime
from app.schemas.types import RoomName, RoomCode, Username
from app.schemas.note_schema import NoteResponse
from app.schemas.tabletop_schema import TabletopAssetResponse
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


class UserInRoom(BaseModel):
    id: int
    username: Username
    profilepic_image_url: str
    role: RoomRole


class UsersRoomResponse(BaseModel):
    room_id: int
    room_name: RoomName
    thumb_image_url: str
    code: RoomCode
    role: RoomRole
    users: list[UserInRoom] = Field(
        default_factory=list
    )

    created_at: datetime
    updated_at: datetime

    model_config = {'from_attributes': True}


class TabletopRoomResponse(BaseModel):
    notes: list[NoteResponse] = Field(
        default_factory=list
    )
    assets: list[TabletopAssetResponse] = Field(
        default_factory=list
    )

    model_config = {'from_attributes': True}
