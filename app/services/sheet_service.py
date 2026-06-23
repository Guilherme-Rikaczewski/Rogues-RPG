from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.sheets import Sheet
from app.models.tabletop_assets import TabletopAssets
from app.services.tabletop_service import create_asset, upload_asset_image
from app.schemas.sheet_schema import SheetCreate, SheetUpdate, GameSystem
from app.schemas.tabletop_schema import AssetCreate
from app.schemas.dnd.dnd_sheet_schema import DnDSheet
from app.utils.user_file_manager import upload_image, delete_image
from fastapi import UploadFile


SHEET_VALIDATOR_MASK = {
    GameSystem.DND5e: DnDSheet
}


async def create_sheet(
    db: AsyncSession,
    sheet_data: SheetCreate
) -> Sheet | None:

    system_sheet_schema = SHEET_VALIDATOR_MASK.get(sheet_data.game_system)

    if not system_sheet_schema:
        raise ValueError(
            f"Unsupported game system: {sheet_data.game_system}"
        )

    validated_content = system_sheet_schema.model_validate(
        sheet_data.content
    )

    sheet = Sheet(
        game_system=sheet_data.game_system,
        sheet_type=sheet_data.sheet_type,
        name=sheet_data.name,
        token_image_url=sheet_data.token_image_url,
        token_image_public_id=sheet_data.token_image_public_id,
        content=validated_content.model_dump()
    )

    try:
        db.add(sheet)

        await db.commit()
        await db.refresh(sheet)

        return sheet
    except Exception:
        await db.rollback()
        raise


async def update_sheet(
    db: AsyncSession,
    sheet_id: int,
    sheet_data: SheetUpdate
) -> Sheet | None:

    try:
        result = await db.execute(
            select(Sheet).where(Sheet.id == sheet_id)
        )

        sheet = result.scalar_one_or_none()

        if not sheet:
            return None

        system_sheet_schema = SHEET_VALIDATOR_MASK.get(
            sheet.game_system  # type: ignore
        )

        if not system_sheet_schema:
            raise ValueError(
                "Unsupported game system"
            )

        if sheet_data.content is not None:
            validated = system_sheet_schema.model_validate(
                sheet_data.content
            )

        update_data = sheet_data.model_dump(
            exclude_unset=True,
            exclude_none=True
        )

        if "content" in update_data:
            update_data['content'] = validated.model_dump()

        for k, v in update_data.items():

            if isinstance(v, str):
                v = v.strip()

            setattr(sheet, k, v)

        await db.commit()
        await db.refresh(sheet)

        return sheet

    except Exception:
        await db.rollback()
        raise


async def upload_sheet_asset_image(
    db: AsyncSession,
    user_id: int,
    room_id: int,
    file: UploadFile,
) -> TabletopAssets | None:

    try:
        asset = await create_asset(
            db,
            AssetCreate(room_id=room_id, user_id=user_id)
        )

        uploaded_asset = await upload_asset_image(
            db,
            user_id,
            asset_id=asset.id,
            file=file
        )

        await db.commit()
        await db.refresh(uploaded_asset)

        return uploaded_asset

    except Exception:
        await db.rollback()
        raise


async def get_sheet(
    db: AsyncSession,
    sheet_id: int
) -> Sheet | None:

    try:
        sheet = await db.get(Sheet, sheet_id)

        if not sheet:
            return None

        return sheet

    except Exception:
        raise


async def delete_sheet(
    db: AsyncSession,
    sheet_id: int
) -> bool:

    try:
        result = await db.execute(
            select(Sheet).where(Sheet.id == sheet_id)
        )

        sheet = result.scalar_one_or_none()

        if not sheet:
            return False

        await db.delete(sheet)
        await db.commit()

        return True

    except Exception:
        await db.rollback()
        raise
