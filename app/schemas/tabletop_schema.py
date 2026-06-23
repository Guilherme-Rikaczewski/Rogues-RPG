from pydantic import BaseModel
from typing import Union, Literal
import enum


class TabletopLayer(str, enum.Enum):
    master = "master"
    players = "players"
    map = "map"


class AssetMoveMessage(BaseModel):
    type: Literal["asset.move"]

    asset_id: int
    x: str
    y: str


class AssetChangeLayerMessage(BaseModel):
    type: Literal["asset.change_layer"]

    asset_id: int
    layer: TabletopLayer


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
    AssetChangeLayerMessage,
    DiceRollMessage,
    ChatMessage,
]


class AssetCreate(BaseModel):
    asset_image_url: str = ''
    asset_image_public_id: str = ''
    asset_image_file_name: str = ''
    layer: TabletopLayer | None = None
    room_id: int
    user_id: int


class AssetUpdate(BaseModel):
    position_x: str | None = None
    position_y: str | None = None
    layer: TabletopLayer | None = None


class TabletopAssetResponse(BaseModel):
    id: int
    asset_image_url: str = ''
    asset_image_public_id: str = ''
    asset_image_file_name: str = ''
    position_x: str | None
    position_y: str | None
    layer: TabletopLayer | None

    model_config = {'from_attributes': True}
