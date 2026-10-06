from unittest.mock import patch

import pytest

from app.models.users import User
from app.schemas.user_schema import UserCreate, UserUpdate
from app.services.user_service import (
    create_user,
    delete_user,
    get_user,
    update_user,
    upload_profile_pic_image,
)
from tests.helpers import (
    make_db,
    make_db_with_scalar,
    make_upload_file,
    make_user,
)


MAX_STORAGE = 50 * 1024 * 1024


# create_user

@patch("app.services.user_service.get_password_hash")
async def test_create_user_stores_hashed_password_and_commits(mock_hash):
    mock_hash.return_value = "hashed_password"
    db = make_db()

    result = await create_user(
        db,
        UserCreate(
            username="guilherme",
            email="gui@email.com",
            password="aB123456"
        )
    )

    assert result.username == "guilherme"
    assert result.email == "gui@email.com"
    assert result.password == "hashed_password"
    assert result.password != "aB123456"

    mock_hash.assert_called_once_with("aB123456")
    db.add.assert_called_once_with(result)
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(result)


# update_user

@patch("app.services.user_service.get_password_hash")
async def test_update_user_updates_fields_and_hashes_new_password(mock_hash):
    mock_hash.return_value = "new_password_hash"
    user = make_user(username="gui")
    db = make_db_with_scalar(user)

    result = await update_user(
        db,
        1,
        UserUpdate(username="guilherme", password="bA123456")
    )

    assert result is user
    assert user.username == "guilherme"
    assert user.password == "new_password_hash"

    mock_hash.assert_called_once_with("bA123456")
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(user)


async def test_update_user_returns_none_when_user_does_not_exist():
    db = make_db_with_scalar(None)

    result = await update_user(db, 999, UserUpdate(username="guilherme"))

    assert result is None
    db.commit.assert_not_awaited()
    db.rollback.assert_not_awaited()


@patch("app.services.user_service.get_password_hash")
async def test_update_user_strips_strings_and_does_not_hash_absent_password(
    mock_hash
):
    user = make_user(username="gui", password="old_hash")
    db = make_db_with_scalar(user)

    result = await update_user(db, 1, UserUpdate(username="  guilherme  "))

    assert result is user
    assert user.username == "guilherme"
    assert user.password == "old_hash"

    mock_hash.assert_not_called()
    db.commit.assert_awaited_once()


async def test_update_user_rolls_back_and_reraises_on_error():
    db = make_db_with_scalar(make_user())
    db.commit.side_effect = RuntimeError("commit failed")

    with pytest.raises(RuntimeError, match="commit failed"):
        await update_user(db, 1, UserUpdate(username="guilherme"))

    db.rollback.assert_awaited_once()


# upload_profile_pic_image

@patch("app.services.user_service.upload_image")
async def test_upload_profile_pic_image_updates_user_storage(mock_upload):
    user = make_user(storage_usage=1000, profilepic_image_size=200)
    db = make_db_with_scalar(user)
    file = make_upload_file()
    mock_upload.return_value = {
        "url": "https://cdn.test/profile.png",
        "size": 500,
        "public_id": "profilepic_user_1",
    }

    result = await upload_profile_pic_image(db, 1, file)

    assert result is user
    assert user.profilepic_image_url == "https://cdn.test/profile.png"
    assert user.profilepic_image_size == 500
    assert user.profilepic_image_public_id == "profilepic_user_1"
    # 1000 - 200 (foto antiga) + 500 (foto nova)
    assert user.storage_usage == 1300

    mock_upload.assert_called_once_with(
        file.file,
        1,
        img_id="profilepic_user_1",
        max_width=512,
        max_height=512
    )
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(user)
    db.rollback.assert_not_awaited()


@patch("app.services.user_service.upload_image")
async def test_upload_profile_pic_image_returns_none_when_user_is_missing(
    mock_upload
):
    db = make_db_with_scalar(None)

    result = await upload_profile_pic_image(db, 999, make_upload_file())

    assert result is None
    mock_upload.assert_not_called()
    db.commit.assert_not_awaited()
    db.rollback.assert_not_awaited()


@patch("app.services.user_service.delete_image")
@patch("app.services.user_service.upload_image")
async def test_upload_profile_pic_image_deletes_image_when_storage_exceeds_limit(
    mock_upload,
    mock_delete
):
    user = make_user(storage_usage=MAX_STORAGE, profilepic_image_size=0)
    db = make_db_with_scalar(user)
    mock_upload.return_value = {
        "url": "https://cdn.test/profile.png",
        "size": 1,
        "public_id": "new_public_id",
    }

    with pytest.raises(ValueError, match="storage limit"):
        await upload_profile_pic_image(db, 1, make_upload_file())

    mock_delete.assert_called_once_with("new_public_id")
    assert user.storage_usage == MAX_STORAGE
    db.commit.assert_not_awaited()
    db.rollback.assert_awaited_once()


@patch("app.services.user_service.upload_image")
async def test_upload_profile_pic_image_rolls_back_and_reraises_on_error(
    mock_upload
):
    db = make_db_with_scalar(make_user())
    db.commit.side_effect = RuntimeError("commit failed")
    mock_upload.return_value = {
        "url": "https://cdn.test/profile.png",
        "size": 500,
        "public_id": "profilepic_user_1",
    }

    with pytest.raises(RuntimeError, match="commit failed"):
        await upload_profile_pic_image(db, 1, make_upload_file())

    db.rollback.assert_awaited_once()


# get_user

async def test_get_user_returns_user_when_found():
    user = make_user()
    db = make_db()
    db.get.return_value = user

    result = await get_user(db, 1)

    assert result is user
    db.get.assert_awaited_once_with(User, 1)


async def test_get_user_returns_none_when_missing():
    db = make_db()
    db.get.return_value = None

    result = await get_user(db, 999)

    assert result is None
    db.get.assert_awaited_once_with(User, 999)


async def test_get_user_reraises_on_error():
    db = make_db()
    db.get.side_effect = RuntimeError("db failed")

    with pytest.raises(RuntimeError, match="db failed"):
        await get_user(db, 1)


# delete_user

async def test_delete_user_deletes_and_commits_when_user_exists():
    user = make_user()
    db = make_db_with_scalar(user)

    result = await delete_user(db, 1)

    assert result is True
    db.delete.assert_awaited_once_with(user)
    db.commit.assert_awaited_once()
    db.rollback.assert_not_awaited()


async def test_delete_user_returns_false_when_user_does_not_exist():
    db = make_db_with_scalar(None)

    result = await delete_user(db, 999)

    assert result is False
    db.delete.assert_not_awaited()
    db.commit.assert_not_awaited()


async def test_delete_user_rolls_back_and_reraises_on_error():
    db = make_db_with_scalar(make_user())
    db.delete.side_effect = RuntimeError("delete failed")

    with pytest.raises(RuntimeError, match="delete failed"):
        await delete_user(db, 1)

    db.rollback.assert_awaited_once()
