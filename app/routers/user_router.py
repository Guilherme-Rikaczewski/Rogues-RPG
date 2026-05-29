from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File
)
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.user_schema import (
    UserCreate,
    UserUpdate,
    UserResponse
)
import app.services.user_service as us
from app.services.auth_service import get_current_user_id


router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


@router.post("/", response_model=UserResponse)
async def create(
    user: UserCreate,
    db: AsyncSession = Depends(get_db)
):

    try:
        return await us.create_user(db, user)

    except Exception as error:
        raise HTTPException(
            500,
            detail=f'Internal server error {error}'
        )


@router.patch('/', response_model=UserResponse)
async def update(
    user: UserUpdate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):

    try:
        updated_user = await us.update_user(
            db,
            user_id,
            user
        )

        if not updated_user:
            raise HTTPException(
                404,
                detail='User not found'
            )

        return updated_user

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            500,
            detail='Internal server error'
        )


@router.get('/', response_model=UserResponse)
async def read(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):

    try:
        user = await us.get_user(db, user_id)

        if not user:
            raise HTTPException(
                404,
                detail='User not found'
            )

        return user

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            500,
            detail='Internal server error'
        )


@router.delete('/', status_code=204)
async def delete(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):

    try:
        success = await us.delete_user(
            db,
            user_id
        )

        if not success:
            raise HTTPException(
                404,
                detail='User not found'
            )

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            500,
            detail='Internal server error'
        )


@router.patch(
    '/upload/profilepic',
    response_model=UserResponse
)
async def update_room_thumb_image(
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

        updated_user = await us.upload_profile_pic_image(
            db,
            user_id,
            file,
        )

        if not updated_user:
            raise HTTPException(
                404,
                detail="User not found"
            )

        return updated_user

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
