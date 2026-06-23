from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app
from app.services.auth_service import get_current_user_id


client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


async def override_get_db():
    yield MagicMock()


async def override_get_current_user_id():
    return 1


def make_room(**overrides):
    now = datetime.now(timezone.utc)
    data = {
        "id": 10,
        "room_name": "Sala Teste",
        "code": "ABC123",
        "thumb_image_url": "",
        "created_at": now,
        "updated_at": now,
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def make_room_user(**overrides):
    data = {
        "room_id": 10,
        "role": "master",
    }
    data.update(overrides)
    return SimpleNamespace(**data)


@patch("app.routers.room_router.rus.create_room_user", new_callable=AsyncMock)
@patch("app.routers.room_router.rs.create_room", new_callable=AsyncMock)
def test_create_room(
    mock_create_room,
    mock_create_room_user
):
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_id] = (
        override_get_current_user_id
    )

    fake_room = make_room()
    fake_room_user = make_room_user()
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

    mock_create_room.assert_awaited_once()

    mock_create_room_user.assert_awaited_once()


@patch("app.routers.room_router.rs.get_room", new_callable=AsyncMock)
@patch("app.routers.room_router.rus.join_room_by_code", new_callable=AsyncMock)
def test_join_room(
    mock_join_room_by_code,
    mock_get_room
):
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_id] = (
        override_get_current_user_id
    )

    fake_room_user = make_room_user(role="player")
    fake_room = make_room(
        room_name="Sala RPG",
        thumb_image_url="thumb.png"
    )
    mock_join_room_by_code.return_value = fake_room_user
    mock_get_room.return_value = fake_room

    response = client.post("/rooms/join/ABC123")

    assert response.status_code == 200

    assert response.json()["room_name"] == "Sala RPG"

    assert response.json()["role"] == "player"

    mock_join_room_by_code.assert_awaited_once()

    mock_get_room.assert_awaited_once()
