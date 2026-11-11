from pydantic import BaseModel, Field
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
    height: str | None = None
    width: str | None = None
    layer_order: int | None = None


class TabletopAssetResponse(BaseModel):
    id: int
    asset_image_url: str = ''
    asset_image_public_id: str = ''
    asset_image_file_name: str = ''
    position_x: str | None
    position_y: str | None
    layer: TabletopLayer | None
    visible: bool | None
    height: str | None = None
    width: str | None = None
    layer_order: int = 0

    model_config = {'from_attributes': True}


class TabletopSettingsResponse(BaseModel):
    visible_grid: bool = True
    movement_adaptable_to_grid: bool = False
    grid_color: str = "#000000"
    grid_opacity: int = 50
    background_color: str = "#949494"
    page_size_x: int = 1920
    page_size_y: int = 1080
    map_scale_value: float = 0
    map_scale_unity: str = "meters"

    model_config = {'from_attributes': True}


class TabletopPageResponse(BaseModel):
    id: int
    room_id: int
    folder_id: int | None = None
    name: str
    display_order: int = 0
    is_players_page: bool = False
    preview_image_url: str | None = None

    model_config = {'from_attributes': True}


class TabletopFolderResponse(BaseModel):
    id: int
    room_id: int
    name: str
    display_order: int = 0

    model_config = {'from_attributes': True}


class AssetMoveMessage(BaseModel):
    type: Literal["asset.move"]

    asset_id: int
    page_id: int | None = None
    x: str
    y: str

    model_config = {'from_attributes': True}


class AssetChangeLayerMessage(BaseModel):
    type: Literal["asset.change_layer"]

    asset_id: int
    page_id: int | None = None
    layer: TabletopLayer

    model_config = {'from_attributes': True}


class AssetChangeOrderMessage(BaseModel):
    type: Literal["asset.change_order"]

    asset_id: int
    page_id: int | None = None
    layer: TabletopLayer
    layer_order: int

    model_config = {'from_attributes': True}


class AssetRemoveFromTabletopMessage(BaseModel):
    type: Literal["asset.remove_from_tabletop"]

    asset_id: int
    page_id: int | None = None

    model_config = {'from_attributes': True}


class AssetInsertMessage(BaseModel):
    type: Literal["asset.insert"]

    asset_id: int
    page_id: int
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


class AssetChangeVisibilityMessage(BaseModel):
    type: Literal["asset.change_visibility"]

    asset_id: int
    page_id: int | None = None
    visible: bool

    model_config = {'from_attributes': True}


class ChangeBackgroundSettingsMessage(BaseModel):
    type: Literal["background.change_settings"]

    visible_grid: bool | None = None
    background_color: str | None = None
    grid_color: str | None = None
    grid_opacity: int | None = Field(default=None, ge=0, le=100)
    page_size_x: int | None = None
    page_size_y: int | None = None
    map_scale_value: float | None = None
    map_scale_unity: str | None = None
    movement_adaptable_to_grid: bool | None = None
    page_id: int | None = None

    model_config = {'from_attributes': True}


class AssetChangeSizeMessage(BaseModel):
    type: Literal["asset.change_size"]

    asset_id: int
    page_id: int | None = None
    height: str | None = None
    width: str | None = None

    model_config = {'from_attributes': True}


class PageCreateMessage(BaseModel):
    type: Literal["page.create"]


class FolderCreateMessage(BaseModel):
    type: Literal["folder.create"]


class PageRenameMessage(BaseModel):
    type: Literal["page.rename"]
    page_id: int
    name: str


class FolderRenameMessage(BaseModel):
    type: Literal["folder.rename"]
    folder_id: int
    name: str


class PageMoveMessage(BaseModel):
    type: Literal["page.move"]
    page_id: int
    folder_id: int | None = None


class PageSetActiveMessage(BaseModel):
    type: Literal["page.set_active"]
    page_id: int


WebSocketMessage = Union[
    AssetMoveMessage,
    AssetChangeLayerMessage,
    AssetChangeOrderMessage,
    AssetRemoveFromTabletopMessage,
    AssetInsertMessage,
    AssetChangeVisibilityMessage,
    ChangeBackgroundSettingsMessage,
    AssetChangeSizeMessage,
    DiceRollMessage,
    ChatMessage,
    PageCreateMessage,
    FolderCreateMessage,
    PageRenameMessage,
    FolderRenameMessage,
    PageMoveMessage,
    PageSetActiveMessage,
]
