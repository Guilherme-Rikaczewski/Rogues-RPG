from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app
from app.services.auth_service import get_current_user_ws_id


client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


async def override_get_db():
    yield MagicMock()


async def override_get_current_user_ws_id():
    return 1


@patch("app.realtime.endpoints.tabletop.get_user", new_callable=AsyncMock)
@patch("app.realtime.endpoints.tabletop.update_user", new_callable=AsyncMock)
@patch(
    "app.realtime.endpoints.tabletop.manager.broadcast",
    new_callable=AsyncMock
)
def test_websocket_chat_message(
    mock_broadcast,
    mock_update_user,
    mock_get_user
):
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_ws_id] = (
        override_get_current_user_ws_id
    )

    room_code = "ABC123"
    mock_get_user.return_value = SimpleNamespace(
        last_room_enter_at=datetime.now(timezone.utc),
        seconds_played=0
    )

    with client.websocket_connect(
        f"/ws/tabletop/{room_code}"
    ) as websocket:

        websocket.send_json({
            "type": "chat.message",
            "message": "hello"
        })

    assert mock_broadcast.await_count >= 2

    mock_update_user.assert_awaited()
    mock_get_user.assert_awaited_once()
