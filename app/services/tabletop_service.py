from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.tabletop_assets import TabletopAssets
from app.models.users import User
from app.schemas.tabletop_schema import (
    AssetCreate,
    AssetUpdate,
)
from app.utils.user_file_manager import (
    upload_image,
    delete_image
)
from fastapi import UploadFile
import random


def roll_dices(quantity: int, sides: int):
    dices = []

    for _ in range(quantity):
        dices.append(random.randint(1, sides))

    return dices


async def create_asset(
    db: AsyncSession,
    asset_data: AssetCreate
) -> TabletopAssets:

    asset = TabletopAssets(
        **asset_data.model_dump()
    )

    db.add(asset)

    await db.commit()
    await db.refresh(asset)

    return asset


async def update_asset(
    db: AsyncSession,
    asset_id: int,
    asset_data: AssetUpdate
) -> TabletopAssets | None:

    try:

        result = await db.execute(
            select(TabletopAssets).where(
                TabletopAssets.id == asset_id
            )
        )

        asset = result.scalar_one_or_none()

        if not asset:
            return None

        update_data = asset_data.model_dump(
            exclude_unset=True,
            exclude_none=True
        )

        for k, v in update_data.items():

            if isinstance(v, str):
                v = v.strip()

            setattr(asset, k, v)

        await db.commit()
        await db.refresh(asset)

        return asset

    except Exception as error:

        await db.rollback()

        print('DEU ERRO:', error)

        raise


async def upload_asset_image(
    db: AsyncSession,
    user_id: int,
    asset_id: int,
    file: UploadFile,
) -> TabletopAssets | None:

    try:

        asset_result = await db.execute(
            select(TabletopAssets).where(
                TabletopAssets.id == asset_id
            )
        )

        asset = asset_result.scalar_one_or_none()

        if not asset:
            return None

        user_result = await db.execute(
            select(User).where(
                User.id == user_id
            )
        )

        user = user_result.scalar_one_or_none()

        if not user:
            return None

        image = upload_image(
            file.file,
            user_id,
            img_id=f'tabletop_asset_{asset_id}',
            extra_folder='/assets_lib'
        )

        MAX_ALLOWED_FOR_USER = 50 * 1024 * 1024

        storage_without_asset_pic = int(
            user.storage_usage
        )

        future_storage_with_asset_pic = (
            storage_without_asset_pic
            + image['size']
        )

        if future_storage_with_asset_pic > MAX_ALLOWED_FOR_USER:

            delete_image(image['public_id'])

            raise ValueError(
                'The image exceeds its storage limit.'
            )

        asset.asset_image_url = image['url']
        asset.asset_image_file_name = file.filename
        asset.asset_image_public_id = image['public_id']

        user.storage_usage = (
            future_storage_with_asset_pic
        )

        await db.commit()
        await db.refresh(asset)

        return asset

    except Exception:

        await db.rollback()
        raise


async def get_asset(
    db: AsyncSession,
    asset_id: int
) -> TabletopAssets | None:

    try:

        asset = await db.get(
            TabletopAssets,
            asset_id
        )

        if not asset:
            return None

        return asset

    except Exception:
        raise


async def delete_asset(
    db: AsyncSession,
    asset_id: int
) -> bool:

    try:

        result = await db.execute(
            select(TabletopAssets).where(
                TabletopAssets.id == asset_id
            )
        )

        asset = result.scalar_one_or_none()

        if not asset:
            return False

        delete_image(public_id=asset.asset_image_public_id)

        await db.delete(asset)

        await db.commit()

        return True

    except Exception:

        await db.rollback()
        raise
