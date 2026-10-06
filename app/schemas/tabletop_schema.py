from pydantic import BaseModel
from typing import Union, Literal
import enum


class TabletopLayer(str, enum.Enum):
    master = "master"
    players = "players"
    map = "map"


class AssetCreate(BaseModel):
    asset_image_url: str = ''
    asset_image_public_id: str = ''
    asset_image_file_name: str = ''
    layer: TabletopLayer | None = None
    room_id: int | None = None
    sheet_id: int | None = None
    user_id: int


class AssetUpdate(BaseModel):
    position_x: str | None = None
    position_y: str | None = None
    layer: TabletopLayer | None = None
    visible: bool | None = None


class TabletopAssetResponse(BaseModel):
    id: int
    asset_image_url: str = ''
    asset_image_public_id: str = ''
    asset_image_file_name: str = ''
    position_x: str | None
    position_y: str | None
    layer: TabletopLayer | None
    visible: bool | None

    model_config = {'from_attributes': True}


class AssetMoveMessage(BaseModel):
    type: Literal["asset.move"]

    asset_id: int
    x: str
    y: str

    model_config = {'from_attributes': True}


class AssetChangeLayerMessage(BaseModel):
    type: Literal["asset.change_layer"]

    asset_id: int
    layer: TabletopLayer

    model_config = {'from_attributes': True}


class AssetInsertMessage(BaseModel):
    type: Literal["asset.insert"]

    asset_id: int
    asset_data: AssetUpdate

    model_config = {'from_attributes': True}


class DiceRollMessage(BaseModel):
    type: Literal["dice.roll"]

    quantity: int = 1
    sides: int
    bonus: int = 0
    result: dict | None = {
        'dices': [],
        'total': 0
    }
    only_for_user_id: int | None = None

    model_config = {'from_attributes': True}


class ChatMessage(BaseModel):
    type: Literal["chat.message"]

    as_character: str | None = None
    message: str
    only_for_user_id: int | None = None

    model_config = {'from_attributes': True}


WebSocketMessage = Union[
    AssetMoveMessage,
    AssetChangeLayerMessage,
    DiceRollMessage,
    ChatMessage,
]
