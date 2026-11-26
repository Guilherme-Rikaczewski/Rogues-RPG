from pydantic import BaseModel, Field
from datetime import datetime
from app.schemas.types import RoomName, RoomCode, Username
from app.schemas.note_schema import NoteResponse, NoteFolderResponse
from app.schemas.tabletop_schema import (
    TabletopAssetResponse,
    TabletopFolderResponse,
    TabletopPageResponse,
    TabletopSettingsResponse,
    TabletopTextResponse,
    TabletopDrawingResponse,
    TabletopMaskResponse,
)
import enum


class RoomRole(str, enum.Enum):
    master = "master"
    player = "player"


class RoomGameSystem(str, enum.Enum):
    DND5e = "D&D5e"
    T20 = "T20"


class RoomCreate(BaseModel):
    room_name: RoomName
    game_system: RoomGameSystem = RoomGameSystem.DND5e
    thumb_image_url: str = ''
    thumb_image_size: int = 0
    thumb_image_public_id: str = ''


class RoomUpdate(BaseModel):
    room_name: RoomName


class RoomResponse(BaseModel):
    id: int
    public_id: str
    room_name: RoomName
    game_system: RoomGameSystem
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
    note_folders: list[NoteFolderResponse] = Field(default_factory=list)
    assets: list[TabletopAssetResponse] = Field(
        default_factory=list
    )
    texts: list[TabletopTextResponse] = Field(default_factory=list)
    drawings: list[TabletopDrawingResponse] = Field(default_factory=list)
    masks: list[TabletopMaskResponse] = Field(default_factory=list)
    dm_darkness_opacity: int = 45
    settings: TabletopSettingsResponse = Field(
        default_factory=TabletopSettingsResponse
    )
    pages: list[TabletopPageResponse] = Field(default_factory=list)
    folders: list[TabletopFolderResponse] = Field(default_factory=list)
    page_id: int | None = None
    active_page_id: int | None = None

    model_config = {'from_attributes': True}
