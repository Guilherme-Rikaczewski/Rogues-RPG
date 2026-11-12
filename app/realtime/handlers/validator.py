from app.schemas.tabletop_schema import (
    AssetMoveMessage,
    MeasureUpdateMessage,
    TextCreateMessage,
    TextUpdateMessage,
    TextMoveMessage,
    TextDeleteMessage,
    DrawingCreateMessage,
    DrawingMoveMessage,
    DrawingDeleteMessage,
    AssetChangeLayerMessage,
    AssetChangeOrderMessage,
    AssetRemoveFromTabletopMessage,
    AssetInsertMessage,
    DiceRollMessage,
    ChatMessage,
    AssetChangeVisibilityMessage,
    ChangeBackgroundSettingsMessage,
    AssetChangeSizeMessage,
    PageCreateMessage,
    FolderCreateMessage,
    PageRenameMessage,
    FolderRenameMessage,
    PageMoveMessage,
    PageSetActiveMessage,
    WebSocketMessage
)
from pydantic import ValidationError


MESSAGE_TYPES = {
    "asset.move": AssetMoveMessage,
    "measure.update": MeasureUpdateMessage,
    "text.create": TextCreateMessage,
    "text.update": TextUpdateMessage,
    "text.move": TextMoveMessage,
    "text.delete": TextDeleteMessage,
    "drawing.create": DrawingCreateMessage,
    "drawing.move": DrawingMoveMessage,
    "drawing.delete": DrawingDeleteMessage,
    "asset.change_layer": AssetChangeLayerMessage,
    "asset.change_order": AssetChangeOrderMessage,
    "asset.remove_from_tabletop": AssetRemoveFromTabletopMessage,
    "asset.change_visibility": AssetChangeVisibilityMessage,
    "asset.change_size": AssetChangeSizeMessage,
    "asset.insert": AssetInsertMessage,
    "dice.roll": DiceRollMessage,
    "chat.message": ChatMessage,
    "background.change_settings": ChangeBackgroundSettingsMessage,
    "page.create": PageCreateMessage,
    "folder.create": FolderCreateMessage,
    "page.rename": PageRenameMessage,
    "folder.rename": FolderRenameMessage,
    "page.move": PageMoveMessage,
    "page.set_active": PageSetActiveMessage,
}


def validate(
    data
) -> WebSocketMessage | None:
    data_type = data.get("type")
    schema: WebSocketMessage = MESSAGE_TYPES.get(data_type)  # type: ignore

    try:
        validated_data = schema.model_validate(data)
        return validated_data
    except ValidationError:
        return None
