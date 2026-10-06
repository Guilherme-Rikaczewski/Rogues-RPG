import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.realtime.handlers.asset import (
    handle_asset_change_layer,
    handle_asset_insert,
    handle_asset_move,
)
from app.realtime.handlers.chat import handle_chat_message
from app.realtime.handlers.dice import handle_dice_roll
from app.realtime.handlers.validator import validate
from app.schemas.tabletop_schema import (
    AssetChangeLayerMessage,
    AssetInsertMessage,
    AssetMoveMessage,
    AssetUpdate,
    ChatMessage,
    DiceRollMessage,
    TabletopLayer,
)


ROOM_CODE = "ABC123"
USER_ID = 1


# validator

@pytest.mark.parametrize(
    "data, expected_type",
    [
        (
            {"type": "asset.move", "asset_id": 1, "x": "10", "y": "20"},
            AssetMoveMessage,
        ),
        (
            {"type": "asset.change_layer", "asset_id": 1, "layer": "map"},
            AssetChangeLayerMessage,
        ),
        (
            {
                "type": "asset.insert",
                "asset_id": 1,
                "asset_data": {"position_x": "1", "position_y": "2"},
            },
            AssetInsertMessage,
        ),
        (
            {"type": "dice.roll", "sides": 20},
            DiceRollMessage,
        ),
        (
            {"type": "chat.message", "message": "hello"},
            ChatMessage,
        ),
    ],
)
def test_validate_returns_matching_schema(data, expected_type):
    result = validate(data)

    assert isinstance(result, expected_type)


@pytest.mark.parametrize(
    "data",
    [
        {"type": "asset.move", "asset_id": 1, "x": "10"},
        {"type": "asset.change_layer", "asset_id": 1, "layer": "invalid"},
        {"type": "asset.insert", "asset_id": 1},
        {"type": "dice.roll"},
        {"type": "chat.message"},
        {"type": "dice.roll", "sides": "not a number"},
    ],
)
def test_validate_returns_none_for_invalid_payload(data):
    assert validate(data) is None


def test_validate_applies_dice_roll_defaults():
    result = validate({"type": "dice.roll", "sides": 6})

    assert result.quantity == 1
    assert result.bonus == 0
    assert result.only_for_user_id is None


# asset handlers

@patch("app.realtime.handlers.asset.manager.send_to_user", new_callable=AsyncMock)
@patch("app.realtime.handlers.asset.update_asset", new_callable=AsyncMock)
async def test_handle_asset_move_updates_position_and_broadcasts(
    mock_update_asset,
    mock_send_to_user
):
    db = MagicMock()
    data = AssetMoveMessage(type="asset.move", asset_id=7, x="10", y="20")
    mock_update_asset.return_value = MagicMock()

    should_broadcast = await handle_asset_move(db, data, ROOM_CODE, USER_ID)

    assert should_broadcast is True
    mock_update_asset.assert_awaited_once_with(
        db,
        7,
        AssetUpdate(position_x="10", position_y="20")
    )
    mock_send_to_user.assert_not_awaited()


@patch("app.realtime.handlers.asset.manager.send_to_user", new_callable=AsyncMock)
@patch("app.realtime.handlers.asset.update_asset", new_callable=AsyncMock)
async def test_handle_asset_move_sends_error_when_asset_not_found(
    mock_update_asset,
    mock_send_to_user
):
    data = AssetMoveMessage(type="asset.move", asset_id=999, x="1", y="1")
    mock_update_asset.return_value = None

    should_broadcast = await handle_asset_move(
        MagicMock(), data, ROOM_CODE, USER_ID
    )

    assert should_broadcast is False
    mock_send_to_user.assert_awaited_once_with(
        ROOM_CODE,
        USER_ID,
        {"event": "error", "payload": {"message": "Can't move the asset"}}
    )


@patch("app.realtime.handlers.asset.manager.send_to_user", new_callable=AsyncMock)
@patch("app.realtime.handlers.asset.update_asset", new_callable=AsyncMock)
async def test_handle_asset_change_layer_updates_layer_and_broadcasts(
    mock_update_asset,
    mock_send_to_user
):
    db = MagicMock()
    data = AssetChangeLayerMessage(
        type="asset.change_layer", asset_id=7, layer=TabletopLayer.master
    )
    mock_update_asset.return_value = MagicMock()

    should_broadcast = await handle_asset_change_layer(
        db, data, ROOM_CODE, USER_ID
    )

    assert should_broadcast is True
    mock_update_asset.assert_awaited_once_with(
        db,
        7,
        AssetUpdate(layer=TabletopLayer.master)
    )
    mock_send_to_user.assert_not_awaited()


@patch("app.realtime.handlers.asset.manager.send_to_user", new_callable=AsyncMock)
@patch("app.realtime.handlers.asset.update_asset", new_callable=AsyncMock)
async def test_handle_asset_change_layer_sends_error_when_asset_not_found(
    mock_update_asset,
    mock_send_to_user
):
    data = AssetChangeLayerMessage(
        type="asset.change_layer", asset_id=999, layer=TabletopLayer.map
    )
    mock_update_asset.return_value = None

    should_broadcast = await handle_asset_change_layer(
        MagicMock(), data, ROOM_CODE, USER_ID
    )

    assert should_broadcast is False
    mock_send_to_user.assert_awaited_once_with(
        ROOM_CODE,
        USER_ID,
        {
            "event": "error",
            "payload": {"message": "Can't change the asset layer"}
        }
    )


