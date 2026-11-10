from app.schemas.tabletop_schema import (
    AssetMoveMessage,
    AssetChangeLayerMessage,
    AssetChangeOrderMessage,
    AssetRemoveFromTabletopMessage,
    AssetInsertMessage,
    DiceRollMessage,
    ChatMessage,
    AssetChangeVisibilityMessage,
    ChangeBackgroundSettingsMessage,
    AssetChangeSizeMessage,
    WebSocketMessage
)
from pydantic import ValidationError


MESSAGE_TYPES = {
    "asset.move": AssetMoveMessage,
    "asset.change_layer": AssetChangeLayerMessage,
    "asset.change_order": AssetChangeOrderMessage,
    "asset.remove_from_tabletop": AssetRemoveFromTabletopMessage,
    "asset.change_visibility": AssetChangeVisibilityMessage,
    "asset.change_size": AssetChangeSizeMessage,
    "asset.insert": AssetInsertMessage,
    "dice.roll": DiceRollMessage,
    "chat.message": ChatMessage,
    "background.change_settings": ChangeBackgroundSettingsMessage,
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
