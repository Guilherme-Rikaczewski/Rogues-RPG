from unittest.mock import patch

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.rooms import Room
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
from tests.helpers import (
    make_all_result,
    make_db,
    make_db_with_scalar,
    make_db_with_scalars,
    make_room,
    make_upload_file,
    make_user,
)


MAX_STORAGE = 50 * 1024 * 1024


# create_room

@patch("app.services.room_service.generate_code", return_value="ABC123")
async def test_create_room_adds_generated_code_and_commits(mock_generate_code):
    db = make_db()

    result = await create_room(db, RoomCreate(room_name="Sala Teste"))

    assert result.room_name == "Sala Teste"
    assert result.code == "ABC123"

    db.add.assert_called_once_with(result)
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(result)
    db.rollback.assert_not_awaited()


@patch(
    "app.services.room_service.generate_code",
    side_effect=["ABC123", "XYZ789"]
)
async def test_create_room_retries_when_generated_code_is_duplicated(
    mock_generate_code
):
    db = make_db()
    db.commit.side_effect = [
        IntegrityError("duplicate", params=None, orig=None),
        None,
    ]

    result = await create_room(db, RoomCreate(room_name="Sala Teste"))

    assert result.code == "XYZ789"
    assert mock_generate_code.call_count == 2
    assert db.commit.await_count == 2
    db.rollback.assert_awaited_once()
    db.refresh.assert_awaited_once_with(result)


@patch("app.services.room_service.generate_code", return_value="ABC123")
async def test_create_room_rolls_back_and_reraises_on_commit_error(
    mock_generate_code
):
    db = make_db()
    db.commit.side_effect = RuntimeError("commit failed")

    with pytest.raises(RuntimeError, match="commit failed"):
        await create_room(db, RoomCreate(room_name="Sala Teste"))

    db.rollback.assert_awaited_once()
    db.refresh.assert_not_awaited()


# update_room

async def test_update_room_updates_stripped_fields_and_commits():
    room = make_room(room_name="Antiga")
    db = make_db_with_scalar(room)

    result = await update_room(db, 1, RoomUpdate(room_name="  Nova Sala  "))

    assert result is room
    assert room.room_name == "Nova Sala"
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(room)
    db.rollback.assert_not_awaited()


async def test_update_room_returns_none_when_room_does_not_exist():
    db = make_db_with_scalar(None)

    result = await update_room(db, 999, RoomUpdate(room_name="Nova Sala"))

    assert result is None
    db.commit.assert_not_awaited()
    db.rollback.assert_not_awaited()


async def test_update_room_rolls_back_and_reraises_on_error():
    db = make_db_with_scalar(make_room())
    db.commit.side_effect = RuntimeError("commit failed")

    with pytest.raises(RuntimeError, match="commit failed"):
        await update_room(db, 1, RoomUpdate(room_name="Nova Sala"))

    db.rollback.assert_awaited_once()


# get_room

async def test_get_room_returns_room():
    room = make_room()
    db = make_db()
    db.get.return_value = room

    result = await get_room(db, 1)

    assert result is room
    db.get.assert_awaited_once_with(Room, 1)


async def test_get_room_returns_none_when_missing():
    db = make_db()
    db.get.return_value = None

    result = await get_room(db, 999)

    assert result is None
    db.get.assert_awaited_once_with(Room, 999)


async def test_get_room_reraises_on_error():
    db = make_db()
    db.get.side_effect = RuntimeError("db failed")

    with pytest.raises(RuntimeError, match="db failed"):
        await get_room(db, 1)


# get_all_rooms_from_user

async def test_get_all_rooms_from_user_groups_member_profile_pictures():
    room = make_room(id=1, room_name="Sala A")
    other_room = make_room(id=2, room_name="Sala B", code="XYZ789")
    db = make_db()
    db.execute.return_value = make_all_result([
        (room, "master", "profile-1.png"),
        (room, "master", "profile-2.png"),
        (other_room, "player", "profile-3.png"),
    ])

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


async def test_get_all_rooms_from_user_returns_empty_list_when_no_rows():
    db = make_db()
    db.execute.return_value = make_all_result([])

    assert await get_all_rooms_from_user(db, 1) == []


async def test_get_all_rooms_from_user_reraises_on_error():
    db = make_db()
    db.execute.side_effect = RuntimeError("db failed")

    with pytest.raises(RuntimeError, match="db failed"):
        await get_all_rooms_from_user(db, 1)


# get_recent_rooms_from_user

async def test_get_recent_rooms_from_user_returns_room_dicts():
    room = make_room(room_name="Sala Recente")
    db = make_db()
    db.execute.return_value = make_all_result([(room, "master")])

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


