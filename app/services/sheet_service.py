from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm.attributes import flag_modified
from app.models.sheets import Sheet
from app.models.sheet_user import SheetUser
from app.models.users import User
from app.models.room_sheet import RoomSheet
from app.models.room_users import RoomUser
from app.models.rooms import Room
from app.models.tabletop_assets import TabletopAssets
from app.services.tabletop_service import create_asset, upload_asset_image
from app.schemas.sheet_schema import (
    SheetCreate,
    SheetUpdate,
    GameSystem,
    ListModeSheetResponse,
    RecentSheetsResponse,
    SheetRoomResponse
)
from app.schemas.tabletop_schema import AssetCreate
from app.schemas.dnd.dnd_sheet_schema import DnDSheet, DnDSheetUpdate
from app.utils.user_file_manager import delete_image
from fastapi import UploadFile


SCHEMA_VERSION_MASK = {
    GameSystem.DND5e: 1
}

CREATE_SHEET_VALIDATOR_MASK = {
    GameSystem.DND5e: DnDSheet
}

UPDATE_SHEET_VALIDATOR_MASK = {
    GameSystem.DND5e: DnDSheetUpdate
}


def deep_update(original: dict, updates: dict):
    for key, value in updates.items():

        if (
            key in original
            and isinstance(original[key], dict)
            and isinstance(value, dict)
        ):
            deep_update(original[key], value)

        else:
            original[key] = value


async def create_sheet(
    db: AsyncSession,
    sheet_data: SheetCreate
) -> Sheet | None:

    system_sheet_schema = CREATE_SHEET_VALIDATOR_MASK.get(
        sheet_data.game_system
    )

    if not system_sheet_schema:
        raise ValueError(
            f"Unsupported game system: {sheet_data.game_system}"
        )

    schema_version = SCHEMA_VERSION_MASK.get(sheet_data.game_system)

    if not schema_version:
        raise ValueError(
            'Unsupported schema version for game system'
        )

    validated_content = system_sheet_schema(
        schema_version=schema_version
    )

    sheet = Sheet(
        game_system=sheet_data.game_system,
        sheet_type=sheet_data.sheet_type,
        name=sheet_data.name,
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

        system_sheet_schema = UPDATE_SHEET_VALIDATOR_MASK.get(
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
            partial_content = validated.model_dump(
                exclude_unset=True,
                exclude_none=True
            )

            deep_update(sheet.content, partial_content)

            flag_modified(sheet, "content")

            del update_data['content']

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
    room_id: int | None,
    sheet_id: int,
    file: UploadFile,
) -> TabletopAssets | None:

    try:
        asset = await create_asset(
            db,
            AssetCreate(room_id=room_id, user_id=user_id, sheet_id=sheet_id)
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

        asset_result = await db.execute(
            select(TabletopAssets).where(TabletopAssets.sheet_id == sheet_id)
        )

        asset = asset_result.scalar_one_or_none()

        if asset:
            setattr(
                sheet,
                'asset_image_url',
                asset.asset_image_url
            )

        return sheet

    except Exception:
        raise


async def get_all_sheets_from_user(
    db: AsyncSession,
    user_id: int
) -> list[ListModeSheetResponse]:

    try:
        profilepics_subq = (
            select(
                SheetUser.sheet_id.label("sheet_id"),
                func.array_agg(
                    User.profilepic_image_url
                ).label("profilepics")
            )
            .join(
                User,
                User.id == SheetUser.user_id
            )
            .group_by(
                SheetUser.sheet_id
            )
            .subquery()
        )

        room_ranked = (
            select(
                RoomSheet.sheet_id.label("sheet_id"),

                Room.id.label("room_id"),
                Room.room_name.label("room_name"),
                Room.code.label("room_code"),

                func.row_number()
                .over(
                    partition_by=RoomSheet.sheet_id,
                    order_by=RoomUser.last_access.desc()
                )
                .label("rn")
            )
            .select_from(RoomSheet)
            .join(
                Room,
                Room.id == RoomSheet.room_id
            )
            .join(
                RoomUser,
                (RoomUser.room_id == Room.id)
                & (RoomUser.user_id == user_id)
            )
            .subquery()
        )

        latest_room_subq = (
            select(room_ranked)
            .where(room_ranked.c.rn == 1)
            .subquery()
        )

        result = await db.execute(
            select(
                Sheet.id,
                Sheet.game_system,
                Sheet.sheet_type,
                Sheet.name,

                SheetUser.owner,

                TabletopAssets.asset_image_url,

                profilepics_subq.c.profilepics,

                latest_room_subq.c.room_id,
                latest_room_subq.c.room_name,
                latest_room_subq.c.room_code
            )
            .join(
                SheetUser,
                (SheetUser.sheet_id == Sheet.id)
                & (SheetUser.user_id == user_id)
            )
            .outerjoin(
                TabletopAssets,
                TabletopAssets.sheet_id == Sheet.id
            )
            .outerjoin(
                profilepics_subq,
                profilepics_subq.c.sheet_id == Sheet.id
            )
            .outerjoin(
                latest_room_subq,
                latest_room_subq.c.sheet_id == Sheet.id
            )
            .order_by(
                Sheet.name
            )
        )

        rows = result.all()

        return [
            ListModeSheetResponse(
                id=row.id,
                game_system=row.game_system,
                sheet_type=row.sheet_type,
                name=row.name,
                owner=row.owner,
                asset_image_url=row.asset_image_url,

                user_profilepics=row.profilepics or [],

                room=(
                    SheetRoomResponse(
                        id=row.room_id,
                        room_name=row.room_name,
                        code=row.room_code
                    )
                    if row.room_id
                    else None
                )
            )
            for row in rows
        ]

    except Exception:
        raise


async def get_recent_sheets_from_user(
    db: AsyncSession,
    user_id: int
) -> RecentSheetsResponse:
    try:
        ranked = (
            select(
                Sheet.id.label("id"),
                Sheet.game_system.label("game_system"),
                Sheet.sheet_type.label("sheet_type"),
                Sheet.name.label("name"),
                SheetUser.owner.label("owner"),
                TabletopAssets.asset_image_url.label("asset_image_url"),
                func.row_number()
                .over(
                    partition_by=SheetUser.owner,
                    order_by=SheetUser.last_access.desc()
                )
                .label("rn")
            )
            .join(
                SheetUser,
                SheetUser.sheet_id == Sheet.id
            )
            .outerjoin(
                TabletopAssets,
                TabletopAssets.sheet_id == Sheet.id
            )
            .where(
                SheetUser.user_id == user_id
            )
            .subquery()
        )

        result = await db.execute(
            select(ranked)
            .where(ranked.c.rn <= 5)
            .order_by(
                ranked.c.owner.desc(),
                ranked.c.rn
            )
        )

        rows = result.all()

        owned = []
        shared = []

        for row in rows:
            sheet = ListModeSheetResponse(
                id=row.id,
                game_system=row.game_system,
                sheet_type=row.sheet_type,
                name=row.name,
                owner=row.owner,
                asset_image_url=row.asset_image_url
            )

            if row.owner:
                owned.append(sheet)
            else:
                shared.append(sheet)

        return RecentSheetsResponse(
            owned=owned,
            shared=shared
        )

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

        asset_result = await db.execute(
            select(TabletopAssets).where(TabletopAssets.sheet_id == sheet_id)
        )

        asset = asset_result.scalar_one_or_none()
        if asset:
            delete_image(public_id=asset.asset_image_public_id)
            await db.delete(asset)

        await db.delete(sheet)
        await db.commit()

        return True

    except Exception:
        await db.rollback()
        raise
