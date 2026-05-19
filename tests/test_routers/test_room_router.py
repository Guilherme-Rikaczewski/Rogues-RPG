from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.services.auth_service import get_current_user_id


client = TestClient(app)


def override_get_current_user_id():
    return 1


app.dependency_overrides[get_current_user_id] = override_get_current_user_id


@patch("app.routers.room_router.rus.create_room_user")
@patch("app.routers.room_router.rs.create_room")
def test_create_room(
    mock_create_room,
    mock_create_room_user
):
    fake_room = MagicMock()
    fake_room.id = 10
    fake_room.room_name = "Sala Teste"
    fake_room.code = "ABC123"
    fake_room.thumb_image_url = "image.png"

    fake_room_user = MagicMock()
    fake_room_user.role = "master"

    mock_create_room.return_value = fake_room
    mock_create_room_user.return_value = fake_room_user

    response = client.post(
        "/rooms/",
        json={
            "room_name": "Sala Teste"
        }
    )

    assert response.status_code == 200

    assert response.json()["room_name"] == "Sala Teste"

    assert response.json()["role"] == "master"

    mock_create_room.assert_called_once()

    mock_create_room_user.assert_called_once()


@patch("app.routers.room_router.rs.get_room")
@patch("app.routers.room_router.rus.join_room_by_code")
def test_join_room(
    mock_join_room_by_code,
    mock_get_room
):
    fake_room_user = MagicMock()
    fake_room_user.room_id = 10
    fake_room_user.role = "player"

    fake_room = MagicMock()
    fake_room.id = 10
    fake_room.room_name = "Sala RPG"
    fake_room.code = "ABC123"
    fake_room.thumb_image_url = "thumb.png"

    mock_join_room_by_code.return_value = fake_room_user
    mock_get_room.return_value = fake_room

    response = client.post("/rooms/join/ABC123")

    assert response.status_code == 200

    assert response.json()["room_name"] == "Sala RPG"

    assert response.json()["role"] == "player"

    mock_join_room_by_code.assert_called_once()

    mock_get_room.assert_called_once()
