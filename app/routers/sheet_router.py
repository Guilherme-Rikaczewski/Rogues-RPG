from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File
)
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.sheet_schema import (
    SheetCreate,
    SheetUpdate,
    SheetResponse,
    RecentSheetsResponse
)
from app.schemas.tabletop_schema import TabletopAssetResponse
import app.services.sheet_service as ss
import app.services.sheet_user_service as sus
from app.services.auth_service import get_current_user_id


router = APIRouter(
    prefix="/sheets",
    tags=["Sheets"]
)


@router.post("/", response_model=SheetResponse)
async def create(
    sheet: SheetCreate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):

    try:
        new_sheet = await ss.create_sheet(db, sheet)

        if not new_sheet:
            raise HTTPException(
                400,
                detail="Can't create sheet"
            )

        sheet_user = await sus.create_sheet_user(
            db,
            new_sheet.id,
            user_id,
            owner=True
        )

        if not sheet_user:
            raise HTTPException(
                400,
                detail="Can't create sheet"
            )

        return new_sheet

    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            500,
            detail=f'Internal server error {error}'
        )


@router.patch('/{sheet_id}', response_model=SheetResponse)
async def update(
    sheet_id: int,
    sheet_data: SheetUpdate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):

    try:
        user_can_edit = await sus.check_user_acces_for_sheet(
            db, user_id=user_id, sheet_id=sheet_id
        )

        if not user_can_edit:
            raise HTTPException(
                403,
                detail='Permission denied'
            )

        updated_sheet = await ss.update_sheet(
            db,
            sheet_id,
            sheet_data,
        )

        if not updated_sheet:
            raise HTTPException(
                404,
                detail='Sheet not found'
            )

        return updated_sheet

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            500,
            detail='Internal server error'
        )


@router.get('/{sheet_id}', response_model=SheetResponse)
async def read(
    sheet_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):

    try:
        user_can_read = await sus.check_user_acces_for_sheet(
            db, user_id=user_id, sheet_id=sheet_id
        )

        if not user_can_read:
            raise HTTPException(
                403,
                detail='Permission denied'
            )

        sheet = await ss.get_sheet(db, sheet_id)

        if not sheet:
            raise HTTPException(
                404,
                detail='Sheet not found'
            )

        await sus.update_sheet_last_access(
            db, user_id, sheet_id
        )

        return sheet

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            500,
            detail=f'Internal server error: {error}'
        )


@router.get('/all/')
async def read_all_sheets_from_user(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):

    try:
        sheets = await ss.get_all_sheets_from_user(
            db,
            user_id
        )

        if not sheets:
            raise HTTPException(
                404,
                detail='Sheets not found'
            )

        return sheets

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            500,
            detail='Internal server error'
        )


@router.get('/recent/', response_model=RecentSheetsResponse)
async def read_recent_sheets_from_user(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):

    try:
        sheets = await ss.get_recent_sheets_from_user(
            db,
            user_id
        )

        if not sheets:
            raise HTTPException(
                404,
                detail='Sheets not found'
            )

        return sheets

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            500,
            detail='Internal server error'
        )


@router.delete('/{sheet_id}', status_code=204)
async def delete(
    sheet_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):

    try:
        user_can_delete = await sus.check_user_acces_for_sheet(
            db, user_id=user_id, sheet_id=sheet_id
        )

        if not user_can_delete:
            raise HTTPException(
                403,
                detail='Permission denied'
            )

        success = await ss.delete_sheet(
            db,
            sheet_id
        )

        if not success:
            raise HTTPException(
                404,
                detail='Sheet not found'
            )

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            500,
            detail='Internal server error'
        )


@router.patch(
    '/upload/sheet_asset/{sheet_id}/on_room/{room_id}',
    response_model=TabletopAssetResponse
)
async def update_sheet_asset_image(
    sheet_id: int,
    room_id: int | None,
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):

    try:
        MAX_SIZE = 10 * 1024 * 1024

        file.file.seek(0, 2)
        size = file.file.tell()
        file.file.seek(0)

        if size > MAX_SIZE:
            raise HTTPException(
                400,
                "File exceeds maximum size: 10MB"
            )

        if file.content_type not in [
            "image/png",
            "image/jpeg",
            "image/webp"
        ]:
            raise HTTPException(
                400,
                detail="Invalid file type"
            )

        updated_sheet_asset = await ss.upload_sheet_asset_image(
            db,
            user_id,
            room_id=room_id,
            sheet_id=sheet_id,
            file=file
        )

        if not updated_sheet_asset:
            raise HTTPException(
                404,
                detail="User not found"
            )

        return updated_sheet_asset

    except ValueError as error:

        raise HTTPException(
            400,
            detail=str(error)
        )

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            500,
            detail=f'Internal server error {error}'
        )


@router.post("/share/{sheet_id}/to_user/{receiver_id}",)
async def share_sheet(
    sheet_id: int,
    receiver_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):

    try:
        user_can_share = await sus.check_user_acces_for_sheet(
            db, user_id=user_id, sheet_id=sheet_id
        )

        if not user_can_share:
            raise HTTPException(
                403,
                detail='Permission denied'
            )

        sheet_is_already_shared = await sus.check_user_acces_for_sheet(
            db, user_id=receiver_id, sheet_id=sheet_id
        )

        if sheet_is_already_shared:
            raise HTTPException(
                409,
                detail='The sharing already exists'
            )

        sheet_user = await sus.create_sheet_user(
            db,
            sheet_id,
            receiver_id,
            owner=False
        )

        if not sheet_user:
            raise HTTPException(
                400,
                detail="Can't create sheet"
            )

    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            500,
            detail=f'Internal server error {error}'
        )
