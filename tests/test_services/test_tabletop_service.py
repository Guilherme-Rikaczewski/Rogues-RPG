from unittest.mock import patch

import pytest

from app.models.tabletop_assets import TabletopAssets
from app.schemas.tabletop_schema import (
    AssetCreate,
    AssetUpdate,
    TabletopLayer,
)
from app.services.tabletop_service import (
    create_asset,
    delete_asset,
    get_all_assets_from_user_in_room,
    get_asset,
    get_random_default_image,
    roll_dices,
    update_asset,
    upload_asset_image,
)
from tests.helpers import (
    make_asset,
    make_db,
    make_db_with_scalar,
    make_db_with_scalars,
    make_scalars_result,
    make_upload_file,
    make_user,
)


MAX_STORAGE = 50 * 1024 * 1024

DEFAULT_IMAGES = [
    "asset_1_tmvhc1",
    "asset_2_naesz7",
    "asset_3_tk6gtv",
    "asset_4_rzrqaq",
    "asset_5_fico0g",
]


# roll_dices

@patch("app.services.tabletop_service.random.randint")
def test_roll_dices_returns_one_random_result_per_quantity(mock_randint):
    mock_randint.side_effect = [2, 5, 6]

    result = roll_dices(quantity=3, sides=6)

    assert result == [2, 5, 6]
    assert mock_randint.call_args_list == [((1, 6),)] * 3


def test_roll_dices_returns_empty_list_when_quantity_is_zero():
    assert roll_dices(quantity=0, sides=6) == []


def test_roll_dices_results_stay_within_dice_sides():
    result = roll_dices(quantity=100, sides=20)

    assert len(result) == 100
    assert all(1 <= value <= 20 for value in result)


# get_random_default_image

@pytest.mark.parametrize("index, image", enumerate(DEFAULT_IMAGES))
@patch("app.services.tabletop_service.random.randint")
def test_get_random_default_image_returns_cloudinary_url(
    mock_randint,
    index,
    image
):
    mock_randint.return_value = index

    url = get_random_default_image()

    assert url == (
        "https://res.cloudinary.com/dmtuq3wg9/image/upload/"
        f"v1783212403/{image}.png"
    )
    mock_randint.assert_called_once_with(0, 4)


# create_asset

async def test_create_asset_adds_asset_and_commits():
    db = make_db()
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


# update_asset

async def test_update_asset_updates_stripped_positions_and_commits():
    asset = make_asset()
    db = make_db_with_scalar(asset)

    result = await update_asset(
        db,
        asset_id=1,
        asset_data=AssetUpdate(position_x="  10px  ", position_y="  20px  ")
    )

    assert result is asset
    assert asset.position_x == "10px"
    assert asset.position_y == "20px"
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(asset)
    db.rollback.assert_not_awaited()


async def test_update_asset_changes_layer_without_touching_positions():
    asset = make_asset(position_x="1px", position_y="2px")
    db = make_db_with_scalar(asset)

    result = await update_asset(
        db,
        asset_id=1,
        asset_data=AssetUpdate(layer=TabletopLayer.master)
    )

    assert result is asset
    assert asset.layer == TabletopLayer.master
    assert asset.position_x == "1px"
    assert asset.position_y == "2px"


async def test_update_asset_returns_none_when_asset_does_not_exist():
    db = make_db_with_scalar(None)

    result = await update_asset(
        db,
        asset_id=999,
        asset_data=AssetUpdate(position_x="10px")
    )

    assert result is None
    db.commit.assert_not_awaited()
    db.rollback.assert_not_awaited()


async def test_update_asset_rolls_back_and_reraises_on_error():
    db = make_db_with_scalar(make_asset())
    db.commit.side_effect = RuntimeError("commit failed")

    with pytest.raises(RuntimeError, match="commit failed"):
        await update_asset(
            db,
            asset_id=1,
            asset_data=AssetUpdate(position_x="10px")
        )

    db.rollback.assert_awaited_once()


# upload_asset_image

@patch("app.services.tabletop_service.upload_image")
async def test_upload_asset_image_updates_asset_and_user_storage(
    mock_upload_image
):
    asset = make_asset()
    user = make_user(storage_usage=100)
    db = make_db_with_scalars(asset, user)
    file = make_upload_file("token.png")
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
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(asset)
    db.rollback.assert_not_awaited()


@patch("app.services.tabletop_service.upload_image")
async def test_upload_asset_image_returns_none_when_asset_is_missing(
    mock_upload_image
):
    db = make_db_with_scalar(None)

    result = await upload_asset_image(db, 5, 999, make_upload_file())

    assert result is None
    mock_upload_image.assert_not_called()
    db.commit.assert_not_awaited()
    db.rollback.assert_not_awaited()


@patch("app.services.tabletop_service.upload_image")
async def test_upload_asset_image_returns_none_when_user_is_missing(
    mock_upload_image
):
    db = make_db_with_scalars(make_asset(), None)

    result = await upload_asset_image(db, 999, 1, make_upload_file())

    assert result is None
    mock_upload_image.assert_not_called()
    db.commit.assert_not_awaited()
    db.rollback.assert_not_awaited()


