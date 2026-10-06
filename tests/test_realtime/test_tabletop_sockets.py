from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from starlette.websockets import WebSocketDisconnect

from app.main import app
from app.realtime.connection.manager import manager
from app.services.auth_service import get_current_user_ws_id
from tests.helpers import USER_ID, make_user


ROOM_CODE = "ABC123"
NOW = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def ws_client(client):
    app.dependency_overrides[get_current_user_ws_id] = lambda: USER_ID
    manager.active_connections.clear()

    yield client

    manager.active_connections.clear()


@pytest.fixture(autouse=True)
def user_service():
    with (
        patch(
            "app.realtime.endpoints.tabletop.get_user",
            new_callable=AsyncMock
        ) as get_user,
        patch(
            "app.realtime.endpoints.tabletop.update_user",
            new_callable=AsyncMock
        ) as update_user,
    ):
        get_user.return_value = make_user(last_room_enter_at=NOW)
        yield SimpleNamespace(get_user=get_user, update_user=update_user)


@pytest.fixture
def frozen_now():
    """Congela datetime.now() dentro do endpoint do WebSocket."""
    with patch("app.realtime.endpoints.tabletop.datetime") as mock_datetime:
        mock_datetime.now.return_value = NOW
        yield mock_datetime


def connect(ws_client):
    return ws_client.websocket_connect(f"/ws/tabletop/{ROOM_CODE}")


def test_websocket_connect_broadcasts_player_join(
    ws_client,
    user_service,
    frozen_now
):
    with connect(ws_client) as websocket:
        assert websocket.receive_json() == {
            "event": "player.join",
            "user_id": USER_ID
        }

    first_update = user_service.update_user.await_args_list[0]
    assert first_update.args[1] == USER_ID
    assert first_update.kwargs["user_data"].last_room_enter_at == NOW


def test_websocket_chat_message_is_broadcast(ws_client):
    with connect(ws_client) as websocket:
        websocket.receive_json()

        websocket.send_json({
            "type": "chat.message",
            "message": "hello",
            "as_character": "Gandalf"
        })

        assert websocket.receive_json() == {
            "event": "message",
            "user_id": USER_ID,
            "payload": {
                "type": "chat.message",
                "as_character": "Gandalf",
                "message": "hello",
                "only_for_user_id": None
            }
        }


@patch("app.realtime.handlers.dice.roll_dices", return_value=[2, 5])
def test_websocket_dice_roll_is_broadcast_with_result(
    mock_roll_dices,
    ws_client
):
    with connect(ws_client) as websocket:
        websocket.receive_json()

        websocket.send_json({
            "type": "dice.roll",
            "quantity": 2,
            "sides": 6,
            "bonus": 1
        })

        response = websocket.receive_json()

    assert response["event"] == "message"
    assert response["payload"]["result"] == {"dices": [2, 5], "total": 8}
    mock_roll_dices.assert_called_once_with(2, 6)


@patch(
    "app.realtime.handlers.asset.update_asset",
    new_callable=AsyncMock,
    return_value=MagicMock()
)
def test_websocket_asset_move_is_broadcast(mock_update_asset, ws_client):
    with connect(ws_client) as websocket:
        websocket.receive_json()

        websocket.send_json({
            "type": "asset.move",
            "asset_id": 7,
            "x": "100",
            "y": "200"
        })

        response = websocket.receive_json()

    assert response["payload"] == {
        "type": "asset.move",
        "asset_id": 7,
        "x": "100",
        "y": "200"
    }
    mock_update_asset.assert_awaited_once()


@patch(
    "app.realtime.handlers.asset.update_asset",
    new_callable=AsyncMock,
    return_value=None
)
def test_websocket_asset_move_sends_error_when_asset_missing(
    mock_update_asset,
    ws_client
):
    with connect(ws_client) as websocket:
        websocket.receive_json()

        websocket.send_json({
            "type": "asset.move",
            "asset_id": 999,
            "x": "1",
            "y": "1"
        })

        assert websocket.receive_json() == {
            "event": "error",
            "payload": {"message": "Can't move the asset"}
        }


def test_websocket_unknown_message_type_returns_error(ws_client):
    with connect(ws_client) as websocket:
        websocket.receive_json()

        websocket.send_json({"type": "unknown.type"})

        assert websocket.receive_json() == {
            "event": "error",
            "payload": {"message": "Unknown message type"}
        }


def test_websocket_invalid_payload_returns_error(ws_client):
    with connect(ws_client) as websocket:
        websocket.receive_json()

        websocket.send_json({"type": "dice.roll"})

        assert websocket.receive_json() == {
            "event": "error",
            "payload": {"message": "Invalid payload"}
        }


def test_websocket_keeps_working_after_error(ws_client):
    with connect(ws_client) as websocket:
        websocket.receive_json()

        websocket.send_json({"type": "unknown.type"})
        websocket.receive_json()

        websocket.send_json({"type": "chat.message", "message": "still here"})

        assert websocket.receive_json()["payload"]["message"] == "still here"


def test_websocket_disconnect_updates_seconds_played(
    ws_client,
    user_service,
    frozen_now
):
    user_service.get_user.return_value = make_user(
        last_room_enter_at=NOW - timedelta(seconds=90),
        seconds_played=10
    )

    with connect(ws_client) as websocket:
        websocket.receive_json()

    user_service.get_user.assert_awaited_once()

    last_update = user_service.update_user.await_args_list[-1]
    assert last_update.kwargs["user_data"].seconds_played == 100

    assert ROOM_CODE not in manager.active_connections


def test_websocket_rejects_connection_without_valid_token(client):
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(f"/ws/tabletop/{ROOM_CODE}") as ws:
            ws.receive_json()
