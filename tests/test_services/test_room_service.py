from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.exc import IntegrityError

from app.schemas.room_schema import RoomCreate, RoomUpdate
from app.services.room_service import (
    create_room,
    delete_room,
    get_all_rooms_from_user,
    get_recent_rooms_from_user,
    get_room,
    update_room,
    upload_room_thumb_image,
)


def make_room(**overrides):
    now = datetime.now(timezone.utc)
    data = {
        "id": 1,
        "room_name": "Sala Teste",
        "code": "ABC123",
        "thumb_image_url": "",
        "thumb_image_size": 0,
        "thumb_image_public_id": "",
        "created_at": now,
        "updated_at": now,
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def make_user(**overrides):
    data = {
        "id": 1,
        "storage_usage": 0,
        "profilepic_image_url": "",
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def make_scalar_result(value):
    result = MagicMock()
    result.scalar_one_or_none.return_value = value
    return result


def make_all_result(rows):
    result = MagicMock()
    result.all.return_value = rows
    return result


def make_db_with_scalar(value):
    db = MagicMock()
    db.execute = AsyncMock(return_value=make_scalar_result(value))
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.rollback = AsyncMock()
    db.delete = AsyncMock()
    return db


@pytest.mark.asyncio
@patch("app.services.room_service.generate_code", return_value="ABC123")
async def test_create_room_adds_generated_code_and_commits(mock_generate_code):
    db = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.rollback = AsyncMock()

    result = await create_room(db, RoomCreate(room_name="Sala Teste"))

    assert result.room_name == "Sala Teste"
    assert result.code == "ABC123"

    mock_generate_code.assert_called_once()
    db.add.assert_called_once_with(result)
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(result)
    db.rollback.assert_not_awaited()


@pytest.mark.asyncio
@patch(
    "app.services.room_service.generate_code",
    side_effect=["ABC123", "XYZ789"]
)
async def test_create_room_retries_when_generated_code_is_duplicated(
    mock_generate_code
):
    db = MagicMock()
    db.commit = AsyncMock(
        side_effect=[
            IntegrityError("duplicate", params=None, orig=None),
            None,
        ]
    )
    db.refresh = AsyncMock()
    db.rollback = AsyncMock()

    result = await create_room(db, RoomCreate(room_name="Sala Teste"))

    assert result.code == "XYZ789"

    assert mock_generate_code.call_count == 2
    assert db.add.call_count == 2
    assert db.commit.await_count == 2
    db.rollback.assert_awaited_once()
    db.refresh.assert_awaited_once_with(result)


@pytest.mark.asyncio
@patch("app.services.room_service.generate_code", return_value="ABC123")
async def test_create_room_rolls_back_and_reraises_on_commit_error(
    mock_generate_code
):
    db = MagicMock()
    db.commit = AsyncMock(side_effect=RuntimeError("commit failed"))
    db.refresh = AsyncMock()
    db.rollback = AsyncMock()

    with pytest.raises(RuntimeError, match="commit failed"):
        await create_room(db, RoomCreate(room_name="Sala Teste"))

    mock_generate_code.assert_called_once()
    db.rollback.assert_awaited_once()
    db.refresh.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_room_updates_stripped_fields_and_commits():
    room = make_room(room_name="Antiga")
    db = make_db_with_scalar(room)

    result = await update_room(
        db,
        1,
        RoomUpdate(room_name="  Nova Sala  ")
    )

    assert result is room
    assert room.room_name == "Nova Sala"

    db.execute.assert_awaited_once()
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(room)
    db.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_room_returns_none_when_room_does_not_exist():
    db = make_db_with_scalar(None)

    result = await update_room(db, 999, RoomUpdate(room_name="Nova Sala"))

    assert result is None

    db.execute.assert_awaited_once()
    db.commit.assert_not_awaited()
    db.refresh.assert_not_awaited()
    db.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_room_rolls_back_and_reraises_on_error():
    db = make_db_with_scalar(make_room())
    db.commit.side_effect = RuntimeError("commit failed")

    with pytest.raises(RuntimeError, match="commit failed"):
        await update_room(db, 1, RoomUpdate(room_name="Nova Sala"))

    db.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_room_returns_room():
    room = make_room()
    db = MagicMock()
    db.get = AsyncMock(return_value=room)

    result = await get_room(db, 1)

    assert result is room
    db.get.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_room_returns_none_when_missing():
    db = MagicMock()
    db.get = AsyncMock(return_value=None)

    result = await get_room(db, 999)

    assert result is None
    db.get.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_room_reraises_on_error():
    db = MagicMock()
    db.get = AsyncMock(side_effect=RuntimeError("db failed"))

    with pytest.raises(RuntimeError, match="db failed"):
        await get_room(db, 1)


@pytest.mark.asyncio
async def test_get_all_rooms_from_user_groups_member_profile_pictures():
    room = make_room(id=1, room_name="Sala A")
    other_room = make_room(id=2, room_name="Sala B", code="XYZ789")
    db = MagicMock()
    db.execute = AsyncMock(
        return_value=make_all_result(
            [
                (room, "master", "profile-1.png"),
                (room, "master", "profile-2.png"),
                (other_room, "player", "profile-3.png"),
            ]
        )
    )

    result = await get_all_rooms_from_user(db, 1)

    assert result == [
        {
            "id": 1,
            "room_name": "Sala A",
            "code": "ABC123",
            "role": "master",
            "thumb_image_url": "",
            "created_at": room.created_at,
            "updated_at": room.updated_at,
            "members_profilepics": ["profile-1.png", "profile-2.png"],
        },
        {
            "id": 2,
            "room_name": "Sala B",
            "code": "XYZ789",
            "role": "player",
            "thumb_image_url": "",
            "created_at": other_room.created_at,
            "updated_at": other_room.updated_at,
            "members_profilepics": ["profile-3.png"],
        },
    ]
    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_all_rooms_from_user_returns_empty_list_when_no_rows():
    db = MagicMock()
    db.execute = AsyncMock(return_value=make_all_result([]))

    result = await get_all_rooms_from_user(db, 1)

    assert result == []
    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_all_rooms_from_user_reraises_on_error():
    db = MagicMock()
    db.execute = AsyncMock(side_effect=RuntimeError("db failed"))

    with pytest.raises(RuntimeError, match="db failed"):
        await get_all_rooms_from_user(db, 1)


@pytest.mark.asyncio
async def test_get_recent_rooms_from_user_returns_room_dicts():
    room = make_room(room_name="Sala Recente")
    db = MagicMock()
    db.execute = AsyncMock(return_value=make_all_result([(room, "master")]))

    result = await get_recent_rooms_from_user(db, 1)

    assert result == [
        {
            "id": 1,
            "room_name": "Sala Recente",
            "code": "ABC123",
            "role": "master",
            "thumb_image_url": "",
            "created_at": room.created_at,
            "updated_at": room.updated_at,
        }
    ]
    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_recent_rooms_from_user_returns_none_when_no_rows():
    db = MagicMock()
    db.execute = AsyncMock(return_value=make_all_result([]))

    result = await get_recent_rooms_from_user(db, 1)

    assert result is None
    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_recent_rooms_from_user_reraises_on_error():
    db = MagicMock()
    db.execute = AsyncMock(side_effect=RuntimeError("db failed"))

    with pytest.raises(RuntimeError, match="db failed"):
        await get_recent_rooms_from_user(db, 1)


@pytest.mark.asyncio
async def test_delete_room_deletes_and_commits_when_room_exists():
    room = make_room()
    db = make_db_with_scalar(room)

    result = await delete_room(db, 1)

    assert result is True
    db.delete.assert_awaited_once_with(room)
    db.commit.assert_awaited_once()
    db.rollback.assert_not_awaited()


@pytest.mark.asyncio
@patch("app.services.room_service.delete_image")
async def test_delete_room_deletes_thumb_image_when_public_id_exists(
    mock_delete_image
):
    room = make_room(thumb_image_public_id="thumb-public-id")
    db = make_db_with_scalar(room)

    result = await delete_room(db, 1)

    assert result is True
    mock_delete_image.assert_called_once_with("thumb-public-id")
    db.delete.assert_awaited_once_with(room)
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_room_returns_false_when_room_does_not_exist():
    db = make_db_with_scalar(None)

    result = await delete_room(db, 999)

    assert result is False
    db.delete.assert_not_awaited()
    db.commit.assert_not_awaited()
    db.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_room_rolls_back_and_reraises_on_error():
    db = make_db_with_scalar(make_room())
    db.delete.side_effect = RuntimeError("delete failed")

    with pytest.raises(RuntimeError, match="delete failed"):
        await delete_room(db, 1)

    db.rollback.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.services.room_service.upload_image")
async def test_upload_room_thumb_image_updates_room_and_user_storage(
    mock_upload_image
):
    room = make_room(thumb_image_size=200)
    user = make_user(storage_usage=1000)
    db = MagicMock()
    db.execute = AsyncMock(
        side_effect=[
            make_scalar_result(user),
            make_scalar_result(room),
        ]
    )
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.rollback = AsyncMock()
    file = SimpleNamespace(file=MagicMock())
    mock_upload_image.return_value = {
        "url": "https://cdn.test/thumb.png",
        "size": 500,
        "public_id": "thumb-public-id",
    }

    result = await upload_room_thumb_image(db, 1, 10, file)

    assert result is room
    assert room.thumb_image_url == "https://cdn.test/thumb.png"
    assert room.thumb_image_size == 500
    assert room.thumb_image_public_id == "thumb-public-id"
    assert user.storage_usage == 1300

    mock_upload_image.assert_called_once_with(
        file.file,
        10,
        img_id="thumb_room_1",
        extra_folder="/rooms/1"
    )
    assert db.execute.await_count == 2
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(room)
    db.rollback.assert_not_awaited()


@pytest.mark.asyncio
@patch("app.services.room_service.upload_image")
async def test_upload_room_thumb_image_returns_none_when_room_is_missing(
    mock_upload_image
):
    db = MagicMock()
    db.execute = AsyncMock(
        side_effect=[
            make_scalar_result(make_user()),
            make_scalar_result(None),
        ]
    )
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.rollback = AsyncMock()
    file = SimpleNamespace(file=MagicMock())

    result = await upload_room_thumb_image(db, 999, 10, file)

    assert result is None
    mock_upload_image.assert_not_called()
    db.commit.assert_not_awaited()
    db.refresh.assert_not_awaited()
    db.rollback.assert_not_awaited()


@pytest.mark.asyncio
@patch("app.services.room_service.upload_image")
async def test_upload_room_thumb_image_returns_none_when_user_is_missing(
    mock_upload_image
):
    db = make_db_with_scalar(None)
    file = SimpleNamespace(file=MagicMock())

    result = await upload_room_thumb_image(db, 1, 999, file)

    assert result is None
    mock_upload_image.assert_not_called()
    db.commit.assert_not_awaited()
    db.refresh.assert_not_awaited()
    db.rollback.assert_not_awaited()


@pytest.mark.asyncio
@patch("app.services.room_service.delete_image")
@patch("app.services.room_service.upload_image")
async def test_upload_room_thumb_image_deletes_image_when_storage_exceeds_limit(
    mock_upload_image,
    mock_delete_image
):
    room = make_room(thumb_image_size=0)
    user = make_user(storage_usage=50 * 1024 * 1024)
    db = MagicMock()
    db.execute = AsyncMock(
        side_effect=[
            make_scalar_result(user),
            make_scalar_result(room),
        ]
    )
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.rollback = AsyncMock()
    file = SimpleNamespace(file=MagicMock())
    mock_upload_image.return_value = {
        "url": "https://cdn.test/thumb.png",
        "size": 1,
        "public_id": "new-thumb-public-id",
    }

    with pytest.raises(ValueError, match="storage limit"):
        await upload_room_thumb_image(db, 1, 10, file)

    mock_delete_image.assert_called_once_with("new-thumb-public-id")
    db.commit.assert_not_awaited()
    db.refresh.assert_not_awaited()
    db.rollback.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.services.room_service.upload_image")
async def test_upload_room_thumb_image_rolls_back_and_reraises_on_error(
    mock_upload_image
):
    db = MagicMock()
    db.execute = AsyncMock(
        side_effect=[
            make_scalar_result(make_user()),
            make_scalar_result(make_room()),
        ]
    )
    db.commit = AsyncMock(side_effect=RuntimeError("commit failed"))
    db.refresh = AsyncMock()
    db.rollback = AsyncMock()
    file = SimpleNamespace(file=MagicMock())
    mock_upload_image.return_value = {
        "url": "https://cdn.test/thumb.png",
        "size": 500,
        "public_id": "thumb-public-id",
    }

    with pytest.raises(RuntimeError, match="commit failed"):
        await upload_room_thumb_image(db, 1, 10, file)

    db.rollback.assert_awaited_once()