async def test_get_recent_rooms_from_user_returns_none_when_no_rows():
    db = make_db()
    db.execute.return_value = make_all_result([])

    assert await get_recent_rooms_from_user(db, 1) is None


async def test_get_recent_rooms_from_user_reraises_on_error():
    db = make_db()
    db.execute.side_effect = RuntimeError("db failed")

    with pytest.raises(RuntimeError, match="db failed"):
        await get_recent_rooms_from_user(db, 1)


# delete_room

@patch("app.services.room_service.delete_image")
async def test_delete_room_without_thumb_does_not_call_cloudinary(
    mock_delete_image
):
    room = make_room(thumb_image_public_id="")
    db = make_db_with_scalar(room)

    result = await delete_room(db, 1)

    assert result is True
    mock_delete_image.assert_not_called()
    db.delete.assert_awaited_once_with(room)
    db.commit.assert_awaited_once()
    db.rollback.assert_not_awaited()


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


async def test_delete_room_returns_false_when_room_does_not_exist():
    db = make_db_with_scalar(None)

    result = await delete_room(db, 999)

    assert result is False
    db.delete.assert_not_awaited()
    db.commit.assert_not_awaited()
    db.rollback.assert_not_awaited()


async def test_delete_room_rolls_back_and_reraises_on_error():
    db = make_db_with_scalar(make_room())
    db.delete.side_effect = RuntimeError("delete failed")

    with pytest.raises(RuntimeError, match="delete failed"):
        await delete_room(db, 1)

    db.rollback.assert_awaited_once()


# upload_room_thumb_image

@patch("app.services.room_service.upload_image")
async def test_upload_room_thumb_image_updates_room_and_user_storage(
    mock_upload_image
):
    room = make_room(thumb_image_size=200)
    user = make_user(storage_usage=1000)
    db = make_db_with_scalars(user, room)
    file = make_upload_file()
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
    # 1000 - 200 (thumb antiga) + 500 (thumb nova)
    assert user.storage_usage == 1300

    mock_upload_image.assert_called_once_with(
        file.file,
        10,
        img_id="thumb_room_1",
        extra_folder="/rooms/1"
    )
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(room)
    db.rollback.assert_not_awaited()


@patch("app.services.room_service.upload_image")
async def test_upload_room_thumb_image_returns_none_when_room_is_missing(
    mock_upload_image
):
    db = make_db_with_scalars(make_user(), None)

    result = await upload_room_thumb_image(db, 999, 10, make_upload_file())

    assert result is None
    mock_upload_image.assert_not_called()
    db.commit.assert_not_awaited()
    db.rollback.assert_not_awaited()


@patch("app.services.room_service.upload_image")
async def test_upload_room_thumb_image_returns_none_when_user_is_missing(
    mock_upload_image
):
    db = make_db_with_scalar(None)

    result = await upload_room_thumb_image(db, 1, 999, make_upload_file())

    assert result is None
    mock_upload_image.assert_not_called()
    db.commit.assert_not_awaited()
    db.rollback.assert_not_awaited()


@patch("app.services.room_service.delete_image")
@patch("app.services.room_service.upload_image")
async def test_upload_room_thumb_image_deletes_image_when_storage_exceeds_limit(
    mock_upload_image,
    mock_delete_image
):
    room = make_room(thumb_image_size=0)
    user = make_user(storage_usage=MAX_STORAGE)
    db = make_db_with_scalars(user, room)
    mock_upload_image.return_value = {
        "url": "https://cdn.test/thumb.png",
        "size": 1,
        "public_id": "new-thumb-public-id",
    }

    with pytest.raises(ValueError, match="storage limit"):
        await upload_room_thumb_image(db, 1, 10, make_upload_file())

    mock_delete_image.assert_called_once_with("new-thumb-public-id")
    assert user.storage_usage == MAX_STORAGE
    db.commit.assert_not_awaited()
    db.rollback.assert_awaited_once()


@patch("app.services.room_service.upload_image")
async def test_upload_room_thumb_image_rolls_back_and_reraises_on_error(
    mock_upload_image
):
    db = make_db_with_scalars(make_user(), make_room())
    db.commit.side_effect = RuntimeError("commit failed")
    mock_upload_image.return_value = {
        "url": "https://cdn.test/thumb.png",
        "size": 500,
        "public_id": "thumb-public-id",
    }

    with pytest.raises(RuntimeError, match="commit failed"):
        await upload_room_thumb_image(db, 1, 10, make_upload_file())

    db.rollback.assert_awaited_once()
