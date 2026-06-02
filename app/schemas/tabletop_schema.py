from pydantic import BaseModel
from typing import Union, Literal
import enum


class AssetMoveMessage(BaseModel):
    type: Literal["asset.move"]

    asset_id: int
    x: str
    y: str


class DiceRollMessage(BaseModel):
    type: Literal["dice.roll"]

    quantity: int = 1
    sides: int
    bonus: int = 0
    result: dict = {
        'dices': [],
        'total': 0
    }
    only_for_user_id: int | None = None


class ChatMessage(BaseModel):
    type: Literal["chat.message"]

    as_character: str | None = None
    message: str
    only_for_user_id: int | None = None


WebSocketMessage = Union[
    AssetMoveMessage,
    DiceRollMessage,
    ChatMessage
]


class TabletopLayer(str, enum.Enum):
    master = "master"
    players = "players"
    map = "map"


class AssetCreate(BaseModel):
    asset_image_url: str = ''
    asset_image_public_id: str = ''
    asset_image_file_name: str = ''
    layer: TabletopLayer
    room_id: int
    user_id: int


class AssetUpdate(BaseModel):
    position_x: str | None = None
    position_y: str | None = None


class TabletopAssetResponse(BaseModel):
    id: int
    asset_image_url: str = ''
    asset_image_public_id: str = ''
    asset_image_file_name: str = ''
    position_x: str | None
    position_y: str | None
    layer: TabletopLayer

    model_config = {'from_attributes': True}
