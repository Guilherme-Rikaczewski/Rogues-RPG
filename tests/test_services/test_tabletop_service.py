from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.tabletop_schema import (
    AssetCreate,
    AssetUpdate,
    TabletopLayer,
)
from app.services.tabletop_service import (
    create_asset,
    delete_asset_in_db,
    get_asset,
    roll_dices,
    update_asset,
    upload_asset_image,
)


def make_asset(**overrides):
    data = {
        "id": 1,
        "asset_image_url": "",
        "asset_image_public_id": "",
        "asset_image_file_name": "",
        "layer": TabletopLayer.players,
        "position_x": None,
        "position_y": None,
        "room_id": 10,
        "user_id": 5,
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def make_user(**overrides):
    data = {
        "id": 5,
        "storage_usage": 0,
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def make_scalar_result(value):
    result = MagicMock()
    result.scalar_one_or_none.return_value = value
    return result


def make_db_with_scalar(value):
    db = MagicMock()
    db.execute = AsyncMock(return_value=make_scalar_result(value))
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.rollback = AsyncMock()
    db.delete = AsyncMock()
    return db


@patch("app.services.tabletop_service.random.randint")
def test_roll_dices_returns_one_random_result_per_quantity(mock_randint):
    mock_randint.side_effect = [2, 5, 6]

    result = roll_dices(quantity=3, sides=6)

    assert result == [2, 5, 6]
    assert mock_randint.call_args_list == [
        ((1, 6),),
        ((1, 6),),
        ((1, 6),),
    ]


def test_roll_dices_returns_empty_list_when_quantity_is_zero():
    result = roll_dices(quantity=0, sides=6)

    assert result == []


@pytest.mark.asyncio
async def test_create_asset_adds_asset_and_commits():
    db = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    asset_data = AssetCreate(
        layer=TabletopLayer.players,
        room_id=10,
        user_id=5,
        asset_image_url="https://cdn.test/asset.png",
        asset_image_public_id="asset-public-id",
        asset_image_file_name="asset.png",
    )

    result = await create_asset(db, asset_data)

    assert result.layer == TabletopLayer.players
    assert result.room_id == 10
    assert result.user_id == 5
    assert result.asset_image_url == "https://cdn.test/asset.png"

    db.add.assert_called_once_with(result)
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(result)


@pytest.mark.asyncio
async def test_update_asset_updates_stripped_positions_and_commits():
    asset = make_asset()
    db = make_db_with_scalar(asset)

    result = await update_asset(
        db,
        asset_id=1,
        asset_data=AssetUpdate(
            position_x="  10px  ",
            position_y="  20px  "
        )
    )

    assert result is asset
    assert asset.position_x == "10px"
    assert asset.position_y == "20px"

    db.execute.assert_awaited_once()
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(asset)
    db.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_asset_returns_none_when_asset_does_not_exist():
    db = make_db_with_scalar(None)

    result = await update_asset(
        db,
        asset_id=999,
        asset_data=AssetUpdate(position_x="10px")
    )

    assert result is None
    db.execute.assert_awaited_once()
    db.commit.assert_not_awaited()
    db.refresh.assert_not_awaited()
    db.rollback.assert_not_awaited()


@pytest.mark.asyncio
@patch("builtins.print")
async def test_update_asset_rolls_back_and_reraises_on_error(mock_print):
    db = make_db_with_scalar(make_asset())
    db.commit.side_effect = RuntimeError("commit failed")

    with pytest.raises(RuntimeError, match="commit failed"):
        await update_asset(
            db,
            asset_id=1,
            asset_data=AssetUpdate(position_x="10px")
        )

    db.rollback.assert_awaited_once()
    mock_print.assert_called_once()


@pytest.mark.asyncio
@patch("app.services.tabletop_service.upload_image")
async def test_upload_asset_image_updates_asset_and_user_storage(
    mock_upload_image
):
    asset = make_asset()
    user = make_user(storage_usage=100)
    db = MagicMock()
    db.execute = AsyncMock(
        side_effect=[
            make_scalar_result(asset),
            make_scalar_result(user),
        ]
    )
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.rollback = AsyncMock()
    file = SimpleNamespace(file=MagicMock(), filename="token.png")
    mock_upload_image.return_value = {
        "url": "https://cdn.test/token.png",
        "size": 250,
        "public_id": "asset-public-id",
    }

    result = await upload_asset_image(db, 5, 1, file)

    assert result is asset
    assert asset.asset_image_url == "https://cdn.test/token.png"
    assert asset.asset_image_file_name == "token.png"
    assert asset.asset_image_public_id == "asset-public-id"
    assert user.storage_usage == 350

    mock_upload_image.assert_called_once_with(
        file.file,
        5,
        img_id="tabletop_asset_1",
        extra_folder="/assets_lib"
    )
    assert db.execute.await_count == 2
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(asset)
    db.rollback.assert_not_awaited()


@pytest.mark.asyncio
@patch("app.services.tabletop_service.upload_image")
async def test_upload_asset_image_returns_none_when_asset_is_missing(
    mock_upload_image
):
    db = make_db_with_scalar(None)
    file = SimpleNamespace(file=MagicMock(), filename="token.png")

    result = await upload_asset_image(db, 5, 999, file)

    assert result is None
    mock_upload_image.assert_not_called()
    db.commit.assert_not_awaited()
    db.refresh.assert_not_awaited()
    db.rollback.assert_not_awaited()


@pytest.mark.asyncio
@patch("app.services.tabletop_service.upload_image")
async def test_upload_asset_image_returns_none_when_user_is_missing(
    mock_upload_image
):
    db = MagicMock()
    db.execute = AsyncMock(
        side_effect=[
            make_scalar_result(make_asset()),
            make_scalar_result(None),
        ]
    )
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.rollback = AsyncMock()
    file = SimpleNamespace(file=MagicMock(), filename="token.png")

    result = await upload_asset_image(db, 999, 1, file)

    assert result is None
    mock_upload_image.assert_not_called()
    db.commit.assert_not_awaited()
    db.refresh.assert_not_awaited()
    db.rollback.assert_not_awaited()


@pytest.mark.asyncio
@patch("app.services.tabletop_service.delete_image")
@patch("app.services.tabletop_service.upload_image")
async def test_upload_asset_image_deletes_uploaded_image_when_storage_exceeds_limit(
    mock_upload_image,
    mock_delete_image
):
    user = make_user(storage_usage=50 * 1024 * 1024)
    db = MagicMock()
    db.execute = AsyncMock(
        side_effect=[
            make_scalar_result(make_asset()),
            make_scalar_result(user),
        ]
    )
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.rollback = AsyncMock()
    file = SimpleNamespace(file=MagicMock(), filename="token.png")
    mock_upload_image.return_value = {
        "url": "https://cdn.test/token.png",
        "size": 1,
        "public_id": "new-asset-public-id",
    }

    with pytest.raises(ValueError, match="storage limit"):
        await upload_asset_image(db, 5, 1, file)

    mock_delete_image.assert_called_once_with("new-asset-public-id")
    db.commit.assert_not_awaited()
    db.refresh.assert_not_awaited()
    db.rollback.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.services.tabletop_service.upload_image")
async def test_upload_asset_image_rolls_back_and_reraises_on_error(
    mock_upload_image
):
    db = MagicMock()
    db.execute = AsyncMock(
        side_effect=[
            make_scalar_result(make_asset()),
            make_scalar_result(make_user()),
        ]
    )
    db.commit = AsyncMock(side_effect=RuntimeError("commit failed"))
    db.refresh = AsyncMock()
    db.rollback = AsyncMock()
    file = SimpleNamespace(file=MagicMock(), filename="token.png")
    mock_upload_image.return_value = {
        "url": "https://cdn.test/token.png",
        "size": 250,
        "public_id": "asset-public-id",
    }

    with pytest.raises(RuntimeError, match="commit failed"):
        await upload_asset_image(db, 5, 1, file)

    db.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_asset_returns_asset_when_found():
    asset = make_asset()
    db = MagicMock()
    db.get = AsyncMock(return_value=asset)

    result = await get_asset(db, 1)

    assert result is asset
    db.get.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_asset_returns_none_when_missing():
    db = MagicMock()
    db.get = AsyncMock(return_value=None)

    result = await get_asset(db, 999)

    assert result is None
    db.get.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_asset_reraises_on_error():
    db = MagicMock()
    db.get = AsyncMock(side_effect=RuntimeError("db failed"))

    with pytest.raises(RuntimeError, match="db failed"):
        await get_asset(db, 1)


@pytest.mark.asyncio
async def test_delete_asset_deletes_and_commits_when_asset_exists():
    asset = make_asset()
    db = make_db_with_scalar(asset)

    result = await delete_asset_in_db(db, 1)

    assert result is True
    db.delete.assert_awaited_once_with(asset)
    db.commit.assert_awaited_once()
    db.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_asset_returns_false_when_asset_does_not_exist():
    db = make_db_with_scalar(None)

    result = await delete_asset_in_db(db, 999)

    assert result is False
    db.delete.assert_not_awaited()
    db.commit.assert_not_awaited()
    db.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_asset_rolls_back_and_reraises_on_error():
    db = make_db_with_scalar(make_asset())
    db.delete.side_effect = RuntimeError("delete failed")

    with pytest.raises(RuntimeError, match="delete failed"):
        await delete_asset_in_db(db, 1)

    db.rollback.assert_awaited_once()