@patch("app.realtime.handlers.asset.manager.send_to_user", new_callable=AsyncMock)
@patch("app.realtime.handlers.asset.update_asset", new_callable=AsyncMock)
async def test_handle_asset_insert_updates_asset_data_and_broadcasts(
    mock_update_asset,
    mock_send_to_user
):
    db = MagicMock()
    asset_data = AssetUpdate(
        position_x="5", position_y="6", layer=TabletopLayer.players
    )
    data = AssetInsertMessage(
        type="asset.insert", asset_id=7, asset_data=asset_data
    )
    mock_update_asset.return_value = MagicMock()

    should_broadcast = await handle_asset_insert(db, data, ROOM_CODE, USER_ID)

    assert should_broadcast is True
    mock_update_asset.assert_awaited_once_with(
        db,
        7,
        asset_data=asset_data
    )
    mock_send_to_user.assert_not_awaited()


@patch("app.realtime.handlers.asset.manager.send_to_user", new_callable=AsyncMock)
@patch("app.realtime.handlers.asset.update_asset", new_callable=AsyncMock)
async def test_handle_asset_insert_sends_error_when_asset_not_found(
    mock_update_asset,
    mock_send_to_user
):
    data = AssetInsertMessage(
        type="asset.insert", asset_id=999, asset_data=AssetUpdate()
    )
    mock_update_asset.return_value = None

    should_broadcast = await handle_asset_insert(
        MagicMock(), data, ROOM_CODE, USER_ID
    )

    assert should_broadcast is False
    mock_send_to_user.assert_awaited_once()


# chat handler

@patch("app.realtime.handlers.chat.manager.send_to_user", new_callable=AsyncMock)
async def test_handle_chat_message_public_message_is_broadcast(
    mock_send_to_user
):
    data = ChatMessage(type="chat.message", message="hello")

    should_broadcast = await handle_chat_message(
        None, data, ROOM_CODE, USER_ID
    )

    assert should_broadcast is True
    mock_send_to_user.assert_not_awaited()


@patch("app.realtime.handlers.chat.manager.send_to_user", new_callable=AsyncMock)
async def test_handle_chat_message_private_message_goes_only_to_target(
    mock_send_to_user
):
    data = ChatMessage(
        type="chat.message", message="secret", only_for_user_id=2
    )

    should_broadcast = await handle_chat_message(
        None, data, ROOM_CODE, USER_ID
    )

    assert should_broadcast is False
    mock_send_to_user.assert_awaited_once()
    args, kwargs = mock_send_to_user.call_args
    assert args == (ROOM_CODE, 2)
    assert kwargs["message"]["event"] == "message"
    assert kwargs["message"]["user_id"] == USER_ID


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Bug: handle_chat_message envia o model Pydantic sem model_dump(), "
        "e send_json não consegue serializar a mensagem privada"
    ),
)
@patch("app.realtime.handlers.chat.manager.send_to_user", new_callable=AsyncMock)
async def test_handle_chat_message_private_message_is_json_serializable(
    mock_send_to_user
):
    data = ChatMessage(
        type="chat.message", message="secret", only_for_user_id=2
    )

    await handle_chat_message(None, data, ROOM_CODE, USER_ID)

    json.dumps(mock_send_to_user.call_args.kwargs["message"])


# dice handler

@patch("app.realtime.handlers.dice.manager.send_to_user", new_callable=AsyncMock)
@patch("app.realtime.handlers.dice.roll_dices")
async def test_handle_dice_roll_fills_result_and_broadcasts(
    mock_roll_dices,
    mock_send_to_user
):
    mock_roll_dices.return_value = [3, 4]
    data = DiceRollMessage(type="dice.roll", quantity=2, sides=6, bonus=5)

    should_broadcast = await handle_dice_roll(None, data, ROOM_CODE, USER_ID)

    assert should_broadcast is True
    assert data.result == {"dices": [3, 4], "total": 12}
    mock_roll_dices.assert_called_once_with(2, 6)
    mock_send_to_user.assert_not_awaited()


@patch("app.realtime.handlers.dice.manager.send_to_user", new_callable=AsyncMock)
@patch("app.realtime.handlers.dice.roll_dices")
async def test_handle_dice_roll_handles_negative_bonus(
    mock_roll_dices,
    mock_send_to_user
):
    mock_roll_dices.return_value = [1]
    data = DiceRollMessage(type="dice.roll", sides=20, bonus=-3)

    await handle_dice_roll(None, data, ROOM_CODE, USER_ID)

    assert data.result == {"dices": [1], "total": -2}


@patch("app.realtime.handlers.dice.manager.send_to_user", new_callable=AsyncMock)
@patch("app.realtime.handlers.dice.roll_dices")
async def test_handle_dice_roll_private_roll_goes_only_to_target(
    mock_roll_dices,
    mock_send_to_user
):
    mock_roll_dices.return_value = [20]
    data = DiceRollMessage(type="dice.roll", sides=20, only_for_user_id=2)

    should_broadcast = await handle_dice_roll(None, data, ROOM_CODE, USER_ID)

    assert should_broadcast is False
    assert data.result == {"dices": [20], "total": 20}
    mock_send_to_user.assert_awaited_once()
    args, kwargs = mock_send_to_user.call_args
    assert args == (ROOM_CODE, 2)
    assert kwargs["message"]["user_id"] == USER_ID


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Bug: handle_dice_roll envia o model Pydantic sem model_dump(), "
        "e send_json não consegue serializar a rolagem privada"
    ),
)
@patch("app.realtime.handlers.dice.manager.send_to_user", new_callable=AsyncMock)
@patch("app.realtime.handlers.dice.roll_dices")
async def test_handle_dice_roll_private_roll_is_json_serializable(
    mock_roll_dices,
    mock_send_to_user
):
    mock_roll_dices.return_value = [20]
    data = DiceRollMessage(type="dice.roll", sides=20, only_for_user_id=2)

    await handle_dice_roll(None, data, ROOM_CODE, USER_ID)

    json.dumps(mock_send_to_user.call_args.kwargs["message"])
