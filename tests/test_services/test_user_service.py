import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.user_service import (
    create_user,
    delete_user,
    get_user,
    update_user,
    upload_profile_pic_image,
)
from app.schemas.user_schema import UserCreate, UserUpdate


def make_db_with_scalar(user):
    result = MagicMock()
    result.scalar_one_or_none.return_value = user

    db = MagicMock()
    db.execute = AsyncMock(return_value=result)
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.rollback = AsyncMock()
    db.delete = AsyncMock()

    return db


def make_user(**overrides):
    data = {
        "id": 1,
        "username": "gui",
        "email": "gui@email.com",
        "password": "old_hash",
        "storage_usage": 0,
        "seconds_played": 0,
        "profilepic_image_url": "",
        "profilepic_image_size": 0,
        "profilepic_image_public_id": "",
    }
    data.update(overrides)
    return SimpleNamespace(**data)


@pytest.mark.asyncio
@patch("app.services.user_service.get_password_hash")
async def test_create_user(mock_hash):
    mock_hash.return_value = "hashed_password"

    fake_db = MagicMock()
    fake_db.commit = AsyncMock()
    fake_db.refresh = AsyncMock()

    user_data = UserCreate(
        username="guilherme",
        email="gui@email.com",
        password="aB123456"
    )

    result = await create_user(fake_db, user_data)

    assert result.username == "guilherme"
    assert result.email == "gui@email.com"
    assert result.password == "hashed_password"

    fake_db.add.assert_called_once()
    fake_db.commit.assert_awaited_once()
    fake_db.refresh.assert_awaited_once_with(result)


@pytest.mark.asyncio
@patch("app.services.user_service.get_password_hash")
async def test_update_user(mock_hash):
    mock_hash.return_value = "nova_senha_hash"

    fake_user = MagicMock()
    fake_user.id = 1
    fake_user.username = "gui"

    fake_result = MagicMock()
    fake_result.scalar_one_or_none.return_value = fake_user

    fake_db = MagicMock()
    fake_db.execute = AsyncMock(return_value=fake_result)
    fake_db.commit = AsyncMock()
    fake_db.refresh = AsyncMock()
    fake_db.rollback = AsyncMock()

    user_data = UserUpdate(
        username="guilherme",
        password="bA123456"
    )

    result = await update_user(fake_db, 1, user_data)

    assert result.username == "guilherme"
    assert result.password == "nova_senha_hash"

    fake_db.execute.assert_awaited_once()
    fake_db.commit.assert_awaited_once()
    fake_db.refresh.assert_awaited_once_with(fake_user)

    mock_hash.assert_called_once_with("bA123456")


@pytest.mark.asyncio
async def test_update_user_returns_none_when_user_does_not_exist():
    fake_db = make_db_with_scalar(None)

    result = await update_user(
        fake_db,
        999,
        UserUpdate(username="guilherme")
    )

    assert result is None

    fake_db.execute.assert_awaited_once()
    fake_db.commit.assert_not_awaited()
    fake_db.refresh.assert_not_awaited()
    fake_db.rollback.assert_not_awaited()


@pytest.mark.asyncio
@patch("app.services.user_service.get_password_hash")
async def test_update_user_strips_strings_and_does_not_hash_absent_password(
    mock_hash
):
    fake_user = make_user(username="gui")
    fake_db = make_db_with_scalar(fake_user)

    result = await update_user(
        fake_db,
        1,
        UserUpdate(username="  guilherme  ")
    )

    assert result is fake_user
    assert fake_user.username == "guilherme"

    mock_hash.assert_not_called()
    fake_db.commit.assert_awaited_once()
    fake_db.refresh.assert_awaited_once_with(fake_user)


@pytest.mark.asyncio
async def test_update_user_rolls_back_and_reraises_on_error():
    fake_db = make_db_with_scalar(make_user())
    fake_db.commit.side_effect = RuntimeError("commit failed")

    with pytest.raises(RuntimeError, match="commit failed"):
        await update_user(
            fake_db,
            1,
            UserUpdate(username="guilherme")
        )

    fake_db.rollback.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.services.user_service.upload_image")
