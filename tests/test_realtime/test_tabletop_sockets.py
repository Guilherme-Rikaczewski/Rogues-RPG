from unittest.mock import patch, AsyncMock

from fastapi.testclient import TestClient

from app.main import app
from app.services.auth_service import get_current_user_ws_id


client = TestClient(app)


def override_get_current_user_ws_id():
    return 1


app.dependency_overrides[get_current_user_ws_id] = (
    override_get_current_user_ws_id
)


@patch(
    "app.realtime.endpoints.tabletop.manager.broadcast",
    new_callable=AsyncMock
)
def test_websocket_message(mock_broadcast):

    room_code = "ABC123"

    with client.websocket_connect(
        f"/ws/tabletop/{room_code}"
    ) as websocket:

        websocket.send_json({
            "message": "hello"
        })

    assert mock_broadcast.call_count >= 2