@patch("app.services.tabletop_service.delete_image")
@patch("app.services.tabletop_service.upload_image")
async def test_upload_asset_image_deletes_uploaded_image_when_storage_exceeds_limit(
    mock_upload_image,
    mock_delete_image
):
    user = make_user(storage_usage=MAX_STORAGE)
    db = make_db_with_scalars(make_asset(), user)
    mock_upload_image.return_value = {
        "url": "https://cdn.test/token.png",
        "size": 1,
        "public_id": "new-asset-public-id",
    }

    with pytest.raises(ValueError, match="storage limit"):
        await upload_asset_image(db, 5, 1, make_upload_file())

    mock_delete_image.assert_called_once_with("new-asset-public-id")
    assert user.storage_usage == MAX_STORAGE
    db.commit.assert_not_awaited()
    db.rollback.assert_awaited_once()


@patch("app.services.tabletop_service.upload_image")
async def test_upload_asset_image_rolls_back_and_reraises_on_error(
    mock_upload_image
):
    db = make_db_with_scalars(make_asset(), make_user())
    db.commit.side_effect = RuntimeError("commit failed")
    mock_upload_image.return_value = {
        "url": "https://cdn.test/token.png",
        "size": 250,
        "public_id": "asset-public-id",
    }

    with pytest.raises(RuntimeError, match="commit failed"):
        await upload_asset_image(db, 5, 1, make_upload_file())

    db.rollback.assert_awaited_once()


# get_asset

async def test_get_asset_returns_asset_when_found():
    asset = make_asset()
    db = make_db()
    db.get.return_value = asset

    result = await get_asset(db, 1)

    assert result is asset
    db.get.assert_awaited_once_with(TabletopAssets, 1)


async def test_get_asset_returns_none_when_missing():
    db = make_db()
    db.get.return_value = None

    result = await get_asset(db, 999)

    assert result is None
    db.get.assert_awaited_once_with(TabletopAssets, 999)


async def test_get_asset_reraises_on_error():
    db = make_db()
    db.get.side_effect = RuntimeError("db failed")

    with pytest.raises(RuntimeError, match="db failed"):
        await get_asset(db, 1)


# get_all_assets_from_user_in_room

async def test_get_all_assets_from_user_in_room_returns_assets():
    assets = [make_asset(id=1), make_asset(id=2)]
    db = make_db()
    db.execute.return_value = make_scalars_result(assets)

    result = await get_all_assets_from_user_in_room(db, 5, 10)

    assert result == assets
    db.execute.assert_awaited_once()


async def test_get_all_assets_from_user_in_room_returns_empty_list():
    db = make_db()
    db.execute.return_value = make_scalars_result([])

    assert await get_all_assets_from_user_in_room(db, 5, 10) == []


# delete_asset

@patch("app.services.tabletop_service.delete_image")
async def test_delete_asset_deletes_image_and_commits_when_asset_exists(
    mock_delete_image
):
    asset = make_asset(asset_image_public_id="asset-public-id")
    db = make_db_with_scalar(asset)

    result = await delete_asset(db, 1)

    assert result is True
    mock_delete_image.assert_called_once_with(public_id="asset-public-id")
    db.delete.assert_awaited_once_with(asset)
    db.commit.assert_awaited_once()
    db.rollback.assert_not_awaited()


@pytest.mark.xfail(
    strict=True,
    reason=(
        "delete_asset chama o Cloudinary mesmo quando o asset não tem "
        "imagem (public_id vazio); delete_room já faz essa checagem"
    ),
)
@patch("app.services.tabletop_service.delete_image")
async def test_delete_asset_without_image_does_not_call_cloudinary(
    mock_delete_image
):
    db = make_db_with_scalar(make_asset(asset_image_public_id=""))

    await delete_asset(db, 1)

    mock_delete_image.assert_not_called()


@patch("app.services.tabletop_service.delete_image")
async def test_delete_asset_returns_false_when_asset_does_not_exist(
    mock_delete_image
):
    db = make_db_with_scalar(None)

    result = await delete_asset(db, 999)

    assert result is False
    mock_delete_image.assert_not_called()
    db.delete.assert_not_awaited()
    db.commit.assert_not_awaited()


@patch("app.services.tabletop_service.delete_image")
async def test_delete_asset_rolls_back_and_reraises_on_error(
    mock_delete_image
):
    db = make_db_with_scalar(make_asset())
    db.delete.side_effect = RuntimeError("delete failed")

    with pytest.raises(RuntimeError, match="delete failed"):
        await delete_asset(db, 1)

    db.rollback.assert_awaited_once()


@patch("app.services.tabletop_service.delete_image")
async def test_delete_asset_rolls_back_when_image_deletion_fails(
    mock_delete_image
):
    db = make_db_with_scalar(make_asset())
    mock_delete_image.side_effect = RuntimeError("cloudinary failed")

    with pytest.raises(RuntimeError, match="cloudinary failed"):
        await delete_asset(db, 1)

    db.delete.assert_not_awaited()
    db.commit.assert_not_awaited()
    db.rollback.assert_awaited_once()