async def test_upload_profile_pic_image_updates_user_storage(mock_upload):
    fake_user = make_user(
        storage_usage=1000,
        profilepic_image_size=200
    )
    fake_db = make_db_with_scalar(fake_user)
    fake_file = SimpleNamespace(file=MagicMock())

    mock_upload.return_value = {
        "url": "https://cdn.test/profile.png",
        "size": 500,
        "public_id": "profilepic_user_1",
    }

    result = await upload_profile_pic_image(fake_db, 1, fake_file)

    assert result is fake_user
    assert fake_user.profilepic_image_url == "https://cdn.test/profile.png"
    assert fake_user.profilepic_image_size == 500
    assert fake_user.profilepic_image_public_id == "profilepic_user_1"
    assert fake_user.storage_usage == 1300

    mock_upload.assert_called_once_with(
        fake_file.file,
        1,
        img_id="profilepic_user_1",
        max_width=512,
        max_height=512
    )
    fake_db.commit.assert_awaited_once()
    fake_db.refresh.assert_awaited_once_with(fake_user)
    fake_db.rollback.assert_not_awaited()


@pytest.mark.asyncio
@patch("app.services.user_service.upload_image")
async def test_upload_profile_pic_image_returns_none_when_user_is_missing(
    mock_upload
):
    fake_db = make_db_with_scalar(None)
    fake_file = SimpleNamespace(file=MagicMock())

    result = await upload_profile_pic_image(fake_db, 999, fake_file)

    assert result is None

    mock_upload.assert_not_called()
    fake_db.commit.assert_not_awaited()
    fake_db.refresh.assert_not_awaited()
    fake_db.rollback.assert_not_awaited()


@pytest.mark.asyncio
@patch("app.services.user_service.delete_image")
@patch("app.services.user_service.upload_image")
async def test_upload_profile_pic_image_deletes_image_when_storage_exceeds_limit(
    mock_upload,
    mock_delete
):
    fake_user = make_user(
        storage_usage=50 * 1024 * 1024,
        profilepic_image_size=0
    )
    fake_db = make_db_with_scalar(fake_user)
    fake_file = SimpleNamespace(file=MagicMock())

    mock_upload.return_value = {
        "url": "https://cdn.test/profile.png",
        "size": 1,
        "public_id": "new_public_id",
    }

    with pytest.raises(ValueError, match="storage limit"):
        await upload_profile_pic_image(fake_db, 1, fake_file)

    mock_delete.assert_called_once_with("new_public_id")
    fake_db.commit.assert_not_awaited()
    fake_db.refresh.assert_not_awaited()
    fake_db.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_upload_profile_pic_image_rolls_back_and_reraises_on_error():
    fake_db = make_db_with_scalar(make_user())
    fake_db.commit.side_effect = RuntimeError("commit failed")
    fake_file = SimpleNamespace(file=MagicMock())

    with patch(
        "app.services.user_service.upload_image",
        return_value={
            "url": "https://cdn.test/profile.png",
            "size": 500,
            "public_id": "profilepic_user_1",
        }
    ):
        with pytest.raises(RuntimeError, match="commit failed"):
            await upload_profile_pic_image(fake_db, 1, fake_file)

    fake_db.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_user_returns_user_when_found():
    fake_user = make_user()
    fake_db = MagicMock()
    fake_db.get = AsyncMock(return_value=fake_user)

    result = await get_user(fake_db, 1)

    assert result is fake_user
    fake_db.get.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_user_returns_none_when_missing():
    fake_db = MagicMock()
    fake_db.get = AsyncMock(return_value=None)

    result = await get_user(fake_db, 999)

    assert result is None
    fake_db.get.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_user_reraises_on_error():
    fake_db = MagicMock()
    fake_db.get = AsyncMock(side_effect=RuntimeError("db failed"))

    with pytest.raises(RuntimeError, match="db failed"):
        await get_user(fake_db, 1)


@pytest.mark.asyncio
async def test_delete_user_deletes_and_commits_when_user_exists():
    fake_user = make_user()
    fake_db = make_db_with_scalar(fake_user)

    result = await delete_user(fake_db, 1)

    assert result is True
    fake_db.delete.assert_awaited_once_with(fake_user)
    fake_db.commit.assert_awaited_once()
    fake_db.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_user_returns_false_when_user_does_not_exist():
    fake_db = make_db_with_scalar(None)

    result = await delete_user(fake_db, 999)

    assert result is False
    fake_db.delete.assert_not_awaited()
    fake_db.commit.assert_not_awaited()
    fake_db.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_user_rolls_back_and_reraises_on_error():
    fake_db = make_db_with_scalar(make_user())
    fake_db.delete.side_effect = RuntimeError("delete failed")

    with pytest.raises(RuntimeError, match="delete failed"):
        await delete_user(fake_db, 1)

    fake_db.rollback.assert_awaited_once()
