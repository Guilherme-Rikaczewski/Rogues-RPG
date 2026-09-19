from app.schemas.tabletop_schema import (
    AssetMoveMessage,
    AssetChangeLayerMessage,
    AssetInsertMessage,
    DiceRollMessage,
    ChatMessage,
    WebSocketMessage
)
from pydantic import ValidationError


MESSAGE_TYPES = {
    "asset.move": AssetMoveMessage,
    "asset.change_layer": AssetChangeLayerMessage,
    "asset.insert": AssetInsertMessage,
    "dice.roll": DiceRollMessage,
    "chat.message": ChatMessage,
}


def validate(
    data
) -> WebSocketMessage | None:
    data_type = data.get("type")
    schema: WebSocketMessage = MESSAGE_TYPES.get(data_type) # type: ignore

    try:
        validated_data = schema.model_validate(data)
        return validated_data
    except ValidationError:
        return None
